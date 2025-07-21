//
//  MobileConfig.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import Foundation

/// Mobile app configuration from /api/mobile/config endpoint
struct MobileConfig: Codable {
    let apiVersion: String
    let features: Features
    let limits: Limits
    let cache: CacheConfig
    let push: PushConfig
    let appStore: AppStoreConfig

    enum CodingKeys: String, CodingKey {
        case apiVersion = "api_version"
        case features
        case limits
        case cache
        case push
        case appStore = "app_store"
    }
}

/// Feature flags for mobile app
struct Features: Codable {
    let realTimeUpdates: Bool
    let pushNotifications: Bool
    let appleIAP: Bool
    let backgroundRefresh: Bool
    let offlineMode: Bool

    enum CodingKeys: String, CodingKey {
        case realTimeUpdates = "real_time_updates"
        case pushNotifications = "push_notifications"
        case appleIAP = "apple_iap"
        case backgroundRefresh = "background_refresh"
        case offlineMode = "offline_mode"
    }
}

/// Rate limits and access limits
struct Limits: Codable {
    let freeUserOpportunities: Int
    let apiRequestsPerMinute: Int
    let cacheTimeoutSeconds: Int
    let maxRetryAttempts: Int

    enum CodingKeys: String, CodingKey {
        case freeUserOpportunities = "free_user_opportunities"
        case apiRequestsPerMinute = "api_requests_per_minute"
        case cacheTimeoutSeconds = "cache_timeout_seconds"
        case maxRetryAttempts = "max_retry_attempts"
    }
}

/// Cache configuration
struct CacheConfig: Codable {
    let opportunitiesTTL: Int
    let userDataTTL: Int
    let configTTL: Int
    let enableCompression: Bool

    enum CodingKeys: String, CodingKey {
        case opportunitiesTTL = "opportunities_ttl"
        case userDataTTL = "user_data_ttl"
        case configTTL = "config_ttl"
        case enableCompression = "enable_compression"
    }
}

/// Push notification configuration
struct PushConfig: Codable {
    let enabled: Bool
    let topics: [String]
    let defaultThreshold: Double
    let quietHoursStart: String
    let quietHoursEnd: String

    enum CodingKeys: String, CodingKey {
        case enabled
        case topics
        case defaultThreshold = "default_threshold"
        case quietHoursStart = "quiet_hours_start"
        case quietHoursEnd = "quiet_hours_end"
    }
}

/// App Store configuration for IAP
struct AppStoreConfig: Codable {
    let basicMonthlyProductId: String
    let premiumMonthlyProductId: String
    let premiumYearlyProductId: String
    let subscriptionGroupId: String

    enum CodingKeys: String, CodingKey {
        case basicMonthlyProductId = "basic_monthly_product_id"
        case premiumMonthlyProductId = "premium_monthly_product_id"
        case premiumYearlyProductId = "premium_yearly_product_id"
        case subscriptionGroupId = "subscription_group_id"
    }
}

/// Mobile health check response
struct MobileHealthResponse: Codable {
    let status: String
    let timestamp: String
    let version: String
    let uptime: String
    let services: HealthServices

    enum CodingKeys: String, CodingKey {
        case status
        case timestamp
        case version
        case uptime
        case services
    }
}

/// Health status of backend services
struct HealthServices: Codable {
    let database: String
    let redis: String
    let appleIAP: String
    let pushNotifications: String

    enum CodingKeys: String, CodingKey {
        case database
        case redis
        case appleIAP = "apple_iap"
        case pushNotifications = "push_notifications"
    }
}
