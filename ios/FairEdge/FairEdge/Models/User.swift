//
//  User.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import Foundation

/// User model for authentication and subscription management
struct User: Codable, Identifiable {
    let id: String
    let email: String
    let role: UserRole
    let subscriptionStatus: SubscriptionStatus

    var displayName: String {
        return email.components(separatedBy: "@").first ?? "User"
    }

    var isPremiumUser: Bool {
        return role == .premium || role == .admin
    }

    var hasBasicAccess: Bool {
        return role != .free
    }

    enum CodingKeys: String, CodingKey {
        case id
        case email
        case role
        case subscriptionStatus = "subscription_status"
    }
}

/// User role matching backend enum
enum UserRole: String, Codable, CaseIterable {
    case free
    case basic
    case premium
    case admin

    var displayName: String {
        switch self {
        case .free:
            return "Free"
        case .basic:
            return "Basic"
        case .premium:
            return "Premium"
        case .admin:
            return "Admin"
        }
    }

    var features: [String] {
        switch self {
        case .free:
            return ["Limited opportunities", "Basic filtering"]
        case .basic:
            return ["All main lines", "Search functionality", "Unlimited opportunities"]
        case .premium:
            return ["All markets including props", "Advanced filtering", "Export functionality", "Push notifications"]
        case .admin:
            return ["Full access", "Admin features", "System monitoring"]
        }
    }
}

/// Subscription status for Apple IAP integration
enum SubscriptionStatus: String, Codable, CaseIterable {
    case none
    case active
    case expired
    case cancelled
    case pending

    var displayName: String {
        switch self {
        case .none:
            return "No Subscription"
        case .active:
            return "Active"
        case .expired:
            return "Expired"
        case .cancelled:
            return "Cancelled"
        case .pending:
            return "Pending"
        }
    }

    var isActive: Bool {
        return self == .active
    }
}
