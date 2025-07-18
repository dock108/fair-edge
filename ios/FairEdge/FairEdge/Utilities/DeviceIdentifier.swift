//
//  DeviceIdentifier.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import Foundation
import UIKit

/// Device identifier utility for consistent device tracking
class DeviceIdentifier {
    
    static let shared = DeviceIdentifier()
    
    private let keychainKey = "device_identifier"
    
    private init() {}
    
    /// Get or create a persistent device identifier
    var deviceId: String? {
        // Try to get existing identifier from keychain
        if let existingId = KeychainService.shared.retrieve(for: keychainKey) {
            return existingId
        }
        
        // Create new identifier
        let newId = UUID().uuidString
        
        // Store in keychain for persistence
        if KeychainService.shared.store(token: newId, for: keychainKey) {
            return newId
        }
        
        // Fallback to vendor identifier if keychain fails
        return UIDevice.current.identifierForVendor?.uuidString
    }
    
    /// Get device type information
    var deviceType: String {
        switch UIDevice.current.userInterfaceIdiom {
        case .phone:
            return "iPhone"
        case .pad:
            return "iPad"
        case .tv:
            return "Apple TV"
        case .mac:
            return "Mac"
        case .carPlay:
            return "CarPlay"
        case .vision:
            return "Vision Pro"
        default:
            return "Unknown"
        }
    }
    
    /// Get device model information
    var deviceModel: String {
        var systemInfo = utsname()
        uname(&systemInfo)
        let machineMirror = Mirror(reflecting: systemInfo.machine)
        let identifier = machineMirror.children.reduce("") { identifier, element in
            guard let value = element.value as? Int8, value != 0 else { return identifier }
            return identifier + String(UnicodeScalar(UInt8(value))!)
        }
        return identifier.isEmpty ? "Unknown" : identifier
    }
    
    /// Get iOS version
    var systemVersion: String {
        return UIDevice.current.systemVersion
    }
    
    /// Get comprehensive device info for API requests
    var deviceInfo: [String: String] {
        return [
            "device_id": deviceId ?? "unknown",
            "device_type": deviceType,
            "device_model": deviceModel,
            "system_version": systemVersion,
            "app_version": Bundle.main.appVersion
        ]
    }
}