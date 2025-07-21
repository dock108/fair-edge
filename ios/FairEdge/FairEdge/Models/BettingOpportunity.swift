//
//  BettingOpportunity.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import Foundation

/// Betting opportunity model optimized for mobile API consumption
/// Matches the mobile-optimized response format with 45% payload reduction
struct BettingOpportunity: Codable, Identifiable, Hashable {
    let id: String
    let event: String
    let betDesc: String        // Mobile-optimized field name (was bet_description)
    let betType: String
    let evPct: Double          // Mobile-optimized field name (was ev_percentage)
    let evClass: EVClassification
    let bestOdds: String
    let bestSource: String
    let fairOdds: String
    let sport: String?
    let actionUrl: String?     // Mobile-optimized field name (was action_link)

    // Computed properties for UI display
    var formattedEVPercentage: String {
        return String(format: "%.1f%%", evPct)
    }

    var evColor: String {
        switch evClass {
        case .great:
            return "green"
        case .good:
            return "blue"
        case .neutral:
            return "gray"
        case .poor:
            return "red"
        }
    }

    var displayEvent: String {
        return event.isEmpty ? "Unknown Event" : event
    }

    var displayBetDescription: String {
        return betDesc.isEmpty ? "No description" : betDesc
    }

    // Custom coding keys to match mobile API response
    enum CodingKeys: String, CodingKey {
        case id
        case event
        case betDesc = "bet_desc"
        case betType = "bet_type"
        case evPct = "ev_pct"
        case evClass = "ev_class"
        case bestOdds = "best_odds"
        case bestSource = "best_source"
        case fairOdds = "fair_odds"
        case sport
        case actionUrl = "action_url"
    }
}

/// EV Classification matching backend enum
enum EVClassification: String, Codable, CaseIterable {
    case great
    case good
    case neutral
    case poor

    var displayName: String {
        switch self {
        case .great:
            return "Great"
        case .good:
            return "Good"
        case .neutral:
            return "Neutral"
        case .poor:
            return "Poor"
        }
    }

    var sortOrder: Int {
        switch self {
        case .great:
            return 0
        case .good:
            return 1
        case .neutral:
            return 2
        case .poor:
            return 3
        }
    }
}

/// Response wrapper for opportunities API with mobile metadata
struct OpportunitiesResponse: Codable {
    let opportunities: [BettingOpportunity]
    let metadata: MobileMetadata
}

/// Mobile-specific metadata from optimized API response
struct MobileMetadata: Codable {
    let totalCount: Int
    let cacheStatus: String
    let cacheTimestamp: String
    let updateFrequency: String
    let nextUpdate: String
    let mobileOptimized: Bool
    let payloadReduction: String

    enum CodingKeys: String, CodingKey {
        case totalCount = "total_count"
        case cacheStatus = "cache_status"
        case cacheTimestamp = "cache_timestamp"
        case updateFrequency = "update_frequency"
        case nextUpdate = "next_update"
        case mobileOptimized = "mobile_optimized"
        case payloadReduction = "payload_reduction"
    }
}
