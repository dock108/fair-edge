//
//  AuthenticationServiceTests.swift
//  FairEdgeTests
//
//  Unit tests for AuthenticationService
//  Tests authentication flows, token management, and user state

import XCTest
import Combine
import AuthenticationServices
@testable import FairEdge

class AuthenticationServiceTests: XCTestCase {
    
    // MARK: - Properties
    
    var authService: AuthenticationService!
    var cancellables: Set<AnyCancellable>!
    var mockAPIService: MockAPIService!
    var mockKeychainService: MockKeychainService!
    
    // MARK: - Setup & Teardown
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        // Create mocks
        mockAPIService = MockAPIService()
        mockKeychainService = MockKeychainService()
        
        // Initialize service with mocks
        authService = AuthenticationService()
        cancellables = Set<AnyCancellable>()
        
        // Clear keychain state
        mockKeychainService.clear()
    }
    
    override func tearDownWithError() throws {
        authService = nil
        mockAPIService = nil
        mockKeychainService = nil
        cancellables.removeAll()
        cancellables = nil
        try super.tearDownWithError()
    }
    
    // MARK: - Authentication Status Tests
    
    func testInitialAuthenticationStatus_NotAuthenticated() throws {
        // Given: No stored tokens
        mockKeychainService.shouldReturnToken = false
        
        // When: Service initializes
        let service = AuthenticationService()
        
        // Then: User should not be authenticated
        XCTAssertFalse(service.isAuthenticated)
        XCTAssertNil(service.currentUser)
    }
    
    func testCheckAuthenticationStatus_WithValidToken() throws {
        // Given: Valid token stored
        mockKeychainService.shouldReturnToken = true
        mockAPIService.shouldRefreshSucceed = true
        
        let expectation = XCTestExpectation(description: "Authentication check")
        
        // When: Checking authentication status
        authService.checkAuthenticationStatus()
        
        // Then: Should become authenticated
        authService.$isAuthenticated
            .dropFirst()
            .sink { isAuthenticated in
                XCTAssertTrue(isAuthenticated)
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testCheckAuthenticationStatus_WithInvalidToken() throws {
        // Given: Invalid token stored
        mockKeychainService.shouldReturnToken = true
        mockAPIService.shouldRefreshSucceed = false
        
        let expectation = XCTestExpectation(description: "Authentication check fails")
        
        // When: Checking authentication status
        authService.checkAuthenticationStatus()
        
        // Then: Should remain unauthenticated
        authService.$isAuthenticated
            .dropFirst()
            .sink { isAuthenticated in
                XCTAssertFalse(isAuthenticated)
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    // MARK: - Sign In Tests
    
    func testSignInWithApple_Success() throws {
        // Given: Mock Apple ID credential
        let mockCredential = MockASAuthorizationAppleIDCredential()
        mockCredential.identityToken = "mock_identity_token".data(using: .utf8)
        mockCredential.user = "test_user_123"
        
        mockAPIService.shouldLoginSucceed = true
        
        let expectation = XCTestExpectation(description: "Sign in succeeds")
        
        // When: Signing in with Apple
        authService.signInWithApple(credential: mockCredential)
        
        // Then: Should become authenticated
        authService.$isAuthenticated
            .dropFirst()
            .sink { isAuthenticated in
                XCTAssertTrue(isAuthenticated)
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testSignInWithApple_Failure() throws {
        // Given: Mock Apple ID credential
        let mockCredential = MockASAuthorizationAppleIDCredential()
        mockCredential.identityToken = "invalid_token".data(using: .utf8)
        
        mockAPIService.shouldLoginSucceed = false
        
        let expectation = XCTestExpectation(description: "Sign in fails")
        
        // When: Signing in with Apple
        authService.signInWithApple(credential: mockCredential)
        
        // Then: Should show error and remain unauthenticated
        authService.$errorMessage
            .compactMap { $0 }
            .sink { errorMessage in
                XCTAssertNotNil(errorMessage)
                XCTAssertFalse(self.authService.isAuthenticated)
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testSignInWithApple_MissingIdentityToken() throws {
        // Given: Mock credential without identity token
        let mockCredential = MockASAuthorizationAppleIDCredential()
        mockCredential.identityToken = nil
        
        let expectation = XCTestExpectation(description: "Sign in fails due to missing token")
        
        // When: Signing in with Apple
        authService.signInWithApple(credential: mockCredential)
        
        // Then: Should show error
        authService.$errorMessage
            .compactMap { $0 }
            .sink { errorMessage in
                XCTAssertTrue(errorMessage.contains("identity token"))
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    // MARK: - Sign Out Tests
    
    func testSignOut_Success() throws {
        // Given: User is authenticated
        authService.isAuthenticated = true
        authService.currentUser = createMockUser()
        
        mockAPIService.shouldLogoutSucceed = true
        
        let expectation = XCTestExpectation(description: "Sign out succeeds")
        
        // When: Signing out
        authService.signOut()
        
        // Then: Should become unauthenticated
        authService.$isAuthenticated
            .dropFirst()
            .sink { isAuthenticated in
                XCTAssertFalse(isAuthenticated)
                XCTAssertNil(self.authService.currentUser)
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testSignOut_ClearsStoredTokens() throws {
        // Given: User is authenticated with stored tokens
        authService.isAuthenticated = true
        mockKeychainService.shouldReturnToken = true
        
        // When: Signing out
        authService.signOut()
        
        // Then: Should clear stored tokens
        XCTAssertTrue(mockKeychainService.deleteCallCount > 0)
    }
    
    // MARK: - Token Refresh Tests
    
    func testTokenRefresh_Success() throws {
        // Given: Valid refresh token
        mockKeychainService.shouldReturnToken = true
        mockAPIService.shouldRefreshSucceed = true
        
        let expectation = XCTestExpectation(description: "Token refresh succeeds")
        
        // When: Refreshing token
        authService.refreshTokenIfNeeded()
        
        // Then: Should maintain authentication
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            XCTAssertTrue(self.authService.isAuthenticated)
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testTokenRefresh_Failure_SignsOut() throws {
        // Given: Invalid refresh token
        authService.isAuthenticated = true
        mockAPIService.shouldRefreshSucceed = false
        
        let expectation = XCTestExpectation(description: "Token refresh fails and signs out")
        
        // When: Refreshing token
        authService.refreshTokenIfNeeded()
        
        // Then: Should sign out user
        authService.$isAuthenticated
            .dropFirst()
            .sink { isAuthenticated in
                XCTAssertFalse(isAuthenticated)
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    // MARK: - User Data Loading Tests
    
    func testPreloadUserData_Success() async throws {
        // Given: Authenticated user
        authService.isAuthenticated = true
        mockAPIService.shouldLoadUserDataSucceed = true
        
        // When: Preloading user data
        await authService.preloadUserData()
        
        // Then: User data should be loaded
        XCTAssertNotNil(authService.currentUser)
    }
    
    func testPreloadUserData_Failure() async throws {
        // Given: Authenticated user with API failure
        authService.isAuthenticated = true
        mockAPIService.shouldLoadUserDataSucceed = false
        
        // When: Preloading user data
        await authService.preloadUserData()
        
        // Then: Should handle error gracefully
        XCTAssertNotNil(authService.errorMessage)
    }
    
    // MARK: - Loading State Tests
    
    func testLoadingState_DuringSignIn() throws {
        // Given: Mock credential
        let mockCredential = MockASAuthorizationAppleIDCredential()
        mockCredential.identityToken = "token".data(using: .utf8)
        
        mockAPIService.delayResponse = true
        
        let expectation = XCTestExpectation(description: "Loading state changes")
        
        // When: Starting sign in
        authService.signInWithApple(credential: mockCredential)
        
        // Then: Should show loading state
        authService.$isLoading
            .dropFirst()
            .sink { isLoading in
                XCTAssertTrue(isLoading)
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 2.0)
    }
    
    // MARK: - Error Handling Tests
    
    func testErrorMessage_ClearsAfterSuccessfulOperation() throws {
        // Given: Service with error state
        authService.errorMessage = "Previous error"
        
        let mockCredential = MockASAuthorizationAppleIDCredential()
        mockCredential.identityToken = "valid_token".data(using: .utf8)
        mockAPIService.shouldLoginSucceed = true
        
        let expectation = XCTestExpectation(description: "Error clears")
        
        // When: Performing successful operation
        authService.signInWithApple(credential: mockCredential)
        
        // Then: Error should be cleared
        authService.$errorMessage
            .dropFirst()
            .sink { errorMessage in
                XCTAssertNil(errorMessage)
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    // MARK: - Concurrent Operation Tests
    
    func testConcurrentSignInAttempts() throws {
        // Given: Multiple sign in attempts
        let mockCredential = MockASAuthorizationAppleIDCredential()
        mockCredential.identityToken = "token".data(using: .utf8)
        
        mockAPIService.shouldLoginSucceed = true
        
        // When: Making concurrent sign in attempts
        authService.signInWithApple(credential: mockCredential)
        authService.signInWithApple(credential: mockCredential)
        authService.signInWithApple(credential: mockCredential)
        
        // Then: Should handle gracefully without crashes
        let expectation = XCTestExpectation(description: "Concurrent operations complete")
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
            XCTAssertTrue(self.authService.isAuthenticated)
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 5.0)
    }
}

// MARK: - Test Utilities

extension AuthenticationServiceTests {
    
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

// MARK: - Mock Classes

class MockAPIService {
    var shouldLoginSucceed = true
    var shouldRefreshSucceed = true
    var shouldLogoutSucceed = true
    var shouldLoadUserDataSucceed = true
    var delayResponse = false
    
    func login(identityToken: String) -> AnyPublisher<User, Error> {
        if delayResponse {
            return Future { promise in
                DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
                    if self.shouldLoginSucceed {
                        promise(.success(self.createMockUser()))
                    } else {
                        promise(.failure(AuthenticationError.invalidCredentials))
                    }
                }
            }
            .eraseToAnyPublisher()
        }
        
        if shouldLoginSucceed {
            return Just(createMockUser())
                .setFailureType(to: Error.self)
                .eraseToAnyPublisher()
        } else {
            return Fail(error: AuthenticationError.invalidCredentials)
                .eraseToAnyPublisher()
        }
    }
    
    func refreshToken() -> AnyPublisher<User, Error> {
        if shouldRefreshSucceed {
            return Just(createMockUser())
                .setFailureType(to: Error.self)
                .eraseToAnyPublisher()
        } else {
            return Fail(error: AuthenticationError.tokenExpired)
                .eraseToAnyPublisher()
        }
    }
    
    private func createMockUser() -> User {
        return User(
            id: "test_user_123",
            email: "test@fair-edge.com",
            role: .premium,
            subscriptionStatus: .active,
            deviceId: "test_device_123"
        )
    }
}

class MockKeychainService {
    var shouldReturnToken = false
    var deleteCallCount = 0
    
    func clear() {
        shouldReturnToken = false
        deleteCallCount = 0
    }
    
    func exists(for key: String) -> Bool {
        return shouldReturnToken
    }
    
    func delete(for key: String) {
        deleteCallCount += 1
    }
}

class MockASAuthorizationAppleIDCredential: ASAuthorizationAppleIDCredential {
    var mockUser: String = ""
    var mockIdentityToken: Data?
    
    override var user: String {
        return mockUser
    }
    
    override var identityToken: Data? {
        return mockIdentityToken
    }
}

enum AuthenticationError: Error {
    case invalidCredentials
    case tokenExpired
    case networkError
}