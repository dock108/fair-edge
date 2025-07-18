//
//  AnalyticsService.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import Foundation
import UIKit
import os.log

/// Analytics and crash reporting service for TestFlight and production
@MainActor
class AnalyticsService: ObservableObject {
    
    // MARK: - Singleton
    
    static let shared = AnalyticsService()
    
    // MARK: - Properties
    
    private let logger = Logger(subsystem: "com.fairedge.app", category: "Analytics")
    private var sessionStartTime: Date?
    private var crashReports: [CrashReport] = []
    
    // MARK: - Initialization
    
    private init() {
        setupCrashReporting()
        startSession()
    }
    
    // MARK: - Session Management
    
    func startSession() {
        sessionStartTime = Date()
        
        let deviceInfo = [
            "device_model": UIDevice.current.model,
            "ios_version": UIDevice.current.systemVersion,
            "app_version": Bundle.main.appVersion,
            "build_number": Bundle.main.buildNumber,
            "device_id": UIDevice.current.identifierForVendor?.uuidString ?? "unknown"
        ]
        
        trackEvent("session_start", parameters: deviceInfo)
        logger.info("Analytics session started")
    }
    
    func endSession() {
        guard let startTime = sessionStartTime else { return }
        
        let sessionDuration = Date().timeIntervalSince(startTime)
        
        trackEvent("session_end", parameters: [
            "duration_seconds": String(Int(sessionDuration))
        ])
        
        logger.info("Analytics session ended after \(sessionDuration) seconds")
        sessionStartTime = nil
    }
    
    // MARK: - Event Tracking
    
    func trackEvent(_ eventName: String, parameters: [String: String] = [:]) {
        let event = AnalyticsEvent(
            name: eventName,
            parameters: parameters,
            timestamp: Date(),
            sessionId: sessionId
        )
        
        // Log locally for debugging
        logger.info("Event: \(eventName) - \(parameters)")
        
        // In production, send to analytics service
        #if !DEBUG
        sendEventToBackend(event)
        #endif
    }
    
    func trackScreenView(_ screenName: String) {
        trackEvent("screen_view", parameters: [
            "screen_name": screenName
        ])
    }
    
    func trackUserAction(_ action: String, target: String? = nil) {
        var parameters = ["action": action]
        if let target = target {
            parameters["target"] = target
        }
        trackEvent("user_action", parameters: parameters)
    }
    
    func trackPerformance(_ metric: String, value: Double, unit: String = "ms") {
        trackEvent("performance_metric", parameters: [
            "metric": metric,
            "value": String(value),
            "unit": unit
        ])
    }
    
    func trackError(_ error: Error, context: String? = nil) {
        var parameters = [
            "error_description": error.localizedDescription,
            "error_domain": (error as NSError).domain,
            "error_code": String((error as NSError).code)
        ]
        
        if let context = context {
            parameters["context"] = context
        }
        
        trackEvent("error", parameters: parameters)
        logger.error("Error tracked: \(error.localizedDescription)")
    }
    
    // MARK: - Business Events
    
    func trackSubscriptionEvent(_ event: SubscriptionEvent, productId: String? = nil) {
        var parameters = ["event_type": event.rawValue]
        if let productId = productId {
            parameters["product_id"] = productId
        }
        trackEvent("subscription_event", parameters: parameters)
    }
    
    func trackOpportunityViewed(_ opportunity: BettingOpportunity) {
        trackEvent("opportunity_viewed", parameters: [
            "sport": opportunity.sport,
            "ev_percentage": String(format: "%.1f", opportunity.evPct),
            "classification": opportunity.classification.rawValue
        ])
    }
    
    func trackFilterUsage(sport: String?, evThreshold: Double?, searchTerm: String?) {
        var parameters: [String: String] = [:]
        
        if let sport = sport, sport != "All" {
            parameters["sport_filter"] = sport
        }
        
        if let threshold = evThreshold, threshold > 0 {
            parameters["ev_threshold"] = String(format: "%.1f", threshold)
        }
        
        if let search = searchTerm, !search.isEmpty {
            parameters["has_search"] = "true"
        }
        
        trackEvent("filter_applied", parameters: parameters)
    }
    
    func trackWebSocketEvent(_ event: WebSocketEvent, status: String? = nil) {
        var parameters = ["event_type": event.rawValue]
        if let status = status {
            parameters["status"] = status
        }
        trackEvent("websocket_event", parameters: parameters)
    }
    
    // MARK: - Crash Reporting
    
    private func setupCrashReporting() {
        // Set up uncaught exception handler
        NSSetUncaughtExceptionHandler { exception in
            Task { @MainActor in
                AnalyticsService.shared.recordCrash(exception: exception)
            }
        }
        
        // Set up signal handler for crashes
        signal(SIGABRT) { _ in
            Task { @MainActor in
                AnalyticsService.shared.recordCrash(signal: "SIGABRT")
            }
        }
        
        signal(SIGILL) { _ in
            Task { @MainActor in
                AnalyticsService.shared.recordCrash(signal: "SIGILL")
            }
        }
        
        signal(SIGSEGV) { _ in
            Task { @MainActor in
                AnalyticsService.shared.recordCrash(signal: "SIGSEGV")
            }
        }
    }
    
    func recordCrash(exception: NSException? = nil, signal: String? = nil) {
        let crashReport = CrashReport(
            timestamp: Date(),
            appVersion: Bundle.main.appVersion,
            buildNumber: Bundle.main.buildNumber,
            deviceModel: UIDevice.current.model,
            osVersion: UIDevice.current.systemVersion,
            exception: exception?.description,
            signal: signal,
            stackTrace: Thread.callStackSymbols.joined(separator: "\n")
        )
        
        crashReports.append(crashReport)
        saveCrashReport(crashReport)
        
        logger.fault("Crash recorded: \(crashReport.description)")
    }
    
    func sendPendingCrashReports() {
        guard !crashReports.isEmpty else { return }
        
        for report in crashReports {
            sendCrashReportToBackend(report)
        }
        
        crashReports.removeAll()
    }
    
    // MARK: - Private Methods
    
    private var sessionId: String {
        return sessionStartTime?.timeIntervalSince1970.description ?? "unknown"
    }
    
    private func sendEventToBackend(_ event: AnalyticsEvent) {
        // Implementation would send to analytics backend
        // For now, just log for TestFlight debugging
        logger.debug("Would send event to backend: \(event.name)")
    }
    
    private func sendCrashReportToBackend(_ report: CrashReport) {
        // Implementation would send crash report to backend
        logger.fault("Would send crash report to backend: \(report.timestamp)")
    }
    
    private func saveCrashReport(_ report: CrashReport) {
        // Save crash report locally for later transmission
        let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let crashReportPath = documentsPath.appendingPathComponent("crash_\(report.timestamp.timeIntervalSince1970).json")
        
        do {
            let data = try JSONEncoder().encode(report)
            try data.write(to: crashReportPath)
        } catch {
            logger.error("Failed to save crash report: \(error)")
        }
    }
}

// MARK: - Supporting Models

struct AnalyticsEvent: Codable {
    let name: String
    let parameters: [String: String]
    let timestamp: Date
    let sessionId: String
}

struct CrashReport: Codable {
    let timestamp: Date
    let appVersion: String
    let buildNumber: String
    let deviceModel: String
    let osVersion: String
    let exception: String?
    let signal: String?
    let stackTrace: String
    
    var description: String {
        return "Crash at \(timestamp): \(exception ?? signal ?? "Unknown")"
    }
}

enum SubscriptionEvent: String, CaseIterable {
    case started = "subscription_started"
    case completed = "subscription_completed"
    case cancelled = "subscription_cancelled"
    case restored = "subscription_restored"
    case failed = "subscription_failed"
    case expired = "subscription_expired"
}

enum WebSocketEvent: String, CaseIterable {
    case connected = "websocket_connected"
    case disconnected = "websocket_disconnected"
    case reconnecting = "websocket_reconnecting"
    case messageReceived = "websocket_message_received"
    case error = "websocket_error"
}

// MARK: - Bundle Extensions

extension Bundle {
    var appVersion: String {
        return infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
    }
    
    var buildNumber: String {
        return infoDictionary?["CFBundleVersion"] as? String ?? "1"
    }
    
    var fullVersion: String {
        return "\(appVersion) (\(buildNumber))"
    }
}