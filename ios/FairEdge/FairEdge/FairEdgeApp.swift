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
    
    // App delegate for push notifications
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(authenticationService)
                .environmentObject(apiService)
                .environmentObject(storeKitService)
                .environmentObject(pushNotificationService)
                .onAppear {
                    // Configure app delegate dependencies
                    appDelegate.pushNotificationService = pushNotificationService
                }
        }
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