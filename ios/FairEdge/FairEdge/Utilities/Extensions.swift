//
//  Extensions.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import Foundation
import UIKit

// MARK: - Bundle Extensions

extension Bundle {
    /// Get app version from Info.plist
    var appVersion: String {
        return infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
    }

    /// Get build number from Info.plist
    var buildNumber: String {
        return infoDictionary?["CFBundleVersion"] as? String ?? "1"
    }

    /// Get full version string
    var fullVersion: String {
        return "\(appVersion) (\(buildNumber))"
    }
}

// MARK: - String Extensions

extension String {
    /// Check if string is a valid email
    var isValidEmail: Bool {
        let emailRegex = "^[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$"
        let emailPredicate = NSPredicate(format: "SELF MATCHES %@", emailRegex)
        return emailPredicate.evaluate(with: self)
    }

    /// Truncate string to specified length
    func truncated(to length: Int) -> String {
        return count > length ? String(prefix(length)) + "..." : self
    }
}

// MARK: - Double Extensions

extension Double {
    /// Format as percentage with specified decimal places
    func asPercentage(decimalPlaces: Int = 1) -> String {
        return String(format: "%.\(decimalPlaces)f%%", self)
    }

    /// Format as currency
    func asCurrency() -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = "USD"
        return formatter.string(from: NSNumber(value: self)) ?? "$0.00"
    }
}

// MARK: - Date Extensions

extension Date {
    /// Format date for API requests (ISO 8601)
    var apiFormat: String {
        let formatter = ISO8601DateFormatter()
        return formatter.string(from: self)
    }

    /// Format date for display
    var displayFormat: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: self)
    }

    /// Check if date is today
    var isToday: Bool {
        return Calendar.current.isDateInToday(self)
    }
}

// MARK: - Color Extensions

extension UIColor {
    /// Colors for EV classifications
    static let evGreat = UIColor.systemGreen
    static let evGood = UIColor.systemBlue
    static let evNeutral = UIColor.systemGray
    static let evPoor = UIColor.systemRed

    /// App brand colors
    static let primaryBrand = UIColor.systemBlue
    static let secondaryBrand = UIColor.systemGray

    /// Create color from hex string
    convenience init?(hex: String) {
        let red, green, blue, alpha: CGFloat

        if hex.hasPrefix("#") {
            let start = hex.index(hex.startIndex, offsetBy: 1)
            let hexColor = String(hex[start...])

            if hexColor.count == 8 {
                let scanner = Scanner(string: hexColor)
                var hexNumber: UInt64 = 0

                if scanner.scanHexInt64(&hexNumber) {
                    red = CGFloat((hexNumber & 0xff000000) >> 24) / 255
                    green = CGFloat((hexNumber & 0x00ff0000) >> 16) / 255
                    blue = CGFloat((hexNumber & 0x0000ff00) >> 8) / 255
                    alpha = CGFloat(hexNumber & 0x000000ff) / 255

                    self.init(red: red, green: green, blue: blue, alpha: alpha)
                    return
                }
            } else if hexColor.count == 6 {
                let scanner = Scanner(string: hexColor)
                var hexNumber: UInt64 = 0

                if scanner.scanHexInt64(&hexNumber) {
                    red = CGFloat((hexNumber & 0xff0000) >> 16) / 255
                    green = CGFloat((hexNumber & 0x00ff00) >> 8) / 255
                    blue = CGFloat((hexNumber & 0x0000ff)) / 255
                    alpha = 1.0

                    self.init(red: red, green: green, blue: blue, alpha: alpha)
                    return
                }
            }
        }

        return nil
    }
}

// MARK: - UserDefaults Extensions

extension UserDefaults {
    /// App-specific keys
    enum Keys {
        static let hasSeenOnboarding = "hasSeenOnboarding"
        static let notificationSettings = "notificationSettings"
        static let evThreshold = "evThreshold"
        static let selectedSports = "selectedSports"
    }

    /// Check if user has seen onboarding
    var hasSeenOnboarding: Bool {
        get { bool(forKey: Keys.hasSeenOnboarding) }
        set { set(newValue, forKey: Keys.hasSeenOnboarding) }
    }

    /// EV threshold for notifications
    var evThreshold: Double {
        get {
            let value = double(forKey: Keys.evThreshold)
            return value == 0 ? 5.0 : value  // Default to 5%
        }
        set { set(newValue, forKey: Keys.evThreshold) }
    }
}

// MARK: - Array Extensions

extension Array where Element == BettingOpportunity {
    /// Filter opportunities by EV classification
    func filtered(by classification: EVClassification) -> [BettingOpportunity] {
        return filter { $0.evClass == classification }
    }

    /// Sort by EV percentage (highest first)
    func sortedByEV() -> [BettingOpportunity] {
        return sorted { $0.evPct > $1.evPct }
    }

    /// Filter by minimum EV threshold
    func filtered(minimumEV: Double) -> [BettingOpportunity] {
        return filter { $0.evPct >= minimumEV }
    }

    /// Filter by sport
    func filtered(by sport: String) -> [BettingOpportunity] {
        return filter { $0.sport?.lowercased() == sport.lowercased() }
    }
}
