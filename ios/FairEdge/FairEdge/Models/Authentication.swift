//
//  Authentication.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import Foundation

/// Mobile session request for optimized authentication
struct MobileSessionRequest: Codable {
    let email: String
    let password: String?  // Optional for Sign in with Apple
    let deviceId: String
    let deviceType: String
    let appVersion: String
    let appleIdToken: String?  // For Sign in with Apple

    enum CodingKeys: String, CodingKey {
        case email
        case password
        case deviceId = "device_id"
        case deviceType = "device_type"
        case appVersion = "app_version"
        case appleIdToken = "apple_id_token"
    }
}

/// Mobile session response with 24-hour tokens
struct MobileSessionResponse: Codable {
    let success: Bool
    let accessToken: String
    let refreshToken: String
    let expiresIn: Int  // 24 hours for mobile
    let tokenType: String
    let userInfo: UserInfo
    let deviceInfo: DeviceInfo
    let sessionConfig: SessionConfig

    enum CodingKeys: String, CodingKey {
        case success
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case expiresIn = "expires_in"
        case tokenType = "token_type"
        case userInfo = "user_info"
        case deviceInfo = "device_info"
        case sessionConfig = "session_config"
    }
}

/// User information from mobile session
struct UserInfo: Codable {
    let email: String
    let role: String
    let subscriptionStatus: String
    let mobileOptimized: Bool

    enum CodingKeys: String, CodingKey {
        case email
        case role
        case subscriptionStatus = "subscription_status"
        case mobileOptimized = "mobile_optimized"
    }
}

/// Device information for session tracking
struct DeviceInfo: Codable {
    let deviceId: String
    let deviceType: String
    let appVersion: String
    let registeredAt: String

    enum CodingKeys: String, CodingKey {
        case deviceId = "device_id"
        case deviceType = "device_type"
        case appVersion = "app_version"
        case registeredAt = "registered_at"
    }
}

/// Session configuration for mobile app
struct SessionConfig: Codable {
    let apiVersion: String
    let cacheDuration: Int  // 5 minutes
    let refreshThreshold: Int  // 1 hour before expiry
    let backgroundRefreshEnabled: Bool

    enum CodingKeys: String, CodingKey {
        case apiVersion = "api_version"
        case cacheDuration = "cache_duration"
        case refreshThreshold = "refresh_threshold"
        case backgroundRefreshEnabled = "background_refresh_enabled"
    }
}

/// Auth token for token refresh
struct AuthToken: Codable {
    let accessToken: String
    let refreshToken: String
    let expiresIn: Int
    let tokenType: String

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case expiresIn = "expires_in"
        case tokenType = "token_type"
    }
}

/// Token refresh request
struct TokenRefreshRequest: Codable {
    let refreshToken: String
    let deviceId: String

    enum CodingKeys: String, CodingKey {
        case refreshToken = "refresh_token"
        case deviceId = "device_id"
    }
}
