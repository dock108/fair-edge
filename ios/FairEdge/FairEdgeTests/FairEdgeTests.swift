//
//  FairEdgeTests.swift
//  FairEdgeTests
//
//  Unit tests for Fair-Edge iOS application
//  Comprehensive testing of core functionality and business logic

import XCTest
import Combine
@testable import FairEdge

class FairEdgeTests: XCTestCase {
    
    // MARK: - Properties
    
    var cancellables: Set<AnyCancellable>!
    
    // MARK: - Setup & Teardown
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        cancellables = Set<AnyCancellable>()
    }
    
    override func tearDownWithError() throws {
        cancellables.removeAll()
        cancellables = nil
        try super.tearDownWithError()
    }
    
    // MARK: - App Lifecycle Tests
    
    func testAppInitialization() throws {
        // Test that the app initializes without crashing
        let app = FairEdgeApp()
        XCTAssertNotNil(app)
    }
    
    func testAppDelegateInitialization() throws {
        // Test AppDelegate initialization
        let appDelegate = AppDelegate()
        XCTAssertNotNil(appDelegate)
        XCTAssertNil(appDelegate.pushNotificationService)
    }
    
    // MARK: - Performance Tests
    
    func testAppStartupPerformance() throws {
        // Measure app startup time
        measure {
            _ = FairEdgeApp()
        }
    }
    
    func testMemoryUsage() throws {
        // Test that app doesn't leak memory during initialization
        weak var weakApp: FairEdgeApp?
        
        autoreleasepool {
            let app = FairEdgeApp()
            weakApp = app
        }
        
        // App should be deallocated
        XCTAssertNil(weakApp, "FairEdgeApp should be deallocated")
    }
}

// MARK: - Test Utilities

extension FairEdgeTests {
    
    /// Create a mock user for testing
    func createMockUser() -> User {
        return User(
            id: "test_user_123",
            email: "test@fair-edge.com",
            role: .premium,
            subscriptionStatus: .active,
            deviceId: "test_device_123"
        )
    }
    
    /// Create mock betting opportunity
    func createMockOpportunity() -> BettingOpportunity {
        return BettingOpportunity(
            id: "test_opp_123",
            event: "Lakers vs Warriors",
            betDescription: "LeBron Points Over 25.5",
            betType: .playerProps,
            sport: "NBA",
            evPercentage: 12.5,
            bestOdds: "+150",
            fairOdds: "+120",
            bestSource: "DraftKings",
            gameTime: Date().addingTimeInterval(3600),
            classification: .great
        )
    }
    
    /// Wait for async expectation with timeout
    func waitForExpectation(_ expectation: XCTestExpectation, timeout: TimeInterval = 5.0) {
        wait(for: [expectation], timeout: timeout)
    }
}