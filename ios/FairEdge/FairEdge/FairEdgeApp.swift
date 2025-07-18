//
//  FairEdgeApp.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import SwiftUI

@main
struct FairEdgeApp: App {
    @StateObject private var authenticationService = AuthenticationService()
    @StateObject private var apiService = APIService()
    @StateObject private var storeKitService = StoreKitService()
    @StateObject private var pushNotificationService = PushNotificationService()
    @StateObject private var webSocketService: WebSocketService
    @StateObject private var analyticsService = AnalyticsService.shared
    
    // App delegate for push notifications
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    
    init() {
        let authService = AuthenticationService()
        let apiService = APIService()
        
        _authenticationService = StateObject(wrappedValue: authService)
        _apiService = StateObject(wrappedValue: apiService)
        _storeKitService = StateObject(wrappedValue: StoreKitService())
        _pushNotificationService = StateObject(wrappedValue: PushNotificationService())
        _webSocketService = StateObject(wrappedValue: WebSocketService(
            authenticationService: authService,
            apiService: apiService
        ))
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(authenticationService)
                .environmentObject(apiService)
                .environmentObject(storeKitService)
                .environmentObject(pushNotificationService)
                .environmentObject(webSocketService)
                .environmentObject(analyticsService)
                .onAppear {
                    // Configure app delegate dependencies
                    appDelegate.pushNotificationService = pushNotificationService
                    
                    // Start WebSocket connection when user is authenticated
                    if authenticationService.isAuthenticated {
                        webSocketService.connect()
                    }
                    
                    // Optimize initial performance
                    Task {
                        await optimizeAppStartup()
                    }
                    
                    // Track app launch
                    analyticsService.trackEvent("app_launched")
                }
        }
    }
    
    // MARK: - Performance Optimization
    
    private func optimizeAppStartup() async {
        // Preload StoreKit products
        await storeKitService.loadProducts()
        
        // Pre-warm API connection for authenticated users
        if authenticationService.isAuthenticated {
            await authenticationService.preloadUserData()
        }
        
        // Initialize push notification permissions
        await pushNotificationService.requestPermissions()
        
        // Send pending crash reports
        await analyticsService.sendPendingCrashReports()
    }
}

// MARK: - App Delegate for Push Notifications

class AppDelegate: NSObject, UIApplicationDelegate {
    var pushNotificationService: PushNotificationService?
    
    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {
        return true
    }
    
    func application(
        _ application: UIApplication,
        didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data
    ) {
        pushNotificationService?.didRegisterForRemoteNotifications(withDeviceToken: deviceToken)
    }
    
    func application(
        _ application: UIApplication,
        didFailToRegisterForRemoteNotificationsWithError error: Error
    ) {
        pushNotificationService?.didFailToRegisterForRemoteNotifications(with: error)
    }
}