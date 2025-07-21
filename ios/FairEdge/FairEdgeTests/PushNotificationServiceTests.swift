//
//  PushNotificationServiceTests.swift
//  FairEdgeTests
//
//  Unit tests for PushNotificationService
//  Tests APNs integration, device token management, and notification handling

import XCTest
import Combine
import UserNotifications
@testable import FairEdge

class PushNotificationServiceTests: XCTestCase {
    
    // MARK: - Properties
    
    var pushService: PushNotificationService!
    var mockUserNotificationCenter: MockUserNotificationCenter!
    var mockAPIService: MockAPIService!
    var cancellables: Set<AnyCancellable>!
    
    // MARK: - Setup & Teardown
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        mockUserNotificationCenter = MockUserNotificationCenter()
        mockAPIService = MockAPIService()
        pushService = PushNotificationService(
            notificationCenter: mockUserNotificationCenter,
            apiService: mockAPIService
        )
        cancellables = Set<AnyCancellable>()
    }
    
    override func tearDownWithError() throws {
        pushService = nil
        mockUserNotificationCenter = nil
        mockAPIService = nil
        cancellables.removeAll()
        cancellables = nil
        try super.tearDownWithError()
    }
    
    // MARK: - Permission Tests
    
    func testRequestPermissions_Success() async throws {
        // Given: User grants permission
        mockUserNotificationCenter.shouldGrantPermission = true
        
        // When: Requesting permissions
        await pushService.requestPermissions()
        
        // Then: Should have permission granted
        XCTAssertTrue(pushService.hasPermission)
        XCTAssertTrue(mockUserNotificationCenter.requestAuthorizationCalled)
    }
    
    func testRequestPermissions_Denied() async throws {
        // Given: User denies permission
        mockUserNotificationCenter.shouldGrantPermission = false
        
        // When: Requesting permissions
        await pushService.requestPermissions()
        
        // Then: Should handle denial gracefully
        XCTAssertFalse(pushService.hasPermission)
        XCTAssertNotNil(pushService.lastError)
    }
    
    func testRequestPermissions_AlreadyGranted() async throws {
        // Given: Permission already granted
        pushService.hasPermission = true
        
        // When: Requesting permissions again
        await pushService.requestPermissions()
        
        // Then: Should not request again
        XCTAssertFalse(mockUserNotificationCenter.requestAuthorizationCalled)
        XCTAssertTrue(pushService.hasPermission)
    }
    
    func testCheckPermissionStatus_Authorized() async throws {
        // Given: Authorized notification settings
        mockUserNotificationCenter.authorizationStatus = .authorized
        
        // When: Checking permission status
        await pushService.checkPermissionStatus()
        
        // Then: Should update permission status
        XCTAssertTrue(pushService.hasPermission)
        XCTAssertTrue(mockUserNotificationCenter.getNotificationSettingsCalled)
    }
    
    func testCheckPermissionStatus_Denied() async throws {
        // Given: Denied notification settings
        mockUserNotificationCenter.authorizationStatus = .denied
        
        // When: Checking permission status
        await pushService.checkPermissionStatus()
        
        // Then: Should update permission status
        XCTAssertFalse(pushService.hasPermission)
    }
    
    func testCheckPermissionStatus_NotDetermined() async throws {
        // Given: Not determined notification settings
        mockUserNotificationCenter.authorizationStatus = .notDetermined
        
        // When: Checking permission status
        await pushService.checkPermissionStatus()
        
        // Then: Should not have permission yet
        XCTAssertFalse(pushService.hasPermission)
    }
    
    // MARK: - Device Token Tests
    
    func testRegisterDeviceToken_Success() throws {
        // Given: Valid device token
        let deviceToken = Data([0x01, 0x02, 0x03, 0x04, 0x05])
        mockAPIService.shouldRegisterDeviceSucceed = true
        
        let expectation = XCTestExpectation(description: "Device token registered")
        
        // When: Registering device token
        pushService.didRegisterForRemoteNotifications(withDeviceToken: deviceToken)
        
        // Then: Should register with API
        pushService.$deviceToken
            .compactMap { $0 }
            .sink { token in
                XCTAssertEqual(token, deviceToken.hexString)
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testRegisterDeviceToken_APIFailure() throws {
        // Given: API registration failure
        let deviceToken = Data([0x01, 0x02, 0x03, 0x04, 0x05])
        mockAPIService.shouldRegisterDeviceSucceed = false
        
        let expectation = XCTestExpectation(description: "API failure handled")
        
        // When: Registering device token
        pushService.didRegisterForRemoteNotifications(withDeviceToken: deviceToken)
        
        // Then: Should handle API failure
        pushService.$lastError
            .compactMap { $0 }
            .sink { error in
                XCTAssertNotNil(error)
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testRegisterDeviceToken_EmptyToken() throws {
        // Given: Empty device token
        let deviceToken = Data()
        
        // When: Registering empty device token
        pushService.didRegisterForRemoteNotifications(withDeviceToken: deviceToken)
        
        // Then: Should handle gracefully
        XCTAssertNil(pushService.deviceToken)
        XCTAssertNotNil(pushService.lastError)
    }
    
    func testFailToRegisterDeviceToken() throws {
        // Given: Registration failure
        let error = NSError(domain: "TestError", code: 1001, userInfo: [NSLocalizedDescriptionKey: "Registration failed"])
        
        let expectation = XCTestExpectation(description: "Registration failure handled")
        
        // When: Failing to register
        pushService.didFailToRegisterForRemoteNotifications(with: error)
        
        // Then: Should handle failure
        pushService.$lastError
            .compactMap { $0 }
            .sink { registrationError in
                XCTAssertEqual(registrationError.localizedDescription, "Registration failed")
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    // MARK: - Notification Handling Tests
    
    func testHandleIncomingNotification_OpportunityAlert() throws {
        // Given: Opportunity notification payload
        let userInfo: [AnyHashable: Any] = [
            "type": "opportunity_alert",
            "opportunity_id": "test_opp_123",
            "title": "New Betting Opportunity",
            "message": "Lakers vs Warriors - LeBron Points Over 25.5 (+150, 12.5% EV)",
            "ev_percentage": 12.5,
            "sport": "NBA"
        ]
        
        let expectation = XCTestExpectation(description: "Notification handled")
        
        // When: Handling notification
        pushService.handleNotification(userInfo: userInfo)
        
        // Then: Should parse and handle opportunity
        pushService.$lastNotification
            .compactMap { $0 }
            .sink { notification in
                XCTAssertEqual(notification.type, .opportunityAlert)
                XCTAssertEqual(notification.opportunityId, "test_opp_123")
                XCTAssertEqual(notification.evPercentage, 12.5)
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testHandleIncomingNotification_SubscriptionUpdate() throws {
        // Given: Subscription update payload
        let userInfo: [AnyHashable: Any] = [
            "type": "subscription_update",
            "title": "Subscription Updated",
            "message": "Your Premium subscription has been renewed",
            "subscription_status": "active",
            "expires_date": "2025-02-20T12:00:00Z"
        ]
        
        let expectation = XCTestExpectation(description: "Subscription notification handled")
        
        // When: Handling notification
        pushService.handleNotification(userInfo: userInfo)
        
        // Then: Should parse subscription update
        pushService.$lastNotification
            .compactMap { $0 }
            .sink { notification in
                XCTAssertEqual(notification.type, .subscriptionUpdate)
                XCTAssertEqual(notification.subscriptionStatus, "active")
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testHandleIncomingNotification_GeneralAlert() throws {
        // Given: General alert payload
        let userInfo: [AnyHashable: Any] = [
            "type": "general_alert",
            "title": "Fair-Edge Update",
            "message": "New features available in the latest update!",
            "action_url": "https://fair-edge.com/updates"
        ]
        
        let expectation = XCTestExpectation(description: "General alert handled")
        
        // When: Handling notification
        pushService.handleNotification(userInfo: userInfo)
        
        // Then: Should parse general alert
        pushService.$lastNotification
            .compactMap { $0 }
            .sink { notification in
                XCTAssertEqual(notification.type, .generalAlert)
                XCTAssertEqual(notification.actionUrl, "https://fair-edge.com/updates")
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testHandleIncomingNotification_InvalidPayload() throws {
        // Given: Invalid notification payload
        let userInfo: [AnyHashable: Any] = [
            "invalid_key": "invalid_value"
        ]
        
        // When: Handling invalid notification
        pushService.handleNotification(userInfo: userInfo)
        
        // Then: Should handle gracefully
        XCTAssertNotNil(pushService.lastError)
        XCTAssertNil(pushService.lastNotification)
    }
    
    // MARK: - Background Notification Tests
    
    func testHandleBackgroundNotification_SilentUpdate() throws {
        // Given: Silent background notification
        let userInfo: [AnyHashable: Any] = [
            "type": "silent_update",
            "content-available": 1,
            "update_type": "opportunities_refresh"
        ]
        
        let expectation = XCTestExpectation(description: "Background notification handled")
        
        // When: Handling background notification
        pushService.handleBackgroundNotification(userInfo: userInfo) { result in
            // Then: Should trigger background refresh
            XCTAssertEqual(result, .newData)
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testHandleBackgroundNotification_NoUpdate() throws {
        // Given: Background notification with no updates
        let userInfo: [AnyHashable: Any] = [
            "type": "silent_update",
            "content-available": 1,
            "update_type": "no_updates"
        ]
        
        let expectation = XCTestExpectation(description: "No update handled")
        
        // When: Handling background notification
        pushService.handleBackgroundNotification(userInfo: userInfo) { result in
            // Then: Should indicate no new data
            XCTAssertEqual(result, .noData)
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testHandleBackgroundNotification_Failed() throws {
        // Given: Failed background notification
        mockAPIService.shouldBackgroundUpdateFail = true
        
        let userInfo: [AnyHashable: Any] = [
            "type": "silent_update",
            "content-available": 1,
            "update_type": "opportunities_refresh"
        ]
        
        let expectation = XCTestExpectation(description: "Background update failed")
        
        // When: Handling background notification
        pushService.handleBackgroundNotification(userInfo: userInfo) { result in
            // Then: Should indicate failure
            XCTAssertEqual(result, .failed)
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    // MARK: - Notification Preferences Tests
    
    func testUpdateNotificationPreferences_Success() async throws {
        // Given: New notification preferences
        let preferences = NotificationPreferences(
            evThreshold: 8.5,
            enabledSports: ["NFL", "NBA"],
            quietHoursEnabled: true,
            quietHoursStart: 22,
            quietHoursEnd: 8
        )
        
        mockAPIService.shouldUpdatePreferencesSucceed = true
        
        // When: Updating preferences
        await pushService.updateNotificationPreferences(preferences)
        
        // Then: Should update successfully
        XCTAssertEqual(pushService.notificationPreferences?.evThreshold, 8.5)
        XCTAssertEqual(pushService.notificationPreferences?.enabledSports, ["NFL", "NBA"])
        XCTAssertTrue(pushService.notificationPreferences?.quietHoursEnabled ?? false)
    }
    
    func testUpdateNotificationPreferences_APIFailure() async throws {
        // Given: API failure for preferences update
        let preferences = NotificationPreferences(
            evThreshold: 8.5,
            enabledSports: ["NFL", "NBA"],
            quietHoursEnabled: true,
            quietHoursStart: 22,
            quietHoursEnd: 8
        )
        
        mockAPIService.shouldUpdatePreferencesSucceed = false
        
        // When: Updating preferences
        await pushService.updateNotificationPreferences(preferences)
        
        // Then: Should handle failure
        XCTAssertNotNil(pushService.lastError)
        XCTAssertNil(pushService.notificationPreferences)
    }
    
    func testQuietHours_DuringQuietTime() throws {
        // Given: Quiet hours enabled and current time is during quiet hours
        let preferences = NotificationPreferences(
            evThreshold: 5.0,
            enabledSports: ["NFL"],
            quietHoursEnabled: true,
            quietHoursStart: 22,
            quietHoursEnd: 8
        )
        pushService.notificationPreferences = preferences
        
        // Mock current time as 2 AM (during quiet hours)
        let dateComponents = DateComponents(hour: 2, minute: 0)
        let mockDate = Calendar.current.date(from: dateComponents)!
        
        // When: Checking if should show notification
        let shouldShow = pushService.shouldShowNotification(at: mockDate)
        
        // Then: Should not show notification during quiet hours
        XCTAssertFalse(shouldShow)
    }
    
    func testQuietHours_OutsideQuietTime() throws {
        // Given: Quiet hours enabled and current time is outside quiet hours
        let preferences = NotificationPreferences(
            evThreshold: 5.0,
            enabledSports: ["NFL"],
            quietHoursEnabled: true,
            quietHoursStart: 22,
            quietHoursEnd: 8
        )
        pushService.notificationPreferences = preferences
        
        // Mock current time as 10 AM (outside quiet hours)
        let dateComponents = DateComponents(hour: 10, minute: 0)
        let mockDate = Calendar.current.date(from: dateComponents)!
        
        // When: Checking if should show notification
        let shouldShow = pushService.shouldShowNotification(at: mockDate)
        
        // Then: Should show notification outside quiet hours
        XCTAssertTrue(shouldShow)
    }
    
    // MARK: - Local Notification Tests
    
    func testScheduleLocalNotification_Success() async throws {
        // Given: Valid notification content
        let content = UNMutableNotificationContent()
        content.title = "Test Notification"
        content.body = "This is a test notification"
        content.sound = .default
        
        mockUserNotificationCenter.shouldScheduleSucceed = true
        
        // When: Scheduling local notification
        await pushService.scheduleLocalNotification(content: content, identifier: "test_notification")
        
        // Then: Should schedule successfully
        XCTAssertTrue(mockUserNotificationCenter.addNotificationRequestCalled)
        XCTAssertNil(pushService.lastError)
    }
    
    func testScheduleLocalNotification_PermissionDenied() async throws {
        // Given: Permission denied
        pushService.hasPermission = false
        
        let content = UNMutableNotificationContent()
        content.title = "Test Notification"
        content.body = "This is a test notification"
        
        // When: Attempting to schedule notification
        await pushService.scheduleLocalNotification(content: content, identifier: "test_notification")
        
        // Then: Should handle permission denial
        XCTAssertNotNil(pushService.lastError)
        XCTAssertFalse(mockUserNotificationCenter.addNotificationRequestCalled)
    }
    
    func testCancelLocalNotification() throws {
        // Given: Scheduled notification
        let identifier = "test_notification"
        
        // When: Canceling notification
        pushService.cancelLocalNotification(withIdentifier: identifier)
        
        // Then: Should cancel notification
        XCTAssertTrue(mockUserNotificationCenter.removePendingNotificationRequestsCalled)
    }
    
    // MARK: - Performance Tests
    
    func testNotificationProcessingPerformance() throws {
        // Given: Large number of notifications
        let notifications = Array(0..<1000).map { index in
            return [
                "type": "opportunity_alert",
                "opportunity_id": "test_opp_\(index)",
                "title": "Opportunity \(index)",
                "message": "Test opportunity \(index)",
                "ev_percentage": Double(index % 20)
            ] as [AnyHashable: Any]
        }
        
        // When: Processing notifications
        measure {
            for notification in notifications {
                pushService.handleNotification(userInfo: notification)
            }
        }
    }
    
    func testDeviceTokenConversionPerformance() throws {
        // Given: Large device token
        let deviceToken = Data(repeating: 0xFF, count: 32)
        
        // When: Converting token to hex string
        measure {
            for _ in 0..<10000 {
                _ = deviceToken.hexString
            }
        }
    }
}

// MARK: - Test Utilities

extension PushNotificationServiceTests {
    
    func createMockNotificationPreferences() -> NotificationPreferences {
        return NotificationPreferences(
            evThreshold: 5.0,
            enabledSports: ["NFL", "NBA", "MLB"],
            quietHoursEnabled: true,
            quietHoursStart: 22,
            quietHoursEnd: 8
        )
    }
}

// MARK: - Mock Classes

class MockUserNotificationCenter: UNUserNotificationCenter {
    var shouldGrantPermission = true
    var shouldScheduleSucceed = true
    var authorizationStatus: UNAuthorizationStatus = .notDetermined
    
    var requestAuthorizationCalled = false
    var getNotificationSettingsCalled = false
    var addNotificationRequestCalled = false
    var removePendingNotificationRequestsCalled = false
    
    override func requestAuthorization(options: UNAuthorizationOptions) async throws -> Bool {
        requestAuthorizationCalled = true
        if shouldGrantPermission {
            authorizationStatus = .authorized
            return true
        } else {
            authorizationStatus = .denied
            throw NSError(domain: "TestError", code: 1001, userInfo: [NSLocalizedDescriptionKey: "Permission denied"])
        }
    }
    
    override func getNotificationSettings() async -> UNNotificationSettings {
        getNotificationSettingsCalled = true
        return MockNotificationSettings(authorizationStatus: authorizationStatus)
    }
    
    override func add(_ request: UNNotificationRequest) async throws {
        addNotificationRequestCalled = true
        if !shouldScheduleSucceed {
            throw NSError(domain: "TestError", code: 1002, userInfo: [NSLocalizedDescriptionKey: "Schedule failed"])
        }
    }
    
    override func removePendingNotificationRequests(withIdentifiers identifiers: [String]) {
        removePendingNotificationRequestsCalled = true
    }
}

class MockNotificationSettings: UNNotificationSettings {
    private let _authorizationStatus: UNAuthorizationStatus
    
    init(authorizationStatus: UNAuthorizationStatus) {
        _authorizationStatus = authorizationStatus
        super.init()
    }
    
    override var authorizationStatus: UNAuthorizationStatus {
        return _authorizationStatus
    }
}

// MARK: - Extensions

extension Data {
    var hexString: String {
        return map { String(format: "%02hhx", $0) }.joined()
    }
}

// MARK: - Models

struct NotificationPreferences {
    let evThreshold: Double
    let enabledSports: [String]
    let quietHoursEnabled: Bool
    let quietHoursStart: Int
    let quietHoursEnd: Int
}

struct PushNotification {
    enum NotificationType {
        case opportunityAlert
        case subscriptionUpdate
        case generalAlert
    }
    
    let type: NotificationType
    let title: String
    let message: String
    let opportunityId: String?
    let evPercentage: Double?
    let subscriptionStatus: String?
    let actionUrl: String?
}

// MARK: - Background Fetch Results

extension UIBackgroundFetchResult {
    static let newData = UIBackgroundFetchResult.newData
    static let noData = UIBackgroundFetchResult.noData
    static let failed = UIBackgroundFetchResult.failed
}