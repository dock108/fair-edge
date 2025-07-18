//
//  APIService.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import Foundation
import Combine

/// API service for communicating with Fair-Edge mobile-optimized backend
class APIService: ObservableObject {
    
    // MARK: - Properties
    
    private let baseURL: String
    private let session: URLSession
    private var cancellables = Set<AnyCancellable>()
    
    @Published var isConnected = false
    @Published var lastError: APIError?
    
    // MARK: - Initialization
    
    init() {
        // Configure base URL based on environment
        #if DEBUG
        self.baseURL = "http://localhost:8000/api"
        #else
        self.baseURL = "https://api.fair-edge.com/api"  // Production URL
        #endif
        
        // Configure URLSession with mobile-optimized settings
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
        config.waitsForConnectivity = true
        config.allowsCellularAccess = true
        
        self.session = URLSession(configuration: config)
        
        // Test connectivity on initialization
        checkConnectivity()
    }
    
    // MARK: - Authentication Endpoints
    
    /// Create mobile session with 24-hour token
    func createMobileSession(request: MobileSessionRequest) -> AnyPublisher<MobileSessionResponse, APIError> {
        let url = URL(string: "\(baseURL)/mobile/session")!
        
        return performRequest(url: url, method: "POST", body: request)
            .map { (response: MobileSessionResponse) in
                // Store tokens securely after successful authentication
                KeychainService.shared.store(token: response.accessToken, for: "access_token")
                KeychainService.shared.store(token: response.refreshToken, for: "refresh_token")
                return response
            }
            .eraseToAnyPublisher()
    }
    
    /// Refresh authentication token for background operation
    func refreshToken() -> AnyPublisher<AuthToken, APIError> {
        guard let refreshToken = KeychainService.shared.retrieve(for: "refresh_token"),
              let deviceId = DeviceIdentifier.shared.deviceId else {
            return Fail(error: APIError.authenticationRequired)
                .eraseToAnyPublisher()
        }
        
        let url = URL(string: "\(baseURL)/mobile/refresh-token")!
        let request = TokenRefreshRequest(refreshToken: refreshToken, deviceId: deviceId)
        
        return performRequest(url: url, method: "POST", body: request)
            .map { (response: AuthToken) in
                // Update stored tokens
                KeychainService.shared.store(token: response.accessToken, for: "access_token")
                KeychainService.shared.store(token: response.refreshToken, for: "refresh_token")
                return response
            }
            .eraseToAnyPublisher()
    }
    
    // MARK: - Opportunities Endpoints
    
    /// Fetch betting opportunities using mobile-optimized endpoint (45% smaller payload)
    func fetchOpportunities(useCache: Bool = true) -> AnyPublisher<OpportunitiesResponse, APIError> {
        let url = URL(string: "\(baseURL)/opportunities?mobile=true")!
        
        return performAuthenticatedRequest(url: url, method: "GET")
    }
    
    // MARK: - Mobile Configuration
    
    /// Get mobile app configuration
    func getMobileConfig() -> AnyPublisher<MobileConfig, APIError> {
        let url = URL(string: "\(baseURL)/mobile/config")!
        
        return performRequest(url: url, method: "GET")
    }
    
    /// Check mobile API health
    func checkMobileHealth() -> AnyPublisher<MobileHealthResponse, APIError> {
        let url = URL(string: "\(baseURL)/mobile/health")!
        
        return performRequest(url: url, method: "GET")
    }
    
    // MARK: - Device Registration
    
    /// Register device for push notifications
    func registerDevice(deviceToken: String) -> AnyPublisher<DeviceRegistrationResponse, APIError> {
        let url = URL(string: "\(baseURL)/mobile/register-device")!
        let request = DeviceRegistrationRequest(
            deviceToken: deviceToken,
            deviceId: DeviceIdentifier.shared.deviceId ?? "",
            platform: "ios",
            appVersion: Bundle.main.appVersion
        )
        
        return performAuthenticatedRequest(url: url, method: "POST", body: request)
    }
    
    // MARK: - Apple In-App Purchase Endpoints
    
    /// Validate Apple receipt with backend
    func validateAppleReceipt(_ request: ReceiptValidationRequest) -> AnyPublisher<ReceiptValidationResponse, APIError> {
        let url = URL(string: "\(baseURL)/iap/validate-receipt")!
        
        return performAuthenticatedRequest(url: url, method: "POST", body: request)
    }
    
    /// Get subscription status from Apple IAP
    func getSubscriptionStatus() -> AnyPublisher<SubscriptionStatusResponse, APIError> {
        let url = URL(string: "\(baseURL)/iap/subscription-status")!
        
        return performAuthenticatedRequest(url: url, method: "GET")
    }
    
    /// Restore purchases from Apple IAP
    func restorePurchases() -> AnyPublisher<RestorePurchasesResponse, APIError> {
        let url = URL(string: "\(baseURL)/iap/restore-purchases")!
        
        return performAuthenticatedRequest(url: url, method: "POST")
    }
    
    /// Get available Apple IAP products
    func getAppleProducts() -> AnyPublisher<AppleProductsResponse, APIError> {
        let url = URL(string: "\(baseURL)/iap/products")!
        
        return performAuthenticatedRequest(url: url, method: "GET")
    }
    
    /// Refresh subscription status
    func refreshSubscriptionStatus() -> AnyPublisher<SubscriptionStatusResponse, APIError> {
        let url = URL(string: "\(baseURL)/iap/refresh-subscription")!
        
        return performAuthenticatedRequest(url: url, method: "POST")
    }
    
    // MARK: - Private Helper Methods
    
    /// Perform authenticated request with automatic token refresh
    private func performAuthenticatedRequest<T: Codable, U: Codable>(
        url: URL,
        method: String,
        body: U? = nil
    ) -> AnyPublisher<T, APIError> {
        
        // First attempt with current token
        return performRequestWithAuth(url: url, method: method, body: body)
            .catch { [weak self] error -> AnyPublisher<T, APIError> in
                guard let self = self,
                      case .unauthorized = error else {
                    return Fail(error: error).eraseToAnyPublisher()
                }
                
                // Token expired, try to refresh
                return self.refreshToken()
                    .flatMap { _ in
                        // Retry original request with new token
                        self.performRequestWithAuth(url: url, method: method, body: body)
                    }
                    .eraseToAnyPublisher()
            }
            .eraseToAnyPublisher()
    }
    
    /// Perform request with current authentication token
    private func performRequestWithAuth<T: Codable, U: Codable>(
        url: URL,
        method: String,
        body: U? = nil
    ) -> AnyPublisher<T, APIError> {
        
        guard let accessToken = KeychainService.shared.retrieve(for: "access_token") else {
            return Fail(error: APIError.authenticationRequired)
                .eraseToAnyPublisher()
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("mobile-ios", forHTTPHeaderField: "User-Agent")
        
        if let body = body {
            do {
                request.httpBody = try JSONEncoder().encode(body)
            } catch {
                return Fail(error: APIError.encodingError(error))
                    .eraseToAnyPublisher()
            }
        }
        
        return session.dataTaskPublisher(for: request)
            .map(\.data)
            .decode(type: T.self, decoder: JSONDecoder())
            .mapError { error in
                if error is DecodingError {
                    return APIError.decodingError(error)
                } else {
                    return APIError.networkError(error)
                }
            }
            .eraseToAnyPublisher()
    }
    
    /// Perform basic request without authentication
    private func performRequest<T: Codable, U: Codable>(
        url: URL,
        method: String,
        body: U? = nil
    ) -> AnyPublisher<T, APIError> {
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("mobile-ios", forHTTPHeaderField: "User-Agent")
        
        if let body = body {
            do {
                request.httpBody = try JSONEncoder().encode(body)
            } catch {
                return Fail(error: APIError.encodingError(error))
                    .eraseToAnyPublisher()
            }
        }
        
        return session.dataTaskPublisher(for: request)
            .tryMap { data, response in
                guard let httpResponse = response as? HTTPURLResponse else {
                    throw APIError.invalidResponse
                }
                
                switch httpResponse.statusCode {
                case 200...299:
                    return data
                case 401:
                    throw APIError.unauthorized
                case 429:
                    throw APIError.rateLimited
                case 500...599:
                    throw APIError.serverError(httpResponse.statusCode)
                default:
                    throw APIError.httpError(httpResponse.statusCode)
                }
            }
            .decode(type: T.self, decoder: JSONDecoder())
            .mapError { error in
                if let apiError = error as? APIError {
                    return apiError
                } else if error is DecodingError {
                    return APIError.decodingError(error)
                } else {
                    return APIError.networkError(error)
                }
            }
            .eraseToAnyPublisher()
    }
    
    /// Check basic connectivity to the API
    private func checkConnectivity() {
        getMobileHealth()
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { [weak self] completion in
                    switch completion {
                    case .finished:
                        self?.isConnected = true
                        self?.lastError = nil
                    case .failure(let error):
                        self?.isConnected = false
                        self?.lastError = error
                    }
                },
                receiveValue: { _ in }
            )
            .store(in: &cancellables)
    }
}

// MARK: - Supporting Models

/// Device registration request for push notifications
struct DeviceRegistrationRequest: Codable {
    let deviceToken: String
    let deviceId: String
    let platform: String
    let appVersion: String
    
    enum CodingKeys: String, CodingKey {
        case deviceToken = "device_token"
        case deviceId = "device_id"
        case platform
        case appVersion = "app_version"
    }
}

/// Device registration response
struct DeviceRegistrationResponse: Codable {
    let success: Bool
    let deviceId: String
    let registeredAt: String
    
    enum CodingKeys: String, CodingKey {
        case success
        case deviceId = "device_id"
        case registeredAt = "registered_at"
    }
}

// MARK: - API Error Types

/// Comprehensive API error handling
enum APIError: Error, LocalizedError {
    case networkError(Error)
    case decodingError(Error)
    case encodingError(Error)
    case invalidResponse
    case unauthorized
    case authenticationRequired
    case rateLimited
    case serverError(Int)
    case httpError(Int)
    
    var errorDescription: String? {
        switch self {
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .decodingError:
            return "Failed to decode response"
        case .encodingError:
            return "Failed to encode request"
        case .invalidResponse:
            return "Invalid response from server"
        case .unauthorized:
            return "Authentication failed"
        case .authenticationRequired:
            return "Authentication required"
        case .rateLimited:
            return "Too many requests. Please try again later."
        case .serverError(let code):
            return "Server error: \(code)"
        case .httpError(let code):
            return "HTTP error: \(code)"
        }
    }
    
    var recoverySuggestion: String? {
        switch self {
        case .networkError:
            return "Check your internet connection and try again."
        case .unauthorized, .authenticationRequired:
            return "Please sign in again."
        case .rateLimited:
            return "Wait a moment before making another request."
        case .serverError:
            return "The server is experiencing issues. Please try again later."
        default:
            return "Please try again."
        }
    }
}