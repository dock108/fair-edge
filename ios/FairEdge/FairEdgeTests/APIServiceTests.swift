//
//  APIServiceTests.swift
//  FairEdgeTests
//
//  Unit tests for APIService
//  Tests network communication, error handling, and data parsing

import XCTest
import Combine
@testable import FairEdge

class APIServiceTests: XCTestCase {
    
    // MARK: - Properties
    
    var apiService: APIService!
    var mockURLSession: MockURLSession!
    var cancellables: Set<AnyCancellable>!
    
    // MARK: - Setup & Teardown
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        mockURLSession = MockURLSession()
        apiService = APIService(urlSession: mockURLSession)
        cancellables = Set<AnyCancellable>()
    }
    
    override func tearDownWithError() throws {
        apiService = nil
        mockURLSession = nil
        cancellables.removeAll()
        cancellables = nil
        try super.tearDownWithError()
    }
    
    // MARK: - Opportunities API Tests
    
    func testFetchOpportunities_Success() throws {
        // Given: Mock successful response
        let mockOpportunities = [createMockOpportunity()]
        let mockData = try JSONEncoder().encode(OpportunitiesResponse(
            opportunities: mockOpportunities,
            totalCount: 1,
            filtersApplied: FiltersApplied(userRole: "premium")
        ))
        
        mockURLSession.data = mockData
        mockURLSession.response = HTTPURLResponse(
            url: URL(string: "https://api.fair-edge.com/opportunities")!,
            statusCode: 200,
            httpVersion: nil,
            headerFields: nil
        )
        
        let expectation = XCTestExpectation(description: "Fetch opportunities succeeds")
        
        // When: Fetching opportunities
        apiService.fetchOpportunities()
            .sink(
                receiveCompletion: { completion in
                    if case .failure = completion {
                        XCTFail("Should not fail")
                    }
                },
                receiveValue: { response in
                    XCTAssertEqual(response.opportunities.count, 1)
                    XCTAssertEqual(response.opportunities.first?.id, "test_opp_123")
                    expectation.fulfill()
                }
            )
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testFetchOpportunities_NetworkError() throws {
        // Given: Network error
        mockURLSession.error = URLError(.notConnectedToInternet)
        
        let expectation = XCTestExpectation(description: "Network error handled")
        
        // When: Fetching opportunities
        apiService.fetchOpportunities()
            .sink(
                receiveCompletion: { completion in
                    if case .failure(let error) = completion {
                        XCTAssertTrue(error is URLError)
                        expectation.fulfill()
                    }
                },
                receiveValue: { _ in
                    XCTFail("Should not succeed")
                }
            )
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testFetchOpportunities_InvalidResponse() throws {
        // Given: Invalid JSON response
        mockURLSession.data = "invalid json".data(using: .utf8)
        mockURLSession.response = HTTPURLResponse(
            url: URL(string: "https://api.fair-edge.com/opportunities")!,
            statusCode: 200,
            httpVersion: nil,
            headerFields: nil
        )
        
        let expectation = XCTestExpectation(description: "Invalid response handled")
        
        // When: Fetching opportunities
        apiService.fetchOpportunities()
            .sink(
                receiveCompletion: { completion in
                    if case .failure(let error) = completion {
                        XCTAssertTrue(error is DecodingError)
                        expectation.fulfill()
                    }
                },
                receiveValue: { _ in
                    XCTFail("Should not succeed")
                }
            )
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testFetchOpportunities_HTTPError() throws {
        // Given: HTTP error response
        mockURLSession.response = HTTPURLResponse(
            url: URL(string: "https://api.fair-edge.com/opportunities")!,
            statusCode: 401,
            httpVersion: nil,
            headerFields: nil
        )
        
        let expectation = XCTestExpectation(description: "HTTP error handled")
        
        // When: Fetching opportunities
        apiService.fetchOpportunities()
            .sink(
                receiveCompletion: { completion in
                    if case .failure(let error) = completion {
                        XCTAssertTrue(error is APIError)
                        expectation.fulfill()
                    }
                },
                receiveValue: { _ in
                    XCTFail("Should not succeed")
                }
            )
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    // MARK: - Authentication API Tests
    
    func testCreateMobileSession_Success() throws {
        // Given: Mock successful session response
        let mockSession = MobileSessionResponse(
            success: true,
            accessToken: "mock_access_token",
            refreshToken: "mock_refresh_token",
            user: createMockUser(),
            deviceInfo: DeviceInfo(deviceId: "test_device", registeredAt: Date())
        )
        
        let mockData = try JSONEncoder().encode(mockSession)
        mockURLSession.data = mockData
        mockURLSession.response = HTTPURLResponse(
            url: URL(string: "https://api.fair-edge.com/mobile/session")!,
            statusCode: 201,
            httpVersion: nil,
            headerFields: nil
        )
        
        let expectation = XCTestExpectation(description: "Create session succeeds")
        
        // When: Creating mobile session
        apiService.createMobileSession(
            email: "test@fair-edge.com",
            identityToken: "mock_token",
            deviceId: "test_device"
        )
        .sink(
            receiveCompletion: { completion in
                if case .failure = completion {
                    XCTFail("Should not fail")
                }
            },
            receiveValue: { response in
                XCTAssertTrue(response.success)
                XCTAssertEqual(response.accessToken, "mock_access_token")
                XCTAssertEqual(response.user.email, "test@fair-edge.com")
                expectation.fulfill()
            }
        )
        .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testRefreshToken_Success() throws {
        // Given: Mock successful refresh response
        let mockUser = createMockUser()
        let mockData = try JSONEncoder().encode(mockUser)
        
        mockURLSession.data = mockData
        mockURLSession.response = HTTPURLResponse(
            url: URL(string: "https://api.fair-edge.com/mobile/session/refresh")!,
            statusCode: 200,
            httpVersion: nil,
            headerFields: nil
        )
        
        let expectation = XCTestExpectation(description: "Token refresh succeeds")
        
        // When: Refreshing token
        apiService.refreshToken()
            .sink(
                receiveCompletion: { completion in
                    if case .failure = completion {
                        XCTFail("Should not fail")
                    }
                },
                receiveValue: { user in
                    XCTAssertEqual(user.email, "test@fair-edge.com")
                    expectation.fulfill()
                }
            )
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    // MARK: - Apple IAP API Tests
    
    func testValidateReceipt_Success() throws {
        // Given: Mock successful validation response
        let mockResponse = ReceiptValidationResponse(
            success: true,
            subscriptionStatus: "active",
            userRole: "premium",
            expiresDate: Date().addingTimeInterval(2592000), // 30 days
            isActive: true
        )
        
        let mockData = try JSONEncoder().encode(mockResponse)
        mockURLSession.data = mockData
        mockURLSession.response = HTTPURLResponse(
            url: URL(string: "https://api.fair-edge.com/iap/validate-receipt")!,
            statusCode: 200,
            httpVersion: nil,
            headerFields: nil
        )
        
        let expectation = XCTestExpectation(description: "Receipt validation succeeds")
        
        // When: Validating receipt
        apiService.validateReceipt(receiptData: "mock_receipt_data")
            .sink(
                receiveCompletion: { completion in
                    if case .failure = completion {
                        XCTFail("Should not fail")
                    }
                },
                receiveValue: { response in
                    XCTAssertTrue(response.success)
                    XCTAssertEqual(response.subscriptionStatus, "active")
                    XCTAssertEqual(response.userRole, "premium")
                    expectation.fulfill()
                }
            )
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testGetSubscriptionStatus_Success() throws {
        // Given: Mock subscription status response
        let mockStatus = SubscriptionStatusResponse(
            role: "premium",
            subscriptionStatus: "active",
            expiresDate: Date().addingTimeInterval(2592000),
            hasAppleSubscription: true,
            isSubscriber: true
        )
        
        let mockData = try JSONEncoder().encode(mockStatus)
        mockURLSession.data = mockData
        mockURLSession.response = HTTPURLResponse(
            url: URL(string: "https://api.fair-edge.com/iap/subscription-status")!,
            statusCode: 200,
            httpVersion: nil,
            headerFields: nil
        )
        
        let expectation = XCTestExpectation(description: "Subscription status fetch succeeds")
        
        // When: Getting subscription status
        apiService.getSubscriptionStatus()
            .sink(
                receiveCompletion: { completion in
                    if case .failure = completion {
                        XCTFail("Should not fail")
                    }
                },
                receiveValue: { status in
                    XCTAssertEqual(status.role, "premium")
                    XCTAssertTrue(status.hasAppleSubscription)
                    XCTAssertTrue(status.isSubscriber)
                    expectation.fulfill()
                }
            )
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    // MARK: - Request Building Tests
    
    func testRequestBuilding_IncludesAuthHeaders() throws {
        // Given: API service with stored token
        KeychainService.shared.save("test_token", for: "access_token")
        
        // When: Building authenticated request
        var request = URLRequest(url: URL(string: "https://api.fair-edge.com/test")!)
        apiService.addAuthenticationHeaders(to: &request)
        
        // Then: Should include auth header
        XCTAssertEqual(request.value(forHTTPHeaderField: "Authorization"), "Bearer test_token")
        
        // Cleanup
        KeychainService.shared.delete(for: "access_token")
    }
    
    func testRequestBuilding_IncludesDeviceHeaders() throws {
        // When: Building request with device info
        var request = URLRequest(url: URL(string: "https://api.fair-edge.com/test")!)
        apiService.addDeviceHeaders(to: &request)
        
        // Then: Should include device headers
        XCTAssertNotNil(request.value(forHTTPHeaderField: "X-Device-ID"))
        XCTAssertNotNil(request.value(forHTTPHeaderField: "X-App-Version"))
        XCTAssertEqual(request.value(forHTTPHeaderField: "X-Platform"), "iOS")
    }
    
    // MARK: - Error Handling Tests
    
    func testErrorHandling_Timeout() throws {
        // Given: Timeout error
        mockURLSession.error = URLError(.timedOut)
        
        let expectation = XCTestExpectation(description: "Timeout handled")
        
        // When: Making request
        apiService.fetchOpportunities()
            .sink(
                receiveCompletion: { completion in
                    if case .failure(let error) = completion {
                        XCTAssertTrue(error is URLError)
                        expectation.fulfill()
                    }
                },
                receiveValue: { _ in
                    XCTFail("Should not succeed")
                }
            )
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testErrorHandling_ServerError() throws {
        // Given: 500 server error
        mockURLSession.response = HTTPURLResponse(
            url: URL(string: "https://api.fair-edge.com/opportunities")!,
            statusCode: 500,
            httpVersion: nil,
            headerFields: nil
        )
        
        let expectation = XCTestExpectation(description: "Server error handled")
        
        // When: Making request
        apiService.fetchOpportunities()
            .sink(
                receiveCompletion: { completion in
                    if case .failure(let error) = completion {
                        XCTAssertTrue(error is APIError)
                        if case .serverError = error as? APIError {
                            expectation.fulfill()
                        }
                    }
                },
                receiveValue: { _ in
                    XCTFail("Should not succeed")
                }
            )
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    // MARK: - Performance Tests
    
    func testAPIPerformance_OpportunitiesRequest() throws {
        // Given: Large mock response
        let opportunities = Array(0..<100).map { _ in createMockOpportunity() }
        let response = OpportunitiesResponse(
            opportunities: opportunities,
            totalCount: 100,
            filtersApplied: FiltersApplied(userRole: "premium")
        )
        
        let mockData = try JSONEncoder().encode(response)
        mockURLSession.data = mockData
        mockURLSession.response = HTTPURLResponse(
            url: URL(string: "https://api.fair-edge.com/opportunities")!,
            statusCode: 200,
            httpVersion: nil,
            headerFields: nil
        )
        
        // When: Measuring performance
        measure {
            let expectation = XCTestExpectation(description: "Performance test")
            
            apiService.fetchOpportunities()
                .sink(
                    receiveCompletion: { _ in },
                    receiveValue: { _ in
                        expectation.fulfill()
                    }
                )
                .store(in: &cancellables)
            
            wait(for: [expectation], timeout: 5.0)
        }
    }
}

// MARK: - Test Utilities

extension APIServiceTests {
    
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
    
    func createMockUser() -> User {
        return User(
            id: "test_user_123",
            email: "test@fair-edge.com",
            role: .premium,
            subscriptionStatus: .active,
            deviceId: "test_device_123"
        )
    }
}

// MARK: - Mock URLSession

class MockURLSession: URLSessionProtocol {
    var data: Data?
    var response: URLResponse?
    var error: Error?
    
    func dataTaskPublisher(for request: URLRequest) -> URLSession.DataTaskPublisher {
        // Create a mock publisher that returns our test data
        if let error = error {
            return Fail(error: error)
                .eraseToAnyPublisher()
                .setFailureType(to: URLError.self)
                .map { _ in (data: Data(), response: URLResponse()) }
                .setFailureType(to: URLError.self)
                .eraseToAnyPublisher()
        }
        
        let data = self.data ?? Data()
        let response = self.response ?? URLResponse()
        
        return Just((data: data, response: response))
            .setFailureType(to: URLError.self)
            .eraseToAnyPublisher()
    }
}

// MARK: - Protocol for URLSession

protocol URLSessionProtocol {
    func dataTaskPublisher(for request: URLRequest) -> URLSession.DataTaskPublisher
}

extension URLSession: URLSessionProtocol {}

// MARK: - API Error Types

enum APIError: Error {
    case invalidURL
    case noData
    case unauthorized
    case serverError
    case decodingError
}

// MARK: - Response Models

struct OpportunitiesResponse: Codable {
    let opportunities: [BettingOpportunity]
    let totalCount: Int
    let filtersApplied: FiltersApplied
}

struct FiltersApplied: Codable {
    let userRole: String
}

struct MobileSessionResponse: Codable {
    let success: Bool
    let accessToken: String
    let refreshToken: String
    let user: User
    let deviceInfo: DeviceInfo
}

struct DeviceInfo: Codable {
    let deviceId: String
    let registeredAt: Date
}

struct ReceiptValidationResponse: Codable {
    let success: Bool
    let subscriptionStatus: String
    let userRole: String
    let expiresDate: Date
    let isActive: Bool
}

struct SubscriptionStatusResponse: Codable {
    let role: String
    let subscriptionStatus: String
    let expiresDate: Date
    let hasAppleSubscription: Bool
    let isSubscriber: Bool
}