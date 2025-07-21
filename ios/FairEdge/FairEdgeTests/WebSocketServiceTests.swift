//
//  WebSocketServiceTests.swift
//  FairEdgeTests
//
//  Unit tests for WebSocketService
//  Tests real-time connection, message handling, and connection management

import XCTest
import Combine
import Network
@testable import FairEdge

class WebSocketServiceTests: XCTestCase {

    // MARK: - Properties

    var webSocketService: WebSocketService!
    var mockWebSocketTask: MockURLSessionWebSocketTask!
    var mockAuthService: MockAuthenticationService!
    var mockAPIService: MockAPIService!
    var cancellables: Set<AnyCancellable>!

    // MARK: - Setup & Teardown

    override func setUpWithError() throws {
        try super.setUpWithError()

        mockWebSocketTask = MockURLSessionWebSocketTask()
        mockAuthService = MockAuthenticationService()
        mockAPIService = MockAPIService()

        webSocketService = WebSocketService(
            authenticationService: mockAuthService,
            apiService: mockAPIService,
            webSocketTask: mockWebSocketTask
        )
        cancellables = Set<AnyCancellable>()
    }

    override func tearDownWithError() throws {
        webSocketService = nil
        mockWebSocketTask = nil
        mockAuthService = nil
        mockAPIService = nil
        cancellables.removeAll()
        cancellables = nil
        try super.tearDownWithError()
    }

    // MARK: - Connection Tests

    func testConnect_Success() throws {
        // Given: Authenticated user
        mockAuthService.isAuthenticated = true
        mockAuthService.mockAccessToken = "valid_token"
        mockWebSocketTask.shouldConnectSucceed = true

        let expectation = XCTestExpectation(description: "Connection succeeds")

        // When: Connecting to WebSocket
        webSocketService.connect()

        // Then: Should establish connection
        webSocketService.$connectionState
            .dropFirst()
            .sink { state in
                if state == .connected {
                    XCTAssertTrue(self.mockWebSocketTask.resumeCalled)
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)

        wait(for: [expectation], timeout: 5.0)
    }

    func testConnect_NotAuthenticated() throws {
        // Given: User not authenticated
        mockAuthService.isAuthenticated = false

        // When: Attempting to connect
        webSocketService.connect()

        // Then: Should not attempt connection
        XCTAssertFalse(mockWebSocketTask.resumeCalled)
        XCTAssertEqual(webSocketService.connectionState, .disconnected)
    }

    func testConnect_ConnectionFailure() throws {
        // Given: Connection failure
        mockAuthService.isAuthenticated = true
        mockWebSocketTask.shouldConnectSucceed = false
        mockWebSocketTask.mockError = WebSocketError.connectionFailed

        let expectation = XCTestExpectation(description: "Connection fails")

        // When: Attempting to connect
        webSocketService.connect()

        // Then: Should handle failure and retry
        webSocketService.$connectionState
            .dropFirst()
            .sink { state in
                if state == .failed {
                    XCTAssertNotNil(self.webSocketService.lastError)
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)

        wait(for: [expectation], timeout: 5.0)
    }

    func testDisconnect_Success() throws {
        // Given: Connected WebSocket
        webSocketService.connectionState = .connected

        let expectation = XCTestExpectation(description: "Disconnection succeeds")

        // When: Disconnecting
        webSocketService.disconnect()

        // Then: Should close connection
        webSocketService.$connectionState
            .dropFirst()
            .sink { state in
                if state == .disconnected {
                    XCTAssertTrue(self.mockWebSocketTask.cancelCalled)
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)

        wait(for: [expectation], timeout: 5.0)
    }

    // MARK: - Authentication Tests

    func testAuthenticationIntegration_UserSignsIn() throws {
        // Given: User signs in after WebSocket is initialized
        mockAuthService.isAuthenticated = false

        let expectation = XCTestExpectation(description: "Auto-connect on sign in")

        // When: User signs in
        mockAuthService.isAuthenticated = true
        mockAuthService.triggerAuthenticationChange()

        // Then: Should automatically connect
        webSocketService.$connectionState
            .dropFirst()
            .sink { state in
                if state == .connecting {
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)

        wait(for: [expectation], timeout: 5.0)
    }

    func testAuthenticationIntegration_UserSignsOut() throws {
        // Given: Connected user signs out
        webSocketService.connectionState = .connected
        mockAuthService.isAuthenticated = true

        let expectation = XCTestExpectation(description: "Auto-disconnect on sign out")

        // When: User signs out
        mockAuthService.isAuthenticated = false
        mockAuthService.triggerAuthenticationChange()

        // Then: Should automatically disconnect
        webSocketService.$connectionState
            .dropFirst()
            .sink { state in
                if state == .disconnected {
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)

        wait(for: [expectation], timeout: 5.0)
    }

    func testTokenRefresh_ReconnectWithNewToken() throws {
        // Given: Connected with old token
        webSocketService.connectionState = .connected
        mockAuthService.mockAccessToken = "old_token"

        let expectation = XCTestExpectation(description: "Reconnect with new token")

        // When: Token is refreshed
        mockAuthService.mockAccessToken = "new_token"
        mockAuthService.triggerTokenRefresh()

        // Then: Should reconnect with new token
        webSocketService.$connectionState
            .dropFirst()
            .sink { state in
                if state == .connecting {
                    // Verify new token is used
                    XCTAssertTrue(self.mockWebSocketTask.cancelCalled)
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)

        wait(for: [expectation], timeout: 5.0)
    }

    // MARK: - Message Sending Tests

    func testSendMessage_Success() async throws {
        // Given: Connected WebSocket
        webSocketService.connectionState = .connected
        mockWebSocketTask.shouldSendSucceed = true

        let message = WebSocketMessage.subscribe(channel: "opportunities")

        // When: Sending message
        await webSocketService.sendMessage(message)

        // Then: Should send successfully
        XCTAssertTrue(mockWebSocketTask.sendCalled)
        XCTAssertNil(webSocketService.lastError)
    }

    func testSendMessage_NotConnected() async throws {
        // Given: Not connected
        webSocketService.connectionState = .disconnected

        let message = WebSocketMessage.subscribe(channel: "opportunities")

        // When: Attempting to send message
        await webSocketService.sendMessage(message)

        // Then: Should handle gracefully
        XCTAssertFalse(mockWebSocketTask.sendCalled)
        XCTAssertNotNil(webSocketService.lastError)
    }

    func testSendMessage_SendFailure() async throws {
        // Given: Connected but send fails
        webSocketService.connectionState = .connected
        mockWebSocketTask.shouldSendSucceed = false
        mockWebSocketTask.mockError = WebSocketError.sendFailed

        let message = WebSocketMessage.subscribe(channel: "opportunities")

        // When: Sending message
        await webSocketService.sendMessage(message)

        // Then: Should handle send failure
        XCTAssertTrue(mockWebSocketTask.sendCalled)
        XCTAssertNotNil(webSocketService.lastError)
    }

    func testSubscribeToChannel_Success() async throws {
        // Given: Connected WebSocket
        webSocketService.connectionState = .connected
        mockWebSocketTask.shouldSendSucceed = true

        // When: Subscribing to channel
        await webSocketService.subscribeToChannel("opportunities")

        // Then: Should send subscription message
        XCTAssertTrue(mockWebSocketTask.sendCalled)
        XCTAssertTrue(webSocketService.subscribedChannels.contains("opportunities"))
    }

    func testUnsubscribeFromChannel_Success() async throws {
        // Given: Subscribed to channel
        webSocketService.connectionState = .connected
        webSocketService.subscribedChannels.insert("opportunities")
        mockWebSocketTask.shouldSendSucceed = true

        // When: Unsubscribing from channel
        await webSocketService.unsubscribeFromChannel("opportunities")

        // Then: Should send unsubscription message
        XCTAssertTrue(mockWebSocketTask.sendCalled)
        XCTAssertFalse(webSocketService.subscribedChannels.contains("opportunities"))
    }

    // MARK: - Message Receiving Tests

    func testReceiveMessage_OpportunityUpdate() throws {
        // Given: Connected and subscribed to opportunities
        webSocketService.connectionState = .connected
        webSocketService.subscribedChannels.insert("opportunities")

        let opportunityData: [String: Any] = [
            "type": "opportunity_update",
            "channel": "opportunities",
            "data": [
                "id": "test_opp_123",
                "event": "Lakers vs Warriors",
                "ev_percentage": 12.5,
                "best_odds": "+150",
                "sport": "NBA"
            ]
        ]

        let jsonData = try JSONSerialization.data(withJSONObject: opportunityData)
        let message = URLSessionWebSocketTask.Message.data(jsonData)

        let expectation = XCTestExpectation(description: "Opportunity update received")

        // When: Receiving opportunity update
        mockWebSocketTask.simulateReceivedMessage(message)

        // Then: Should parse and handle update
        webSocketService.$lastReceivedMessage
            .compactMap { $0 }
            .sink { receivedMessage in
                if case .opportunityUpdate(let opportunity) = receivedMessage {
                    XCTAssertEqual(opportunity.id, "test_opp_123")
                    XCTAssertEqual(opportunity.evPercentage, 12.5)
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)

        wait(for: [expectation], timeout: 5.0)
    }

    func testReceiveMessage_UserUpdate() throws {
        // Given: Connected WebSocket
        webSocketService.connectionState = .connected

        let userUpdateData: [String: Any] = [
            "type": "user_update",
            "data": [
                "subscription_status": "active",
                "role": "premium",
                "expires_date": "2025-02-20T12:00:00Z"
            ]
        ]

        let jsonData = try JSONSerialization.data(withJSONObject: userUpdateData)
        let message = URLSessionWebSocketTask.Message.data(jsonData)

        let expectation = XCTestExpectation(description: "User update received")

        // When: Receiving user update
        mockWebSocketTask.simulateReceivedMessage(message)

        // Then: Should parse and handle update
        webSocketService.$lastReceivedMessage
            .compactMap { $0 }
            .sink { receivedMessage in
                if case .userUpdate(let userInfo) = receivedMessage {
                    XCTAssertEqual(userInfo["subscription_status"] as? String, "active")
                    XCTAssertEqual(userInfo["role"] as? String, "premium")
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)

        wait(for: [expectation], timeout: 5.0)
    }

    func testReceiveMessage_PingPong() throws {
        // Given: Connected WebSocket
        webSocketService.connectionState = .connected

        let pingMessage = URLSessionWebSocketTask.Message.string("ping")

        // When: Receiving ping message
        mockWebSocketTask.simulateReceivedMessage(pingMessage)

        // Then: Should respond with pong
        XCTAssertTrue(mockWebSocketTask.sendCalled)
        // Verify pong was sent
        XCTAssertEqual(mockWebSocketTask.lastSentMessage, "pong")
    }

    func testReceiveMessage_InvalidJSON() throws {
        // Given: Connected WebSocket
        webSocketService.connectionState = .connected

        let invalidMessage = URLSessionWebSocketTask.Message.data("invalid json".data(using: .utf8)!)

        // When: Receiving invalid JSON
        mockWebSocketTask.simulateReceivedMessage(invalidMessage)

        // Then: Should handle gracefully
        XCTAssertNotNil(webSocketService.lastError)
    }

    // MARK: - Connection Management Tests

    func testAutoReconnect_OnConnectionLoss() throws {
        // Given: Connected WebSocket that loses connection
        webSocketService.connectionState = .connected
        webSocketService.shouldAutoReconnect = true

        let expectation = XCTestExpectation(description: "Auto-reconnect triggered")

        // When: Connection is lost
        mockWebSocketTask.simulateConnectionLoss()

        // Then: Should attempt to reconnect
        webSocketService.$connectionState
            .dropFirst()
            .sink { state in
                if state == .connecting {
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)

        wait(for: [expectation], timeout: 5.0)
    }

    func testAutoReconnect_Disabled() throws {
        // Given: Auto-reconnect disabled
        webSocketService.connectionState = .connected
        webSocketService.shouldAutoReconnect = false

        // When: Connection is lost
        mockWebSocketTask.simulateConnectionLoss()

        // Then: Should not attempt to reconnect
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            XCTAssertEqual(self.webSocketService.connectionState, .failed)
        }
    }

    func testReconnectWithBackoff() throws {
        // Given: Multiple connection failures
        mockWebSocketTask.shouldConnectSucceed = false
        mockAuthService.isAuthenticated = true

        // When: Attempting multiple reconnections
        webSocketService.connect()
        webSocketService.connect()
        webSocketService.connect()

        // Then: Should implement exponential backoff
        XCTAssertTrue(webSocketService.reconnectDelay > 1.0)
        XCTAssertTrue(webSocketService.reconnectAttempts > 0)
    }

    func testMaxReconnectAttempts() throws {
        // Given: Persistent connection failures
        mockWebSocketTask.shouldConnectSucceed = false
        mockAuthService.isAuthenticated = true
        webSocketService.maxReconnectAttempts = 3

        let expectation = XCTestExpectation(description: "Max reconnect attempts reached")

        // When: Exceeding max reconnect attempts
        for _ in 0..<5 {
            webSocketService.connect()
        }

        // Then: Should stop attempting after max attempts
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            XCTAssertEqual(self.webSocketService.reconnectAttempts, 3)
            XCTAssertEqual(self.webSocketService.connectionState, .failed)
            expectation.fulfill()
        }

        wait(for: [expectation], timeout: 5.0)
    }

    // MARK: - Network Monitoring Tests

    func testNetworkMonitoring_WifiToMobile() throws {
        // Given: Connected on WiFi
        webSocketService.connectionState = .connected

        let expectation = XCTestExpectation(description: "Network change handled")

        // When: Network changes to mobile
        webSocketService.handleNetworkChange(from: .wifi, to: .cellular)

        // Then: Should maintain connection or reconnect if needed
        webSocketService.$connectionState
            .dropFirst()
            .sink { state in
                // Should either stay connected or reconnect
                XCTAssertTrue(state == .connected || state == .connecting)
                expectation.fulfill()
            }
            .store(in: &cancellables)

        wait(for: [expectation], timeout: 5.0)
    }

    func testNetworkMonitoring_NoConnection() throws {
        // Given: Connected WebSocket
        webSocketService.connectionState = .connected

        let expectation = XCTestExpectation(description: "No network handled")

        // When: Network becomes unavailable
        webSocketService.handleNetworkChange(from: .wifi, to: .none)

        // Then: Should disconnect gracefully
        webSocketService.$connectionState
            .dropFirst()
            .sink { state in
                if state == .disconnected {
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)

        wait(for: [expectation], timeout: 5.0)
    }

    // MARK: - Performance Tests

    func testMessageProcessingPerformance() throws {
        // Given: Large number of messages
        let messages = Array(0..<1000).map { index in
            let data: [String: Any] = [
                "type": "opportunity_update",
                "data": ["id": "opp_\(index)", "ev_percentage": Double(index % 20)]
            ]
            let jsonData = try! JSONSerialization.data(withJSONObject: data)
            return URLSessionWebSocketTask.Message.data(jsonData)
        }

        webSocketService.connectionState = .connected

        // When: Processing messages
        measure {
            for message in messages {
                mockWebSocketTask.simulateReceivedMessage(message)
            }
        }
    }

    func testConnectionPerformance() throws {
        // Given: Multiple connection attempts
        mockAuthService.isAuthenticated = true
        mockWebSocketTask.shouldConnectSucceed = true

        // When: Measuring connection time
        measure {
            webSocketService.connect()
            webSocketService.disconnect()
        }
    }
}

// MARK: - Test Utilities

extension WebSocketServiceTests {

    func createMockOpportunity() -> [String: Any] {
        return [
            "id": "test_opp_123",
            "event": "Lakers vs Warriors",
            "bet_description": "LeBron Points Over 25.5",
            "ev_percentage": 12.5,
            "best_odds": "+150",
            "sport": "NBA"
        ]
    }
}

// MARK: - Mock Classes

class MockURLSessionWebSocketTask: URLSessionWebSocketTask {
    var shouldConnectSucceed = true
    var shouldSendSucceed = true
    var mockError: Error?

    var resumeCalled = false
    var cancelCalled = false
    var sendCalled = false
    var lastSentMessage: String?

    private var messageHandler: ((URLSessionWebSocketTask.Message) -> Void)?
    private var connectionHandler: (() -> Void)?

    override func resume() {
        resumeCalled = true
        if shouldConnectSucceed {
            connectionHandler?()
        } else {
            // Simulate connection failure
        }
    }

    override func cancel(with closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        cancelCalled = true
    }

    override func send(_ message: URLSessionWebSocketTask.Message) async throws {
        sendCalled = true

        if case .string(let text) = message {
            lastSentMessage = text
        }

        if !shouldSendSucceed {
            throw mockError ?? WebSocketError.sendFailed
        }
    }

    override func receive() async throws -> URLSessionWebSocketTask.Message {
        // This would be called in a loop in real implementation
        return .string("mock_message")
    }

    // Test helper methods
    func simulateReceivedMessage(_ message: URLSessionWebSocketTask.Message) {
        messageHandler?(message)
    }

    func simulateConnectionLoss() {
        // Simulate connection loss
        cancelCalled = true
    }

    func setMessageHandler(_ handler: @escaping (URLSessionWebSocketTask.Message) -> Void) {
        messageHandler = handler
    }

    func setConnectionHandler(_ handler: @escaping () -> Void) {
        connectionHandler = handler
    }
}

class MockAuthenticationService: ObservableObject {
    @Published var isAuthenticated = false
    var mockAccessToken: String?

    func triggerAuthenticationChange() {
        objectWillChange.send()
    }

    func triggerTokenRefresh() {
        objectWillChange.send()
    }

    func getAccessToken() -> String? {
        return mockAccessToken
    }
}

// MARK: - Error Types

enum WebSocketError: Error {
    case connectionFailed
    case sendFailed
    case invalidMessage
    case notAuthenticated
}

// MARK: - Message Types

enum WebSocketMessage {
    case subscribe(channel: String)
    case unsubscribe(channel: String)
    case ping
    case pong
    case custom(data: [String: Any])
}

enum WebSocketReceivedMessage {
    case opportunityUpdate(opportunity: BettingOpportunity)
    case userUpdate(userInfo: [String: Any])
    case subscriptionConfirmation(channel: String)
    case error(message: String)
}

// MARK: - Connection State

enum WebSocketConnectionState {
    case disconnected
    case connecting
    case connected
    case failed
}

// MARK: - Network Types

enum NetworkType {
    case wifi
    case cellular
    case none
}
