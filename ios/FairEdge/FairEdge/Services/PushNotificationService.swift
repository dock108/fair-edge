//
//  PushNotificationService.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import Foundation
import UserNotifications
import Combine

/// Push notification service for managing local and remote notifications
class PushNotificationService: NSObject, ObservableObject {
    
    // MARK: - Published Properties
    
    @Published var authorizationStatus: UNAuthorizationStatus = .notDetermined
    @Published var isRegistered = false
    @Published var deviceToken: String?
    @Published var errorMessage: String?
    
    // MARK: - Private Properties
    
    private let apiService: APIService
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: - Notification Categories
    
    enum NotificationCategory: String, CaseIterable {
        case opportunityAlert = "OPPORTUNITY_ALERT"
        case subscriptionUpdate = "SUBSCRIPTION_UPDATE"
        case systemNotification = "SYSTEM_NOTIFICATION"
        
        var identifier: String {
            return self.rawValue
        }
        
        var actions: [UNNotificationAction] {
            switch self {
            case .opportunityAlert:
                return [
                    UNNotificationAction(
                        identifier: "VIEW_OPPORTUNITY",
                        title: "View Details",
                        options: [.foreground]
                    ),
                    UNNotificationAction(
                        identifier: "DISMISS",
                        title: "Dismiss",
                        options: []
                    )
                ]
            case .subscriptionUpdate:
                return [
                    UNNotificationAction(
                        identifier: "MANAGE_SUBSCRIPTION",
                        title: "Manage",
                        options: [.foreground]
                    )
                ]
            case .systemNotification:
                return []
            }
        }
    }
    
    // MARK: - Initialization
    
    init(apiService: APIService = APIService()) {
        self.apiService = apiService
        super.init()
        
        UNUserNotificationCenter.current().delegate = self
        checkAuthorizationStatus()
        setupNotificationCategories()
    }
    
    // MARK: - Public Methods
    
    /// Request notification permissions
    func requestNotificationPermissions() async -> Bool {
        do {
            let granted = try await UNUserNotificationCenter.current().requestAuthorization(
                options: [.alert, .sound, .badge, .providesAppNotificationSettings]
            )
            
            await MainActor.run {
                self.authorizationStatus = granted ? .authorized : .denied
            }
            
            if granted {
                await registerForRemoteNotifications()
            }
            
            return granted
            
        } catch {
            await MainActor.run {
                self.errorMessage = "Failed to request notification permissions: \(error.localizedDescription)"
            }
            return false
        }
    }
    
    /// Register for remote notifications
    @MainActor
    func registerForRemoteNotifications() async {
        guard authorizationStatus == .authorized else { return }
        
        UIApplication.shared.registerForRemoteNotifications()
    }
    
    /// Handle device token registration
    func didRegisterForRemoteNotifications(withDeviceToken deviceToken: Data) {
        let tokenString = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        
        self.deviceToken = tokenString
        
        // Register with backend
        apiService.registerDevice(deviceToken: tokenString)
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { [weak self] completion in
                    switch completion {
                    case .finished:
                        self?.isRegistered = true
                    case .failure(let error):
                        self?.errorMessage = "Failed to register device: \(error.localizedDescription)"
                    }
                },
                receiveValue: { _ in }
            )
            .store(in: &cancellables)
    }
    
    /// Handle registration failure
    func didFailToRegisterForRemoteNotifications(with error: Error) {
        self.errorMessage = "Failed to register for remote notifications: \(error.localizedDescription)"
    }
    
    /// Schedule local notification for high-value opportunity
    func scheduleOpportunityAlert(for opportunity: BettingOpportunity) {
        guard authorizationStatus == .authorized else { return }
        
        let content = UNMutableNotificationContent()
        content.title = "High Value Opportunity!"
        content.body = "\(opportunity.event): \(opportunity.betDesc) (\(opportunity.formattedEVPercentage) EV)"
        content.sound = .default
        content.badge = 1
        content.categoryIdentifier = NotificationCategory.opportunityAlert.identifier
        
        // Add opportunity data
        content.userInfo = [
            "opportunity_id": opportunity.id,
            "event": opportunity.event,
            "ev_percentage": opportunity.evPct,
            "action_url": opportunity.actionUrl ?? ""
        ]
        
        // Schedule immediately
        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: 1, repeats: false)
        let request = UNNotificationRequest(
            identifier: "opportunity_\(opportunity.id)",
            content: content,
            trigger: trigger
        )
        
        UNUserNotificationCenter.current().add(request) { error in
            if let error = error {
                DispatchQueue.main.async {
                    self.errorMessage = "Failed to schedule notification: \(error.localizedDescription)"
                }
            }
        }
    }
    
    /// Schedule subscription update notification
    func scheduleSubscriptionUpdate(title: String, message: String) {
        guard authorizationStatus == .authorized else { return }
        
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = message
        content.sound = .default
        content.categoryIdentifier = NotificationCategory.subscriptionUpdate.identifier
        
        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: 1, repeats: false)
        let request = UNNotificationRequest(
            identifier: "subscription_\(Date().timeIntervalSince1970)",
            content: content,
            trigger: trigger
        )
        
        UNUserNotificationCenter.current().add(request)
    }
    
    /// Remove all pending notifications
    func removeAllPendingNotifications() {
        UNUserNotificationCenter.current().removeAllPendingNotificationRequests()
    }
    
    /// Remove delivered notifications
    func removeAllDeliveredNotifications() {
        UNUserNotificationCenter.current().removeAllDeliveredNotifications()
        UIApplication.shared.applicationIconBadgeNumber = 0
    }
    
    /// Open notification settings
    func openNotificationSettings() {
        if let settingsUrl = URL(string: UIApplication.openSettingsURLString) {
            UIApplication.shared.open(settingsUrl)
        }
    }
    
    // MARK: - Private Methods
    
    /// Check current authorization status
    private func checkAuthorizationStatus() {
        UNUserNotificationCenter.current().getNotificationSettings { [weak self] settings in
            DispatchQueue.main.async {
                self?.authorizationStatus = settings.authorizationStatus
            }
        }
    }
    
    /// Setup notification categories and actions
    private func setupNotificationCategories() {
        let categories = NotificationCategory.allCases.map { category in
            UNNotificationCategory(
                identifier: category.identifier,
                actions: category.actions,
                intentIdentifiers: [],
                options: []
            )
        }
        
        UNUserNotificationCenter.current().setNotificationCategories(Set(categories))
    }
}

// MARK: - UNUserNotificationCenterDelegate

extension PushNotificationService: UNUserNotificationCenterDelegate {
    
    /// Handle notification when app is in foreground
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        // Show notification even when app is in foreground
        completionHandler([.banner, .sound, .badge])
    }
    
    /// Handle notification tap
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        let userInfo = response.notification.request.content.userInfo
        let actionIdentifier = response.actionIdentifier
        
        switch actionIdentifier {
        case "VIEW_OPPORTUNITY":
            handleOpportunityNotificationTap(userInfo: userInfo)
            
        case "MANAGE_SUBSCRIPTION":
            handleSubscriptionNotificationTap()
            
        case UNNotificationDefaultActionIdentifier:
            // Default tap action
            if let _ = userInfo["opportunity_id"] {
                handleOpportunityNotificationTap(userInfo: userInfo)
            }
            
        default:
            break
        }
        
        completionHandler()
    }
    
    /// Handle opportunity notification tap
    private func handleOpportunityNotificationTap(userInfo: [AnyHashable: Any]) {
        guard let opportunityId = userInfo["opportunity_id"] as? String else { return }
        
        // Post notification to navigate to opportunity details
        NotificationCenter.default.post(
            name: .showOpportunityDetails,
            object: nil,
            userInfo: ["opportunity_id": opportunityId]
        )
    }
    
    /// Handle subscription notification tap
    private func handleSubscriptionNotificationTap() {
        // Post notification to show subscription management
        NotificationCenter.default.post(
            name: .showSubscriptionManagement,
            object: nil
        )
    }
}

// MARK: - Notification Names

extension Notification.Name {
    static let showOpportunityDetails = Notification.Name("showOpportunityDetails")
    static let showSubscriptionManagement = Notification.Name("showSubscriptionManagement")
}

// MARK: - User Defaults Extension for Notification Preferences

extension UserDefaults {
    
    enum NotificationKeys {
        static let evThreshold = "notificationEVThreshold"
        static let enabledSports = "notificationEnabledSports"
        static let quietHoursEnabled = "notificationQuietHoursEnabled"
        static let quietHoursStart = "notificationQuietHoursStart"
        static let quietHoursEnd = "notificationQuietHoursEnd"
    }
    
    /// EV threshold for notifications (default: 5.0%)
    var notificationEVThreshold: Double {
        get {
            let value = double(forKey: NotificationKeys.evThreshold)
            return value == 0 ? 5.0 : value
        }
        set { set(newValue, forKey: NotificationKeys.evThreshold) }
    }
    
    /// Enabled sports for notifications
    var notificationEnabledSports: [String] {
        get { stringArray(forKey: NotificationKeys.enabledSports) ?? ["NFL", "NBA", "MLB", "NHL"] }
        set { set(newValue, forKey: NotificationKeys.enabledSports) }
    }
    
    /// Quiet hours enabled
    var notificationQuietHoursEnabled: Bool {
        get { bool(forKey: NotificationKeys.quietHoursEnabled) }
        set { set(newValue, forKey: NotificationKeys.quietHoursEnabled) }
    }
    
    /// Quiet hours start time (24-hour format)
    var notificationQuietHoursStart: Int {
        get {
            let value = integer(forKey: NotificationKeys.quietHoursStart)
            return value == 0 ? 22 : value  // Default: 10 PM
        }
        set { set(newValue, forKey: NotificationKeys.quietHoursStart) }
    }
    
    /// Quiet hours end time (24-hour format)
    var notificationQuietHoursEnd: Int {
        get {
            let value = integer(forKey: NotificationKeys.quietHoursEnd)
            return value == 0 ? 8 : value  // Default: 8 AM
        }
        set { set(newValue, forKey: NotificationKeys.quietHoursEnd) }
    }
}