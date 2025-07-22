//
//  AnalyticsServiceTests.swift
//  FairEdgeTests
//
//  Unit tests for AnalyticsService
//  Tests event tracking, crash reporting, and performance monitoring

import XCTest
import Combine
@testable import FairEdge

class AnalyticsServiceTests: XCTestCase {

    // MARK: - Properties

    var analyticsService: AnalyticsService!
    var mockEventStore: MockEventStore!
    var mockCrashReporter: MockCrashReporter!
    var mockNetworkClient: MockNetworkClient!
    var cancellables: Set<AnyCancellable>!

    // MARK: - Setup & Teardown

    override func setUpWithError() throws {
        try super.setUpWithError()

        mockEventStore = MockEventStore()
        mockCrashReporter = MockCrashReporter()
        mockNetworkClient = MockNetworkClient()

        analyticsService = AnalyticsService(
            eventStore: mockEventStore,
            crashReporter: mockCrashReporter,
            networkClient: mockNetworkClient
        )
        cancellables = Set<AnyCancellable>()
    }

    override func tearDownWithError() throws {
        analyticsService = nil
        mockEventStore = nil
        mockCrashReporter = nil
        mockNetworkClient = nil
        cancellables.removeAll()
        cancellables = nil
        try super.tearDownWithError()
    }

    // MARK: - Event Tracking Tests

    func testTrackEvent_SimpleEvent() throws {
        // Given: Simple event data
        let eventName = "app_launched"

        // When: Tracking event
        analyticsService.trackEvent(eventName)

        // Then: Should store event
        XCTAssertTrue(mockEventStore.storeEventCalled)
        XCTAssertEqual(mockEventStore.lastStoredEvent?.name, eventName)
        XCTAssertNotNil(mockEventStore.lastStoredEvent?.timestamp)
    }

    func testTrackEvent_EventWithProperties() throws {
        // Given: Event with properties
        let eventName = "opportunity_viewed"
        let properties: [String: Any] = [
            "opportunity_id": "test_opp_123",
            "sport": "NBA",
            "ev_percentage": 12.5,
            "user_role": "premium"
        ]

        // When: Tracking event with properties
        analyticsService.trackEvent(eventName, properties: properties)

        // Then: Should store event with properties
        XCTAssertTrue(mockEventStore.storeEventCalled)
        XCTAssertEqual(mockEventStore.lastStoredEvent?.name, eventName)
        XCTAssertEqual(mockEventStore.lastStoredEvent?.properties?["opportunity_id"] as? String, "test_opp_123")
        XCTAssertEqual(mockEventStore.lastStoredEvent?.properties?["ev_percentage"] as? Double, 12.5)
    }

    func testTrackEvent_UserInteraction() throws {
        // Given: User interaction event
        let eventName = "button_tapped"
        let properties: [String: Any] = [
            "button_name": "subscribe_premium",
            "screen": "paywall",
            "user_type": "free"
        ]

        // When: Tracking user interaction
        analyticsService.trackUserInteraction(eventName, properties: properties)

        // Then: Should store with interaction category
        XCTAssertTrue(mockEventStore.storeEventCalled)
        XCTAssertEqual(mockEventStore.lastStoredEvent?.category, .userInteraction)
        XCTAssertEqual(mockEventStore.lastStoredEvent?.properties?["button_name"] as? String, "subscribe_premium")
    }

    func testTrackEvent_PerformanceMetric() throws {
        // Given: Performance metric
        let duration: TimeInterval = 1.25
        let properties: [String: Any] = [
            "operation": "api_request",
            "endpoint": "/api/opportunities",
            "duration_ms": duration * 1000
        ]

        // When: Tracking performance
        analyticsService.trackPerformance("api_response_time", duration: duration, properties: properties)

        // Then: Should store performance event
        XCTAssertTrue(mockEventStore.storeEventCalled)
        XCTAssertEqual(mockEventStore.lastStoredEvent?.category, .performance)
        XCTAssertEqual(mockEventStore.lastStoredEvent?.properties?["duration_ms"] as? Double, 1250.0)
    }

    func testTrackEvent_BusinessMetric() throws {
        // Given: Business metric event
        let eventName = "subscription_purchased"
        let properties: [String: Any] = [
            "product_id": "com.fairedge.premium.monthly",
            "price": 9.99,
            "currency": "USD",
            "trial_period": false
        ]

        // When: Tracking business metric
        analyticsService.trackBusinessEvent(eventName, properties: properties)

        // Then: Should store business event
        XCTAssertTrue(mockEventStore.storeEventCalled)
        XCTAssertEqual(mockEventStore.lastStoredEvent?.category, .business)
        XCTAssertEqual(mockEventStore.lastStoredEvent?.properties?["product_id"] as? String, "com.fairedge.premium.monthly")
    }

    // MARK: - Event Batching Tests

    func testEventBatching_AutomaticUpload() throws {
        // Given: Multiple events approaching batch threshold
        analyticsService.batchSize = 5

        let expectation = XCTestExpectation(description: "Batch uploaded")

        // When: Adding events to trigger batch upload
        for i in 0..<5 {
            analyticsService.trackEvent("test_event_\(i)")
        }

        // Then: Should trigger automatic upload
        mockNetworkClient.onUploadCalled = {
            expectation.fulfill()
        }

        wait(for: [expectation], timeout: 5.0)
        XCTAssertTrue(mockNetworkClient.uploadEventsCalled)
    }

    func testEventBatching_ManualUpload() async throws {
        // Given: Events stored locally
        for i in 0..<3 {
            analyticsService.trackEvent("test_event_\(i)")
        }

        mockNetworkClient.shouldUploadSucceed = true

        // When: Manually uploading events
        await analyticsService.uploadPendingEvents()

        // Then: Should upload stored events
        XCTAssertTrue(mockNetworkClient.uploadEventsCalled)
        XCTAssertEqual(mockNetworkClient.lastUploadedEvents?.count, 3)
    }

    func testEventBatching_UploadFailure() async throws {
        // Given: Network failure during upload
        analyticsService.trackEvent("test_event")
        mockNetworkClient.shouldUploadSucceed = false

        // When: Attempting to upload
        await analyticsService.uploadPendingEvents()

        // Then: Should handle failure and retry later
        XCTAssertTrue(mockNetworkClient.uploadEventsCalled)
        XCTAssertEqual(analyticsService.pendingEventsCount, 1) // Event should remain in queue
    }

    func testEventBatching_RetryLogic() async throws {
        // Given: Failed upload with retry enabled
        analyticsService.trackEvent("test_event")
        mockNetworkClient.shouldUploadSucceed = false
        analyticsService.maxRetryAttempts = 3

        // When: Upload fails and retries
        await analyticsService.uploadPendingEvents()

        // Then: Should implement retry logic
        XCTAssertTrue(analyticsService.retryAttempts > 0)
        XCTAssertTrue(analyticsService.retryAttempts <= 3)
    }

    // MARK: - User Properties Tests

    func testSetUserProperty() throws {
        // Given: User property
        let propertyName = "user_role"
        let propertyValue = "premium"

        // When: Setting user property
        analyticsService.setUserProperty(propertyName, value: propertyValue)

        // Then: Should store user property
        XCTAssertEqual(analyticsService.userProperties[propertyName] as? String, propertyValue)
    }

    func testSetUserID() throws {
        // Given: User ID
        let userID = "user_12345"

        // When: Setting user ID
        analyticsService.setUserID(userID)

        // Then: Should store user ID
        XCTAssertEqual(analyticsService.currentUserID, userID)
    }

    func testUserPropertiesIncludedInEvents() throws {
        // Given: User properties set
        analyticsService.setUserID("user_12345")
        analyticsService.setUserProperty("role", value: "premium")
        analyticsService.setUserProperty("subscription_status", value: "active")

        // When: Tracking an event
        analyticsService.trackEvent("test_event")

        // Then: User properties should be included
        let storedEvent = mockEventStore.lastStoredEvent
        XCTAssertEqual(storedEvent?.userID, "user_12345")
        XCTAssertEqual(storedEvent?.userProperties?["role"] as? String, "premium")
        XCTAssertEqual(storedEvent?.userProperties?["subscription_status"] as? String, "active")
    }

    func testClearUserData() throws {
        // Given: User data set
        analyticsService.setUserID("user_12345")
        analyticsService.setUserProperty("role", value: "premium")

        // When: Clearing user data
        analyticsService.clearUserData()

        // Then: Should clear all user data
        XCTAssertNil(analyticsService.currentUserID)
        XCTAssertTrue(analyticsService.userProperties.isEmpty)
    }

    // MARK: - Screen Tracking Tests

    func testTrackScreen() throws {
        // Given: Screen view
        let screenName = "opportunities_list"
        let properties: [String: Any] = [
            "filter_applied": "NFL",
            "sort_order": "ev_desc",
            "user_role": "premium"
        ]

        // When: Tracking screen view
        analyticsService.trackScreen(screenName, properties: properties)

        // Then: Should store screen view event
        XCTAssertTrue(mockEventStore.storeEventCalled)
        XCTAssertEqual(mockEventStore.lastStoredEvent?.name, "screen_view")
        XCTAssertEqual(mockEventStore.lastStoredEvent?.category, .navigation)
        XCTAssertEqual(mockEventStore.lastStoredEvent?.properties?["screen_name"] as? String, screenName)
    }

    func testTrackScreenTime() throws {
        // Given: Screen time measurement
        let screenName = "opportunities_list"
        let timeSpent: TimeInterval = 45.7

        // When: Tracking screen time
        analyticsService.trackScreenTime(screenName, timeSpent: timeSpent)

        // Then: Should store screen time event
        XCTAssertTrue(mockEventStore.storeEventCalled)
        XCTAssertEqual(mockEventStore.lastStoredEvent?.name, "screen_time")
        XCTAssertEqual(mockEventStore.lastStoredEvent?.properties?["screen_name"] as? String, screenName)
        XCTAssertEqual(mockEventStore.lastStoredEvent?.properties?["time_spent"] as? TimeInterval, timeSpent)
    }

    // MARK: - Crash Reporting Tests

    func testCrashReporting_Enabled() throws {
        // Given: Crash reporting enabled
        analyticsService.enableCrashReporting()

        // When: Crash occurs
        let crashInfo = CrashInfo(
            type: "NSException",
            message: "Test crash",
            stackTrace: ["line1", "line2", "line3"],
            timestamp: Date()
        )

        analyticsService.reportCrash(crashInfo)

        // Then: Should report crash
        XCTAssertTrue(mockCrashReporter.reportCrashCalled)
        XCTAssertEqual(mockCrashReporter.lastCrashInfo?.message, "Test crash")
    }

    func testCrashReporting_Disabled() throws {
        // Given: Crash reporting disabled
        analyticsService.disableCrashReporting()

        // When: Crash occurs
        let crashInfo = CrashInfo(
            type: "NSException",
            message: "Test crash",
            stackTrace: ["line1", "line2"],
            timestamp: Date()
        )

        analyticsService.reportCrash(crashInfo)

        // Then: Should not report crash
        XCTAssertFalse(mockCrashReporter.reportCrashCalled)
    }

    func testSendPendingCrashReports() async throws {
        // Given: Pending crash reports
        mockCrashReporter.hasPendingReports = true
        mockNetworkClient.shouldUploadSucceed = true

        // When: Sending pending reports
        await analyticsService.sendPendingCrashReports()

        // Then: Should send reports
        XCTAssertTrue(mockCrashReporter.sendPendingReportsCalled)
    }

    // MARK: - Privacy Tests

    func testPrivacyMode_OptOut() throws {
        // Given: User opts out of analytics
        analyticsService.setAnalyticsEnabled(false)

        // When: Tracking event
        analyticsService.trackEvent("test_event")

        // Then: Should not store event
        XCTAssertFalse(mockEventStore.storeEventCalled)
    }

    func testPrivacyMode_OptIn() throws {
        // Given: User opts into analytics
        analyticsService.setAnalyticsEnabled(true)

        // When: Tracking event
        analyticsService.trackEvent("test_event")

        // Then: Should store event
        XCTAssertTrue(mockEventStore.storeEventCalled)
    }

    func testDataRetention() throws {
        // Given: Old events stored
        let oldDate = Date().addingTimeInterval(-60 * 60 * 24 * 30) // 30 days ago
        mockEventStore.oldestEventDate = oldDate
        analyticsService.dataRetentionDays = 7

        // When: Performing cleanup
        analyticsService.cleanupOldEvents()

        // Then: Should remove old events
        XCTAssertTrue(mockEventStore.removeOldEventsCalled)
    }

    func testPII_Scrubbing() throws {
        // Given: Event with potential PII
        let properties: [String: Any] = [
            "email": "user@example.com",
            "phone": "+1234567890",
            "safe_property": "safe_value",
            "device_id": "device_123"
        ]

        // When: Tracking event
        analyticsService.trackEvent("test_event", properties: properties)

        // Then: Should scrub PII
        let storedEvent = mockEventStore.lastStoredEvent
        XCTAssertNil(storedEvent?.properties?["email"])
        XCTAssertNil(storedEvent?.properties?["phone"])
        XCTAssertNotNil(storedEvent?.properties?["safe_property"])
        XCTAssertNotNil(storedEvent?.properties?["device_id"]) // Device ID is okay
    }

    // MARK: - Session Tracking Tests

    func testSessionStart() throws {
        // Given: App launches

        // When: Starting session
        analyticsService.startSession()

        // Then: Should track session start
        XCTAssertTrue(mockEventStore.storeEventCalled)
        XCTAssertEqual(mockEventStore.lastStoredEvent?.name, "session_start")
        XCTAssertNotNil(analyticsService.currentSessionID)
    }

    func testSessionEnd() throws {
        // Given: Active session
        analyticsService.startSession()
        let sessionStart = Date()

        // When: Ending session
        analyticsService.endSession()

        // Then: Should track session end with duration
        XCTAssertTrue(mockEventStore.storeEventCalled)
        XCTAssertEqual(mockEventStore.lastStoredEvent?.name, "session_end")
        XCTAssertNotNil(mockEventStore.lastStoredEvent?.properties?["session_duration"])
    }

    func testSessionTimeout() throws {
        // Given: Session with timeout
        analyticsService.sessionTimeoutInterval = 5.0 // 5 seconds
        analyticsService.startSession()

        let expectation = XCTestExpectation(description: "Session timeout")

        // When: Session times out
        DispatchQueue.main.asyncAfter(deadline: .now() + 6) {
            // Trigger background/foreground to check timeout
            self.analyticsService.handleAppDidEnterBackground()
            self.analyticsService.handleAppDidBecomeActive()
            expectation.fulfill()
        }

        wait(for: [expectation], timeout: 10.0)

        // Then: Should start new session
        XCTAssertNotEqual(analyticsService.currentSessionID, analyticsService.previousSessionID)
    }

    // MARK: - Device Info Tests

    func testDeviceInfoCollection() throws {
        // When: Getting device info
        let deviceInfo = analyticsService.getDeviceInfo()

        // Then: Should collect device information
        XCTAssertNotNil(deviceInfo["device_model"])
        XCTAssertNotNil(deviceInfo["os_version"])
        XCTAssertNotNil(deviceInfo["app_version"])
        XCTAssertNotNil(deviceInfo["bundle_id"])
        XCTAssertNotNil(deviceInfo["locale"])
        XCTAssertNotNil(deviceInfo["timezone"])
    }

    func testDeviceInfoIncludedInEvents() throws {
        // When: Tracking event
        analyticsService.trackEvent("test_event")

        // Then: Device info should be included
        let storedEvent = mockEventStore.lastStoredEvent
        XCTAssertNotNil(storedEvent?.deviceInfo)
        XCTAssertNotNil(storedEvent?.deviceInfo?["device_model"])
        XCTAssertNotNil(storedEvent?.deviceInfo?["os_version"])
    }

    // MARK: - Performance Tests

    func testEventTrackingPerformance() throws {
        // Given: Large number of events
        let eventCount = 1000

        // When: Tracking many events
        measure {
            for i in 0..<eventCount {
                analyticsService.trackEvent("performance_test_\(i)", properties: [
                    "index": i,
                    "timestamp": Date().timeIntervalSince1970
                ])
            }
        }
    }

    func testEventSerializationPerformance() throws {
        // Given: Complex event with large properties
        let largeProperties = Dictionary(uniqueKeysWithValues:
            Array(0..<100).map { ("key_\($0)", "value_\($0)_with_longer_string") }
        )

        // When: Tracking events with large properties
        measure {
            for _ in 0..<100 {
                analyticsService.trackEvent("complex_event", properties: largeProperties)
            }
        }
    }
}

// MARK: - Test Utilities

extension AnalyticsServiceTests {

    func createMockEvent(name: String) -> AnalyticsEvent {
        return AnalyticsEvent(
            name: name,
            properties: ["test": "value"],
            timestamp: Date(),
            category: .userInteraction
        )
    }
}

// MARK: - Mock Classes

class MockEventStore {
    var storeEventCalled = false
    var removeOldEventsCalled = false
    var lastStoredEvent: AnalyticsEvent?
    var oldestEventDate: Date?

    func storeEvent(_ event: AnalyticsEvent) {
        storeEventCalled = true
        lastStoredEvent = event
    }

    func removeOldEvents(olderThan date: Date) {
        removeOldEventsCalled = true
    }

    func getAllEvents() -> [AnalyticsEvent] {
        return []
    }

    func clearAllEvents() {
        // Mock implementation
    }
}

class MockCrashReporter {
    var reportCrashCalled = false
    var sendPendingReportsCalled = false
    var lastCrashInfo: CrashInfo?
    var hasPendingReports = false

    func reportCrash(_ crashInfo: CrashInfo) {
        reportCrashCalled = true
        lastCrashInfo = crashInfo
    }

    func sendPendingReports() async {
        sendPendingReportsCalled = true
    }

    func getPendingReports() -> [CrashInfo] {
        return hasPendingReports ? [CrashInfo(type: "Test", message: "Test", stackTrace: [], timestamp: Date())] : []
    }
}

class MockNetworkClient {
    var uploadEventsCalled = false
    var shouldUploadSucceed = true
    var lastUploadedEvents: [AnalyticsEvent]?
    var onUploadCalled: (() -> Void)?

    func uploadEvents(_ events: [AnalyticsEvent]) async throws {
        uploadEventsCalled = true
        lastUploadedEvents = events
        onUploadCalled?()

        if !shouldUploadSucceed {
            throw NetworkError.uploadFailed
        }
    }
}

// MARK: - Data Models

struct AnalyticsEvent {
    let id: String = UUID().uuidString
    let name: String
    let properties: [String: Any]?
    let timestamp: Date
    let category: EventCategory
    var userID: String?
    var userProperties: [String: Any]?
    var deviceInfo: [String: Any]?
}

enum EventCategory {
    case userInteraction
    case navigation
    case performance
    case business
    case system
}

struct CrashInfo {
    let type: String
    let message: String
    let stackTrace: [String]
    let timestamp: Date
}

enum NetworkError: Error {
    case uploadFailed
    case noConnection
    case serverError
}
