//
//  AppleIAP.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import Foundation

// MARK: - Receipt Validation

/// Receipt validation request for backend validation
struct ReceiptValidationRequest: Codable {
    let receiptData: String
    let productId: String
    let transactionId: String
    
    enum CodingKeys: String, CodingKey {
        case receiptData = "receipt_data"
        case productId = "product_id" 
        case transactionId = "transaction_id"
    }
}

/// Receipt validation response from backend
struct ReceiptValidationResponse: Codable {
    let success: Bool
    let userRole: String?
    let subscriptionStatus: String?
    let expirationDate: String?
    let message: String?
    let validationDetails: ValidationDetails?
    
    enum CodingKeys: String, CodingKey {
        case success
        case userRole = "user_role"
        case subscriptionStatus = "subscription_status"
        case expirationDate = "expiration_date"
        case message
        case validationDetails = "validation_details"
    }
}

/// Detailed validation information
struct ValidationDetails: Codable {
    let appleValidationStatus: Int
    let isActive: Bool
    let productId: String
    let purchaseDate: String?
    let expiresDate: String?
    
    enum CodingKeys: String, CodingKey {
        case appleValidationStatus = "apple_validation_status"
        case isActive = "is_active"
        case productId = "product_id"
        case purchaseDate = "purchase_date"
        case expiresDate = "expires_date"
    }
}

// MARK: - Subscription Status

/// Subscription status response
struct SubscriptionStatusResponse: Codable {
    let hasActiveSubscription: Bool
    let currentPlan: String?
    let subscriptionStatus: String
    let expirationDate: String?
    let nextBillingDate: String?
    let features: [String]
    let canUpgrade: Bool
    let availableUpgrades: [String]
    
    enum CodingKeys: String, CodingKey {
        case hasActiveSubscription = "has_active_subscription"
        case currentPlan = "current_plan"
        case subscriptionStatus = "subscription_status"
        case expirationDate = "expiration_date"
        case nextBillingDate = "next_billing_date"
        case features
        case canUpgrade = "can_upgrade"
        case availableUpgrades = "available_upgrades"
    }
}

// MARK: - Restore Purchases

/// Restore purchases response
struct RestorePurchasesResponse: Codable {
    let success: Bool
    let restoredPurchases: [RestoredPurchase]
    let currentSubscription: CurrentSubscription?
    let message: String?
    
    enum CodingKeys: String, CodingKey {
        case success
        case restoredPurchases = "restored_purchases"
        case currentSubscription = "current_subscription"
        case message
    }
}

/// Individual restored purchase
struct RestoredPurchase: Codable {
    let productId: String
    let purchaseDate: String
    let expirationDate: String?
    let isActive: Bool
    
    enum CodingKeys: String, CodingKey {
        case productId = "product_id"
        case purchaseDate = "purchase_date"
        case expirationDate = "expiration_date"
        case isActive = "is_active"
    }
}

/// Current subscription information
struct CurrentSubscription: Codable {
    let productId: String
    let plan: String
    let status: String
    let purchaseDate: String
    let expirationDate: String?
    let autoRenewStatus: Bool
    
    enum CodingKeys: String, CodingKey {
        case productId = "product_id"
        case plan
        case status
        case purchaseDate = "purchase_date"
        case expirationDate = "expiration_date"
        case autoRenewStatus = "auto_renew_status"
    }
}

// MARK: - Apple Products

/// Apple products response from backend
struct AppleProductsResponse: Codable {
    let products: [AppleProduct]
    let subscriptionGroups: [SubscriptionGroup]
    
    enum CodingKeys: String, CodingKey {
        case products
        case subscriptionGroups = "subscription_groups"
    }
}

/// Apple product information
struct AppleProduct: Codable {
    let productId: String
    let name: String
    let description: String
    let price: String
    let priceTier: String
    let subscriptionPeriod: String?
    let subscriptionGroup: String?
    let features: [String]
    
    enum CodingKeys: String, CodingKey {
        case productId = "product_id"
        case name
        case description
        case price
        case priceTier = "price_tier"
        case subscriptionPeriod = "subscription_period"
        case subscriptionGroup = "subscription_group"
        case features
    }
}

/// Subscription group information
struct SubscriptionGroup: Codable {
    let groupId: String
    let name: String
    let products: [String]
    
    enum CodingKeys: String, CodingKey {
        case groupId = "group_id"
        case name
        case products
    }
}

// MARK: - App Store Server Notifications

/// App Store server notification payload
struct AppStoreNotification: Codable {
    let notificationType: String
    let subtype: String?
    let notificationUUID: String
    let data: NotificationData
    let version: String
    let signedDate: Int64
    
    enum CodingKeys: String, CodingKey {
        case notificationType = "notificationType"
        case subtype
        case notificationUUID = "notificationUUID"
        case data
        case version
        case signedDate = "signedDate"
    }
}

/// Notification data payload
struct NotificationData: Codable {
    let appAppleId: Int
    let bundleId: String
    let bundleVersion: String
    let environment: String
    let signedTransactionInfo: String
    let signedRenewalInfo: String?
    
    enum CodingKeys: String, CodingKey {
        case appAppleId = "appAppleId"
        case bundleId = "bundleId"
        case bundleVersion = "bundleVersion"
        case environment
        case signedTransactionInfo = "signedTransactionInfo"
        case signedRenewalInfo = "signedRenewalInfo"
    }
}

// MARK: - Error Types

/// Apple IAP specific errors
enum AppleIAPError: Error, LocalizedError {
    case invalidReceipt
    case validationFailed
    case noActiveSubscription
    case subscriptionExpired
    case productNotFound
    case purchaseNotAllowed
    case restoreFailed
    case networkError
    
    var errorDescription: String? {
        switch self {
        case .invalidReceipt:
            return "Invalid receipt data"
        case .validationFailed:
            return "Receipt validation failed"
        case .noActiveSubscription:
            return "No active subscription found"
        case .subscriptionExpired:
            return "Subscription has expired"
        case .productNotFound:
            return "Product not found in App Store"
        case .purchaseNotAllowed:
            return "Purchases are not allowed on this device"
        case .restoreFailed:
            return "Failed to restore previous purchases"
        case .networkError:
            return "Network connection required"
        }
    }
    
    var recoverySuggestion: String? {
        switch self {
        case .invalidReceipt, .validationFailed:
            return "Please try purchasing again."
        case .noActiveSubscription:
            return "Purchase a subscription to access premium features."
        case .subscriptionExpired:
            return "Renew your subscription to continue using premium features."
        case .productNotFound:
            return "Please try again later or contact support."
        case .purchaseNotAllowed:
            return "Check your device settings to allow purchases."
        case .restoreFailed:
            return "Make sure you're signed in with the same Apple ID."
        case .networkError:
            return "Check your internet connection and try again."
        }
    }
}