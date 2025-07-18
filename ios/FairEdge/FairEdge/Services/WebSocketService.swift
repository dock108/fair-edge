//
//  WebSocketService.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import Foundation
import Combine
import SwiftUI
import Network

/// Connection status for WebSocket
enum ConnectionStatus: String, CaseIterable {
    case disconnected = "disconnected"
    case connecting = "connecting"
    case connected = "connected"
    case reconnecting = "reconnecting"
    case error = "error"
    
    var displayText: String {
        switch self {
        case .disconnected:
            return "Disconnected"
        case .connecting:
            return "Connecting..."
        case .connected:
            return "Live Updates Active"
        case .reconnecting:
            return "Reconnecting..."
        case .error:
            return "Connection Error"
        }
    }
    
    var color: Color {
        switch self {
        case .disconnected:
            return .gray
        case .connecting, .reconnecting:
            return .orange
        case .connected:
            return .green
        case .error:
            return .red
        }
    }
}

/// WebSocket message types from backend
enum WebSocketMessageType: String, Codable {
    case connection = "connection"
    case opportunityUpdate = "opportunity_update"
    case heartbeat = "heartbeat"
    case error = "error"
}

/// WebSocket message structure
struct WebSocketMessage: Codable {
    let type: WebSocketMessageType
    let data: BettingOpportunity?
    let status: String?
    let userAuthenticated: Bool?
    let userRole: String?
    let subscriptionPreferences: [String: AnyCodable]?
    let timestamp: String?
    let message: String?
    
    private enum CodingKeys: String, CodingKey {
        case type, data, status, message, timestamp
        case userAuthenticated = "user_authenticated"
        case userRole = "user_role"
        case subscriptionPreferences = "subscription_preferences"
    }
}

/// Helper for encoding/decoding any JSON value
struct AnyCodable: Codable {
    let value: Any
    
    init(_ value: Any) {
        self.value = value
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        
        if let intValue = try? container.decode(Int.self) {
            value = intValue
        } else if let doubleValue = try? container.decode(Double.self) {
            value = doubleValue
        } else if let stringValue = try? container.decode(String.self) {
            value = stringValue
        } else if let boolValue = try? container.decode(Bool.self) {
            value = boolValue
        } else if let arrayValue = try? container.decode([AnyCodable].self) {
            value = arrayValue.map { $0.value }
        } else if let dictValue = try? container.decode([String: AnyCodable].self) {
            value = dictValue.mapValues { $0.value }
        } else {
            value = NSNull()
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        
        switch value {
        case let intValue as Int:
            try container.encode(intValue)
        case let doubleValue as Double:
            try container.encode(doubleValue)
        case let stringValue as String:
            try container.encode(stringValue)
        case let boolValue as Bool:
            try container.encode(boolValue)
        case let arrayValue as [Any]:
            try container.encode(arrayValue.map(AnyCodable.init))
        case let dictValue as [String: Any]:
            try container.encode(dictValue.mapValues(AnyCodable.init))
        default:
            try container.encodeNil()
        }
    }
}

/// Real-time WebSocket service for live opportunity updates
@MainActor
class WebSocketService: NSObject, ObservableObject {
    @Published var connectionStatus: ConnectionStatus = .disconnected
    @Published var liveUpdates: [BettingOpportunity] = []
    @Published var lastUpdateTime: Date?
    @Published var isRealtimeEnabled: Bool = true
    @Published var connectionStats: String = "Not connected"
    
    private var webSocketTask: URLSessionWebSocketTask?
    private var urlSession: URLSession?
    private var heartbeatTimer: Timer?
    private var reconnectTimer: Timer?
    private var networkMonitor: NWPathMonitor?
    private var backgroundTaskID: UIBackgroundTaskIdentifier = .invalid
    
    // Reconnection strategy
    private var reconnectAttempts = 0
    private let maxReconnectAttempts = 10
    private let baseReconnectDelay: TimeInterval = 2.0
    
    // Authentication and preferences
    private var authToken: String?
    private var userPreferences: [String: Any] = [:]
    
    // Dependencies
    private let authenticationService: AuthenticationService
    private let apiService: APIService
    
    init(authenticationService: AuthenticationService, apiService: APIService) {
        self.authenticationService = authenticationService
        self.apiService = apiService
        super.init()
        
        setupNetworkMonitoring()
        setupNotificationObservers()
    }
    
    deinit {
        disconnect()
        networkMonitor?.cancel()
        NotificationCenter.default.removeObserver(self)
    }
    
    // MARK: - Public Methods
    
    func connect() {
        guard connectionStatus != .connected && connectionStatus != .connecting else {
            return
        }
        
        Task {
            await connectWebSocket()
        }
    }
    
    func disconnect() {
        connectionStatus = .disconnected
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        webSocketTask = nil
        urlSession = nil
        heartbeatTimer?.invalidate()
        reconnectTimer?.invalidate()
        endBackgroundTask()
        
        liveUpdates.removeAll()
        connectionStats = "Disconnected"
    }
    
    func toggleRealtimeUpdates() {
        isRealtimeEnabled.toggle()
        
        if isRealtimeEnabled {
            connect()
        } else {
            disconnect()
        }
    }
    
    func reconnect() {
        disconnect()
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            self.connect()
        }
    }
    
    // MARK: - Private Methods
    
    private func connectWebSocket() async {
        guard isRealtimeEnabled else { return }
        
        connectionStatus = .connecting
        
        // Get authentication token
        authToken = await authenticationService.getValidToken()
        
        // Build WebSocket URL with authentication
        guard let baseURL = URL(string: apiService.baseURL),
              var urlComponents = URLComponents(url: baseURL, resolvingAgainstBaseURL: true) else {
            handleConnectionError("Invalid base URL")
            return
        }
        
        urlComponents.scheme = urlComponents.scheme == "https" ? "wss" : "ws"
        urlComponents.path = "/api/realtime/ws/opportunities"
        
        // Add authentication token as query parameter
        if let token = authToken {
            urlComponents.queryItems = [URLQueryItem(name: "token", value: token)]
        }
        
        guard let websocketURL = urlComponents.url else {
            handleConnectionError("Failed to construct WebSocket URL")
            return
        }
        
        // Create URLSession with custom configuration
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 0 // No timeout for WebSocket
        config.waitsForConnectivity = true
        
        urlSession = URLSession(configuration: config, delegate: self, delegateQueue: nil)
        webSocketTask = urlSession?.webSocketTask(with: websocketURL)
        
        // Start background task for connection
        beginBackgroundTask()
        
        webSocketTask?.resume()
        listenForMessages()
        startHeartbeat()
        
        reconnectAttempts = 0
    }
    
    private func listenForMessages() {
        webSocketTask?.receive { [weak self] result in
            DispatchQueue.main.async {
                self?.handleWebSocketMessage(result)
            }
        }
    }
    
    private func handleWebSocketMessage(_ result: Result<URLSessionWebSocketTask.Message, Error>) {
        switch result {
        case .success(let message):
            switch message {
            case .string(let text):
                processTextMessage(text)
            case .data(let data):
                processDataMessage(data)
            @unknown default:
                print("Unknown WebSocket message type received")
            }
            
            // Continue listening for next message
            listenForMessages()
            
        case .failure(let error):
            handleConnectionError("WebSocket receive error: \(error.localizedDescription)")
        }
    }
    
    private func processTextMessage(_ text: String) {
        guard let data = text.data(using: .utf8) else {
            print("Failed to convert WebSocket text to data")
            return
        }
        
        processDataMessage(data)
    }
    
    private func processDataMessage(_ data: Data) {
        do {
            let message = try JSONDecoder().decode(WebSocketMessage.self, from: data)
            handleParsedMessage(message)
        } catch {
            print("Failed to decode WebSocket message: \(error)")
        }
    }
    
    private func handleParsedMessage(_ message: WebSocketMessage) {
        switch message.type {
        case .connection:
            handleConnectionMessage(message)
        case .opportunityUpdate:
            handleOpportunityUpdate(message)
        case .heartbeat:
            handleHeartbeat(message)
        case .error:
            handleErrorMessage(message)
        }
    }
    
    private func handleConnectionMessage(_ message: WebSocketMessage) {
        connectionStatus = .connected
        lastUpdateTime = Date()
        
        let isAuthenticated = message.userAuthenticated ?? false
        let role = message.userRole ?? "anonymous"
        
        connectionStats = "Connected as \(role)"
        
        if isAuthenticated {
            userPreferences = message.subscriptionPreferences?.mapValues { $0.value } ?? [:]
            print("WebSocket connected with user preferences: \(userPreferences)")
        }
        
        print("WebSocket connection established successfully")
    }
    
    private func handleOpportunityUpdate(_ message: WebSocketMessage) {
        guard let opportunity = message.data else {
            print("Received opportunity update without data")
            return
        }
        
        lastUpdateTime = Date()
        
        // Update or add opportunity to live updates
        if let existingIndex = liveUpdates.firstIndex(where: { $0.id == opportunity.id }) {
            liveUpdates[existingIndex] = opportunity
        } else {
            liveUpdates.insert(opportunity, at: 0)
            
            // Keep only the latest 50 opportunities to manage memory
            if liveUpdates.count > 50 {
                liveUpdates = Array(liveUpdates.prefix(50))
            }
        }
        
        // Post notification for UI updates
        NotificationCenter.default.post(
            name: NSNotification.Name("LiveOpportunityUpdate"),
            object: opportunity
        )
        
        print("Received live opportunity update: \(opportunity.displayEvent) - \(opportunity.formattedEVPercentage)")
    }
    
    private func handleHeartbeat(_ message: WebSocketMessage) {
        lastUpdateTime = Date()
        // Heartbeat received - connection is alive
    }
    
    private func handleErrorMessage(_ message: WebSocketMessage) {
        let errorMsg = message.message ?? "Unknown WebSocket error"
        handleConnectionError(errorMsg)
    }
    
    private func handleConnectionError(_ error: String) {
        print("WebSocket error: \(error)")
        connectionStatus = .error
        connectionStats = "Error: \(error)"
        
        // Attempt reconnection if enabled and within retry limits
        if isRealtimeEnabled && reconnectAttempts < maxReconnectAttempts {
            scheduleReconnection()
        }
    }
    
    private func scheduleReconnection() {
        guard connectionStatus != .connected && connectionStatus != .connecting else {
            return
        }
        
        connectionStatus = .reconnecting
        reconnectAttempts += 1
        
        // Exponential backoff with jitter
        let delay = min(baseReconnectDelay * pow(2.0, Double(reconnectAttempts)), 60.0)
        let jitter = Double.random(in: 0...2.0)
        let totalDelay = delay + jitter
        
        connectionStats = "Reconnecting in \(Int(totalDelay))s (attempt \(reconnectAttempts))"
        
        reconnectTimer?.invalidate()
        reconnectTimer = Timer.scheduledTimer(withTimeInterval: totalDelay, repeats: false) { [weak self] _ in
            Task {
                await self?.connectWebSocket()
            }
        }
    }
    
    private func startHeartbeat() {
        heartbeatTimer?.invalidate()
        heartbeatTimer = Timer.scheduledTimer(withTimeInterval: 30.0, repeats: true) { [weak self] _ in
            self?.sendHeartbeat()
        }
    }
    
    private func sendHeartbeat() {
        let heartbeat = ["type": "ping", "timestamp": ISO8601DateFormatter().string(from: Date())]
        
        do {
            let data = try JSONSerialization.data(withJSONObject: heartbeat)
            let message = URLSessionWebSocketTask.Message.data(data)
            webSocketTask?.send(message) { error in
                if let error = error {
                    print("Failed to send heartbeat: \(error)")
                }
            }
        } catch {
            print("Failed to encode heartbeat: \(error)")
        }
    }
    
    // MARK: - Background Task Management
    
    private func beginBackgroundTask() {
        backgroundTaskID = UIApplication.shared.beginBackgroundTask(withName: "WebSocketConnection") {
            self.endBackgroundTask()
        }
    }
    
    private func endBackgroundTask() {
        if backgroundTaskID != .invalid {
            UIApplication.shared.endBackgroundTask(backgroundTaskID)
            backgroundTaskID = .invalid
        }
    }
    
    // MARK: - Network Monitoring
    
    private func setupNetworkMonitoring() {
        networkMonitor = NWPathMonitor()
        
        networkMonitor?.pathUpdateHandler = { [weak self] path in
            DispatchQueue.main.async {
                if path.status == .satisfied && self?.connectionStatus == .disconnected {
                    // Network became available, attempt to reconnect
                    if self?.isRealtimeEnabled == true {
                        self?.connect()
                    }
                } else if path.status != .satisfied {
                    // Network lost, update status
                    self?.connectionStatus = .disconnected
                    self?.connectionStats = "No network connection"
                }
            }
        }
        
        networkMonitor?.start(queue: DispatchQueue.global(qos: .background))
    }
    
    // MARK: - Notification Observers
    
    private func setupNotificationObservers() {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(appDidEnterBackground),
            name: UIApplication.didEnterBackgroundNotification,
            object: nil
        )
        
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(appWillEnterForeground),
            name: UIApplication.willEnterForegroundNotification,
            object: nil
        )
    }
    
    @objc private func appDidEnterBackground() {
        // Reduce heartbeat frequency in background
        startHeartbeat()
    }
    
    @objc private func appWillEnterForeground() {
        // Restore normal heartbeat frequency
        startHeartbeat()
        
        // Reconnect if disconnected
        if isRealtimeEnabled && connectionStatus == .disconnected {
            connect()
        }
    }
}

// MARK: - URLSessionWebSocketDelegate

extension WebSocketService: URLSessionWebSocketDelegate {
    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didOpenWithProtocol protocol: String?) {
        DispatchQueue.main.async {
            print("WebSocket connection opened")
            // Connection confirmation will come via first message
        }
    }
    
    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didCloseWith closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        DispatchQueue.main.async {
            print("WebSocket connection closed with code: \(closeCode)")
            self.connectionStatus = .disconnected
            self.connectionStats = "Connection closed"
            
            // Attempt reconnection if enabled
            if self.isRealtimeEnabled {
                self.scheduleReconnection()
            }
        }
    }
}

// MARK: - Preview Helper

extension WebSocketService {
    static func preview() -> WebSocketService {
        return WebSocketService(
            authenticationService: AuthenticationService(),
            apiService: APIService()
        )
    }
}