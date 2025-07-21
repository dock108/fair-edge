//
//  ViewModelTests.swift
//  FairEdgeTests
//
//  Unit tests for iOS ViewModels
//  Tests business logic, state management, and UI interactions

import XCTest
import Combine
@testable import FairEdge

class ViewModelTests: XCTestCase {
    
    // MARK: - Properties
    
    var cancellables: Set<AnyCancellable>!
    var mockAPIService: MockAPIService!
    var mockAuthService: MockAuthenticationService!
    var mockAnalyticsService: MockAnalyticsService!
    
    // MARK: - Setup & Teardown
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        cancellables = Set<AnyCancellable>()
        mockAPIService = MockAPIService()
        mockAuthService = MockAuthenticationService()
        mockAnalyticsService = MockAnalyticsService()
    }
    
    override func tearDownWithError() throws {
        cancellables.removeAll()
        cancellables = nil
        mockAPIService = nil
        mockAuthService = nil
        mockAnalyticsService = nil
        try super.tearDownWithError()
    }
    
    // MARK: - OpportunityListViewModel Tests
    
    func testOpportunityListViewModel_LoadOpportunities_Success() throws {
        // Given: ViewModel with mock service
        let viewModel = OpportunityListViewModel(
            apiService: mockAPIService,
            analyticsService: mockAnalyticsService
        )
        
        mockAPIService.shouldLoadOpportunitiesSucceed = true
        mockAPIService.mockOpportunities = createMockOpportunities()
        
        let expectation = XCTestExpectation(description: "Opportunities loaded")
        
        // When: Loading opportunities
        viewModel.loadOpportunities()
        
        // Then: Should update opportunities list
        viewModel.$opportunities
            .dropFirst()
            .sink { opportunities in
                XCTAssertEqual(opportunities.count, 3)
                XCTAssertFalse(viewModel.isLoading)
                XCTAssertNil(viewModel.errorMessage)
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testOpportunityListViewModel_LoadOpportunities_Failure() throws {
        // Given: ViewModel with failing service
        let viewModel = OpportunityListViewModel(
            apiService: mockAPIService,
            analyticsService: mockAnalyticsService
        )
        
        mockAPIService.shouldLoadOpportunitiesSucceed = false
        mockAPIService.mockError = APIError.networkError
        
        let expectation = XCTestExpectation(description: "Error handled")
        
        // When: Loading opportunities fails
        viewModel.loadOpportunities()
        
        // Then: Should handle error
        viewModel.$errorMessage
            .compactMap { $0 }
            .sink { errorMessage in
                XCTAssertNotNil(errorMessage)
                XCTAssertFalse(viewModel.isLoading)
                XCTAssertTrue(viewModel.opportunities.isEmpty)
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testOpportunityListViewModel_FilterOpportunities() throws {
        // Given: ViewModel with opportunities
        let viewModel = OpportunityListViewModel(
            apiService: mockAPIService,
            analyticsService: mockAnalyticsService
        )
        
        viewModel.opportunities = createMockOpportunities()
        
        // When: Filtering by sport
        viewModel.selectedSport = "NBA"
        viewModel.applyFilters()
        
        // Then: Should filter opportunities
        let filteredOpportunities = viewModel.filteredOpportunities
        XCTAssertEqual(filteredOpportunities.count, 2) // 2 NBA opportunities
        XCTAssertTrue(filteredOpportunities.allSatisfy { $0.sport == "NBA" })
    }
    
    func testOpportunityListViewModel_SortOpportunities() throws {
        // Given: ViewModel with opportunities
        let viewModel = OpportunityListViewModel(
            apiService: mockAPIService,
            analyticsService: mockAnalyticsService
        )
        
        viewModel.opportunities = createMockOpportunities()
        
        // When: Sorting by EV percentage
        viewModel.sortOption = .evPercentage
        viewModel.applySorting()
        
        // Then: Should sort by EV descending
        let sortedOpportunities = viewModel.sortedOpportunities
        XCTAssertTrue(sortedOpportunities[0].evPercentage >= sortedOpportunities[1].evPercentage)
        XCTAssertTrue(sortedOpportunities[1].evPercentage >= sortedOpportunities[2].evPercentage)
    }
    
    func testOpportunityListViewModel_SearchOpportunities() throws {
        // Given: ViewModel with opportunities
        let viewModel = OpportunityListViewModel(
            apiService: mockAPIService,
            analyticsService: mockAnalyticsService
        )
        
        viewModel.opportunities = createMockOpportunities()
        
        // When: Searching for "Lakers"
        viewModel.searchText = "Lakers"
        
        // Then: Should filter search results
        let searchResults = viewModel.searchResults
        XCTAssertEqual(searchResults.count, 2) // 2 Lakers opportunities
        XCTAssertTrue(searchResults.allSatisfy { $0.event.contains("Lakers") })
    }
    
    func testOpportunityListViewModel_RefreshOpportunities() throws {
        // Given: ViewModel with existing opportunities
        let viewModel = OpportunityListViewModel(
            apiService: mockAPIService,
            analyticsService: mockAnalyticsService
        )
        
        viewModel.opportunities = createMockOpportunities()
        mockAPIService.shouldLoadOpportunitiesSucceed = true
        
        let expectation = XCTestExpectation(description: "Opportunities refreshed")
        
        // When: Refreshing opportunities
        viewModel.refreshOpportunities()
        
        // Then: Should reload data
        viewModel.$isRefreshing
            .dropFirst()
            .sink { isRefreshing in
                if !isRefreshing {
                    XCTAssertTrue(self.mockAPIService.loadOpportunitiesCalled)
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    // MARK: - AuthenticationViewModel Tests
    
    func testAuthenticationViewModel_SignInWithApple_Success() throws {
        // Given: Authentication ViewModel
        let viewModel = AuthenticationViewModel(
            authService: mockAuthService,
            analyticsService: mockAnalyticsService
        )
        
        mockAuthService.shouldSignInSucceed = true
        
        let expectation = XCTestExpectation(description: "Sign in successful")
        
        // When: Signing in with Apple
        viewModel.signInWithApple()
        
        // Then: Should authenticate successfully
        viewModel.$isAuthenticated
            .dropFirst()
            .sink { isAuthenticated in
                if isAuthenticated {
                    XCTAssertFalse(viewModel.isLoading)
                    XCTAssertNil(viewModel.errorMessage)
                    XCTAssertTrue(self.mockAnalyticsService.trackEventCalled)
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testAuthenticationViewModel_SignInWithApple_Failure() throws {
        // Given: Authentication ViewModel with failing service
        let viewModel = AuthenticationViewModel(
            authService: mockAuthService,
            analyticsService: mockAnalyticsService
        )
        
        mockAuthService.shouldSignInSucceed = false
        mockAuthService.mockError = AuthenticationError.signInFailed
        
        let expectation = XCTestExpectation(description: "Sign in failed")
        
        // When: Sign in fails
        viewModel.signInWithApple()
        
        // Then: Should handle error
        viewModel.$errorMessage
            .compactMap { $0 }
            .sink { errorMessage in
                XCTAssertNotNil(errorMessage)
                XCTAssertFalse(viewModel.isAuthenticated)
                XCTAssertFalse(viewModel.isLoading)
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testAuthenticationViewModel_SignOut() throws {
        // Given: Authenticated user
        let viewModel = AuthenticationViewModel(
            authService: mockAuthService,
            analyticsService: mockAnalyticsService
        )
        
        viewModel.isAuthenticated = true
        mockAuthService.shouldSignOutSucceed = true
        
        let expectation = XCTestExpectation(description: "Sign out successful")
        
        // When: Signing out
        viewModel.signOut()
        
        // Then: Should sign out successfully
        viewModel.$isAuthenticated
            .dropFirst()
            .sink { isAuthenticated in
                if !isAuthenticated {
                    XCTAssertTrue(self.mockAuthService.signOutCalled)
                    XCTAssertTrue(self.mockAnalyticsService.trackEventCalled)
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testAuthenticationViewModel_ValidateForm() throws {
        // Given: Authentication ViewModel
        let viewModel = AuthenticationViewModel(
            authService: mockAuthService,
            analyticsService: mockAnalyticsService
        )
        
        // When: Validating empty form
        let emptyFormValid = viewModel.isFormValid()
        
        // Then: Should be invalid
        XCTAssertFalse(emptyFormValid)
        
        // When: Setting valid email
        viewModel.email = "test@example.com"
        viewModel.password = "ValidPass123!"
        
        let validFormValid = viewModel.isFormValid()
        
        // Then: Should be valid
        XCTAssertTrue(validFormValid)
    }
    
    // MARK: - UserProfileViewModel Tests
    
    func testUserProfileViewModel_LoadProfile_Success() throws {
        // Given: User profile ViewModel
        let viewModel = UserProfileViewModel(
            apiService: mockAPIService,
            authService: mockAuthService,
            analyticsService: mockAnalyticsService
        )
        
        mockAPIService.shouldLoadUserProfileSucceed = true
        mockAPIService.mockUserProfile = createMockUserProfile()
        
        let expectation = XCTestExpectation(description: "Profile loaded")
        
        // When: Loading user profile
        viewModel.loadProfile()
        
        // Then: Should load profile
        viewModel.$userProfile
            .compactMap { $0 }
            .sink { profile in
                XCTAssertEqual(profile.email, "test@example.com")
                XCTAssertEqual(profile.role, .premium)
                XCTAssertFalse(viewModel.isLoading)
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testUserProfileViewModel_UpdateProfile_Success() throws {
        // Given: User profile ViewModel with loaded profile
        let viewModel = UserProfileViewModel(
            apiService: mockAPIService,
            authService: mockAuthService,
            analyticsService: mockAnalyticsService
        )
        
        viewModel.userProfile = createMockUserProfile()
        mockAPIService.shouldUpdateUserProfileSucceed = true
        
        let expectation = XCTestExpectation(description: "Profile updated")
        
        // When: Updating profile
        viewModel.updateProfile()
        
        // Then: Should update successfully
        viewModel.$profileUpdateSuccess
            .dropFirst()
            .sink { success in
                if success {
                    XCTAssertTrue(self.mockAPIService.updateUserProfileCalled)
                    XCTAssertNil(viewModel.errorMessage)
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testUserProfileViewModel_DeleteAccount() throws {
        // Given: User profile ViewModel
        let viewModel = UserProfileViewModel(
            apiService: mockAPIService,
            authService: mockAuthService,
            analyticsService: mockAnalyticsService
        )
        
        mockAPIService.shouldDeleteAccountSucceed = true
        
        let expectation = XCTestExpectation(description: "Account deleted")
        
        // When: Deleting account
        viewModel.deleteAccount()
        
        // Then: Should delete account and sign out
        viewModel.$accountDeleted
            .dropFirst()
            .sink { deleted in
                if deleted {
                    XCTAssertTrue(self.mockAPIService.deleteAccountCalled)
                    XCTAssertTrue(self.mockAuthService.signOutCalled)
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    // MARK: - SubscriptionViewModel Tests
    
    func testSubscriptionViewModel_LoadProducts_Success() throws {
        // Given: Subscription ViewModel
        let viewModel = SubscriptionViewModel(
            apiService: mockAPIService,
            iapService: MockIAPService(),
            analyticsService: mockAnalyticsService
        )
        
        let mockProducts = createMockIAPProducts()
        (viewModel.iapService as! MockIAPService).mockProducts = mockProducts
        
        let expectation = XCTestExpectation(description: "Products loaded")
        
        // When: Loading IAP products
        viewModel.loadProducts()
        
        // Then: Should load products
        viewModel.$availableProducts
            .dropFirst()
            .sink { products in
                XCTAssertEqual(products.count, 2)
                XCTAssertFalse(viewModel.isLoading)
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testSubscriptionViewModel_PurchaseProduct_Success() throws {
        // Given: Subscription ViewModel with products
        let viewModel = SubscriptionViewModel(
            apiService: mockAPIService,
            iapService: MockIAPService(),
            analyticsService: mockAnalyticsService
        )
        
        viewModel.availableProducts = createMockIAPProducts()
        let product = viewModel.availableProducts.first!
        
        (viewModel.iapService as! MockIAPService).shouldPurchaseSucceed = true
        mockAPIService.shouldValidateReceiptSucceed = true
        
        let expectation = XCTestExpectation(description: "Purchase successful")
        
        // When: Purchasing product
        viewModel.purchaseProduct(product)
        
        // Then: Should complete purchase
        viewModel.$purchaseSuccess
            .dropFirst()
            .sink { success in
                if success {
                    XCTAssertTrue(self.mockAPIService.validateReceiptCalled)
                    XCTAssertTrue(self.mockAnalyticsService.trackEventCalled)
                    XCTAssertFalse(viewModel.isPurchasing)
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testSubscriptionViewModel_RestorePurchases() throws {
        // Given: Subscription ViewModel
        let viewModel = SubscriptionViewModel(
            apiService: mockAPIService,
            iapService: MockIAPService(),
            analyticsService: mockAnalyticsService
        )
        
        (viewModel.iapService as! MockIAPService).shouldRestoreSucceed = true
        
        let expectation = XCTestExpectation(description: "Purchases restored")
        
        // When: Restoring purchases
        viewModel.restorePurchases()
        
        // Then: Should restore successfully
        viewModel.$restoreSuccess
            .dropFirst()
            .sink { success in
                if success {
                    XCTAssertTrue((viewModel.iapService as! MockIAPService).restorePurchasesCalled)
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    // MARK: - SettingsViewModel Tests
    
    func testSettingsViewModel_LoadSettings() throws {
        // Given: Settings ViewModel
        let viewModel = SettingsViewModel(
            analyticsService: mockAnalyticsService
        )
        
        // When: Loading settings
        viewModel.loadSettings()
        
        // Then: Should load default settings
        XCTAssertNotNil(viewModel.notificationSettings)
        XCTAssertNotNil(viewModel.appSettings)
        XCTAssertFalse(viewModel.isLoading)
    }
    
    func testSettingsViewModel_UpdateNotificationSettings() throws {
        // Given: Settings ViewModel
        let viewModel = SettingsViewModel(
            analyticsService: mockAnalyticsService
        )
        
        let newSettings = NotificationSettings(
            enabled: true,
            evThreshold: 8.0,
            enabledSports: ["NFL", "NBA"],
            quietHoursEnabled: true
        )
        
        let expectation = XCTestExpectation(description: "Settings updated")
        
        // When: Updating notification settings
        viewModel.updateNotificationSettings(newSettings)
        
        // Then: Should update settings
        viewModel.$notificationSettings
            .dropFirst()
            .sink { settings in
                XCTAssertEqual(settings?.evThreshold, 8.0)
                XCTAssertTrue(settings?.quietHoursEnabled ?? false)
                XCTAssertTrue(self.mockAnalyticsService.trackEventCalled)
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testSettingsViewModel_ToggleAnalytics() throws {
        // Given: Settings ViewModel with analytics enabled
        let viewModel = SettingsViewModel(
            analyticsService: mockAnalyticsService
        )
        
        viewModel.appSettings = AppSettings(
            analyticsEnabled: true,
            crashReportingEnabled: true,
            theme: .system
        )
        
        // When: Toggling analytics
        viewModel.toggleAnalytics()
        
        // Then: Should disable analytics
        XCTAssertFalse(viewModel.appSettings?.analyticsEnabled ?? true)
        XCTAssertTrue(mockAnalyticsService.setAnalyticsEnabledCalled)
    }
    
    // MARK: - OpportunityDetailViewModel Tests
    
    func testOpportunityDetailViewModel_LoadOpportunityDetail() throws {
        // Given: Opportunity detail ViewModel
        let opportunity = createMockOpportunities().first!
        let viewModel = OpportunityDetailViewModel(
            opportunity: opportunity,
            apiService: mockAPIService,
            analyticsService: mockAnalyticsService
        )
        
        mockAPIService.shouldLoadOpportunityDetailSucceed = true
        mockAPIService.mockOpportunityDetail = createMockOpportunityDetail()
        
        let expectation = XCTestExpectation(description: "Detail loaded")
        
        // When: Loading opportunity detail
        viewModel.loadOpportunityDetail()
        
        // Then: Should load additional details
        viewModel.$opportunityDetail
            .compactMap { $0 }
            .sink { detail in
                XCTAssertNotNil(detail.historicalData)
                XCTAssertNotNil(detail.relatedOpportunities)
                XCTAssertFalse(viewModel.isLoading)
                expectation.fulfill()
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testOpportunityDetailViewModel_AddToFavorites() throws {
        // Given: Opportunity detail ViewModel
        let opportunity = createMockOpportunities().first!
        let viewModel = OpportunityDetailViewModel(
            opportunity: opportunity,
            apiService: mockAPIService,
            analyticsService: mockAnalyticsService
        )
        
        mockAPIService.shouldAddToFavoritesSucceed = true
        
        let expectation = XCTestExpectation(description: "Added to favorites")
        
        // When: Adding to favorites
        viewModel.addToFavorites()
        
        // Then: Should add successfully
        viewModel.$isFavorite
            .dropFirst()
            .sink { isFavorite in
                if isFavorite {
                    XCTAssertTrue(self.mockAPIService.addToFavoritesCalled)
                    XCTAssertTrue(self.mockAnalyticsService.trackEventCalled)
                    expectation.fulfill()
                }
            }
            .store(in: &cancellables)
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testOpportunityDetailViewModel_ShareOpportunity() throws {
        // Given: Opportunity detail ViewModel
        let opportunity = createMockOpportunities().first!
        let viewModel = OpportunityDetailViewModel(
            opportunity: opportunity,
            apiService: mockAPIService,
            analyticsService: mockAnalyticsService
        )
        
        // When: Sharing opportunity
        let shareData = viewModel.getShareData()
        
        // Then: Should generate share content
        XCTAssertNotNil(shareData.title)
        XCTAssertNotNil(shareData.text)
        XCTAssertTrue(shareData.text.contains(opportunity.event))
        XCTAssertTrue(shareData.text.contains("\(opportunity.evPercentage)%"))
        XCTAssertTrue(mockAnalyticsService.trackEventCalled)
    }
    
    // MARK: - Performance Tests
    
    func testViewModelPerformance_OpportunityListFiltering() throws {
        // Given: ViewModel with large number of opportunities
        let viewModel = OpportunityListViewModel(
            apiService: mockAPIService,
            analyticsService: mockAnalyticsService
        )
        
        let largeOpportunityList = Array(0..<1000).map { index in
            BettingOpportunity(
                id: "opp_\(index)",
                event: "Event \(index)",
                betDescription: "Bet \(index)",
                betType: .moneyline,
                sport: index % 2 == 0 ? "NFL" : "NBA",
                evPercentage: Double(index % 20),
                bestOdds: "+150",
                fairOdds: "+120",
                bestSource: "DraftKings",
                gameTime: Date(),
                classification: .great
            )
        }
        
        viewModel.opportunities = largeOpportunityList
        
        // When: Filtering opportunities
        measure {
            viewModel.selectedSport = "NFL"
            viewModel.applyFilters()
            _ = viewModel.filteredOpportunities
        }
    }
    
    func testViewModelPerformance_OpportunityListSorting() throws {
        // Given: ViewModel with large number of opportunities
        let viewModel = OpportunityListViewModel(
            apiService: mockAPIService,
            analyticsService: mockAnalyticsService
        )
        
        let largeOpportunityList = Array(0..<1000).map { index in
            BettingOpportunity(
                id: "opp_\(index)",
                event: "Event \(index)",
                betDescription: "Bet \(index)",
                betType: .moneyline,
                sport: "NFL",
                evPercentage: Double.random(in: 0...25),
                bestOdds: "+150",
                fairOdds: "+120",
                bestSource: "DraftKings",
                gameTime: Date(),
                classification: .great
            )
        }
        
        viewModel.opportunities = largeOpportunityList
        
        // When: Sorting opportunities
        measure {
            viewModel.sortOption = .evPercentage
            viewModel.applySorting()
            _ = viewModel.sortedOpportunities
        }
    }
}

// MARK: - Test Utilities

extension ViewModelTests {
    
    func createMockOpportunities() -> [BettingOpportunity] {
        return [
            BettingOpportunity(
                id: "opp_1",
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
            ),
            BettingOpportunity(
                id: "opp_2",
                event: "Lakers vs Clippers",
                betDescription: "Lakers Moneyline",
                betType: .moneyline,
                sport: "NBA",
                evPercentage: 8.7,
                bestOdds: "+110",
                fairOdds: "+100",
                bestSource: "FanDuel",
                gameTime: Date().addingTimeInterval(7200),
                classification: .good
            ),
            BettingOpportunity(
                id: "opp_3",
                event: "Cowboys vs Giants",
                betDescription: "Cowboys -3.5",
                betType: .spread,
                sport: "NFL",
                evPercentage: 15.2,
                bestOdds: "-110",
                fairOdds: "-120",
                bestSource: "BetMGM",
                gameTime: Date().addingTimeInterval(86400),
                classification: .great
            )
        ]
    }
    
    func createMockUserProfile() -> UserProfile {
        return UserProfile(
            id: "user_123",
            email: "test@example.com",
            role: .premium,
            subscriptionStatus: .active,
            deviceId: "device_456",
            firstName: "John",
            lastName: "Doe",
            preferences: UserPreferences(
                evThreshold: 5.0,
                enabledSports: ["NFL", "NBA"],
                notificationsEnabled: true
            )
        )
    }
    
    func createMockIAPProducts() -> [IAPProduct] {
        return [
            IAPProduct(
                id: "com.fairedge.premium.monthly",
                displayName: "Premium Monthly",
                description: "Monthly premium subscription",
                price: 9.99,
                period: .monthly
            ),
            IAPProduct(
                id: "com.fairedge.premium.yearly",
                displayName: "Premium Yearly",
                description: "Yearly premium subscription",
                price: 99.99,
                period: .yearly
            )
        ]
    }
    
    func createMockOpportunityDetail() -> OpportunityDetail {
        return OpportunityDetail(
            opportunity: createMockOpportunities().first!,
            historicalData: HistoricalData(
                pastWeekEV: [8.5, 9.2, 11.1, 12.5],
                winRate: 0.67,
                averageOdds: "+140"
            ),
            relatedOpportunities: Array(createMockOpportunities().dropFirst()),
            bookmakerComparison: [
                BookmakerOdds(name: "DraftKings", odds: "+150", available: true),
                BookmakerOdds(name: "FanDuel", odds: "+145", available: true),
                BookmakerOdds(name: "BetMGM", odds: "+155", available: false)
            ]
        )
    }
}

// MARK: - Mock Services

class MockAnalyticsService {
    var trackEventCalled = false
    var setAnalyticsEnabledCalled = false
    
    func trackEvent(_ name: String, properties: [String: Any]? = nil) {
        trackEventCalled = true
    }
    
    func setAnalyticsEnabled(_ enabled: Bool) {
        setAnalyticsEnabledCalled = true
    }
}

class MockIAPService {
    var mockProducts: [IAPProduct] = []
    var shouldPurchaseSucceed = true
    var shouldRestoreSucceed = true
    var restorePurchasesCalled = false
    
    func loadProducts() async -> [IAPProduct] {
        return mockProducts
    }
    
    func purchaseProduct(_ product: IAPProduct) async throws -> PurchaseResult {
        if shouldPurchaseSucceed {
            return PurchaseResult(success: true, transactionId: "txn_123", receipt: "receipt_data")
        } else {
            throw IAPError.purchaseFailed
        }
    }
    
    func restorePurchases() async throws {
        restorePurchasesCalled = true
        if !shouldRestoreSucceed {
            throw IAPError.restoreFailed
        }
    }
}

// MARK: - Data Models

struct UserProfile {
    let id: String
    let email: String
    let role: UserRole
    let subscriptionStatus: SubscriptionStatus
    let deviceId: String
    let firstName: String?
    let lastName: String?
    let preferences: UserPreferences
}

struct UserPreferences {
    let evThreshold: Double
    let enabledSports: [String]
    let notificationsEnabled: Bool
}

struct NotificationSettings {
    let enabled: Bool
    let evThreshold: Double
    let enabledSports: [String]
    let quietHoursEnabled: Bool
}

struct AppSettings {
    let analyticsEnabled: Bool
    let crashReportingEnabled: Bool
    let theme: AppTheme
}

enum AppTheme {
    case light, dark, system
}

struct IAPProduct {
    let id: String
    let displayName: String
    let description: String
    let price: Double
    let period: SubscriptionPeriod
}

enum SubscriptionPeriod {
    case monthly, yearly
}

struct PurchaseResult {
    let success: Bool
    let transactionId: String?
    let receipt: String?
}

struct OpportunityDetail {
    let opportunity: BettingOpportunity
    let historicalData: HistoricalData
    let relatedOpportunities: [BettingOpportunity]
    let bookmakerComparison: [BookmakerOdds]
}

struct HistoricalData {
    let pastWeekEV: [Double]
    let winRate: Double
    let averageOdds: String
}

struct BookmakerOdds {
    let name: String
    let odds: String
    let available: Bool
}

struct ShareData {
    let title: String
    let text: String
    let url: URL?
}

// MARK: - Error Types

enum AuthenticationError: Error {
    case signInFailed, signOutFailed, invalidCredentials
}

enum IAPError: Error {
    case purchaseFailed, restoreFailed, productNotFound
}

enum APIError: Error {
    case networkError, invalidResponse, unauthorized
}

// MARK: - ViewModels (Simplified for Testing)

class OpportunityListViewModel: ObservableObject {
    @Published var opportunities: [BettingOpportunity] = []
    @Published var filteredOpportunities: [BettingOpportunity] = []
    @Published var sortedOpportunities: [BettingOpportunity] = []
    @Published var searchResults: [BettingOpportunity] = []
    @Published var isLoading = false
    @Published var isRefreshing = false
    @Published var errorMessage: String?
    @Published var searchText = "" {
        didSet { updateSearchResults() }
    }
    @Published var selectedSport: String? {
        didSet { applyFilters() }
    }
    @Published var sortOption: SortOption = .gameTime {
        didSet { applySorting() }
    }
    
    private let apiService: MockAPIService
    private let analyticsService: MockAnalyticsService
    
    init(apiService: MockAPIService, analyticsService: MockAnalyticsService) {
        self.apiService = apiService
        self.analyticsService = analyticsService
    }
    
    func loadOpportunities() {
        isLoading = true
        errorMessage = nil
        
        Task {
            do {
                let opportunities = try await apiService.loadOpportunities()
                await MainActor.run {
                    self.opportunities = opportunities
                    self.applyFilters()
                    self.applySorting()
                    self.isLoading = false
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
    
    func refreshOpportunities() {
        isRefreshing = true
        loadOpportunities()
        isRefreshing = false
    }
    
    func applyFilters() {
        if let selectedSport = selectedSport {
            filteredOpportunities = opportunities.filter { $0.sport == selectedSport }
        } else {
            filteredOpportunities = opportunities
        }
    }
    
    func applySorting() {
        switch sortOption {
        case .evPercentage:
            sortedOpportunities = filteredOpportunities.sorted { $0.evPercentage > $1.evPercentage }
        case .gameTime:
            sortedOpportunities = filteredOpportunities.sorted { $0.gameTime < $1.gameTime }
        }
    }
    
    private func updateSearchResults() {
        if searchText.isEmpty {
            searchResults = opportunities
        } else {
            searchResults = opportunities.filter { $0.event.localizedCaseInsensitiveContains(searchText) }
        }
    }
}

enum SortOption {
    case evPercentage, gameTime
}

class AuthenticationViewModel: ObservableObject {
    @Published var isAuthenticated = false
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var email = ""
    @Published var password = ""
    
    private let authService: MockAuthenticationService
    private let analyticsService: MockAnalyticsService
    
    init(authService: MockAuthenticationService, analyticsService: MockAnalyticsService) {
        self.authService = authService
        self.analyticsService = analyticsService
    }
    
    func signInWithApple() {
        isLoading = true
        errorMessage = nil
        
        Task {
            do {
                try await authService.signInWithApple()
                await MainActor.run {
                    self.isAuthenticated = true
                    self.isLoading = false
                    self.analyticsService.trackEvent("sign_in_success")
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
    
    func signOut() {
        Task {
            do {
                try await authService.signOut()
                await MainActor.run {
                    self.isAuthenticated = false
                    self.analyticsService.trackEvent("sign_out")
                }
            } catch {
                // Handle sign out error
            }
        }
    }
    
    func isFormValid() -> Bool {
        return email.isValidEmail && password.count >= 8
    }
}

class UserProfileViewModel: ObservableObject {
    @Published var userProfile: UserProfile?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var profileUpdateSuccess = false
    @Published var accountDeleted = false
    
    private let apiService: MockAPIService
    private let authService: MockAuthenticationService
    private let analyticsService: MockAnalyticsService
    
    init(apiService: MockAPIService, authService: MockAuthenticationService, analyticsService: MockAnalyticsService) {
        self.apiService = apiService
        self.authService = authService
        self.analyticsService = analyticsService
    }
    
    func loadProfile() {
        isLoading = true
        
        Task {
            do {
                let profile = try await apiService.loadUserProfile()
                await MainActor.run {
                    self.userProfile = profile
                    self.isLoading = false
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
    
    func updateProfile() {
        guard let profile = userProfile else { return }
        
        Task {
            do {
                try await apiService.updateUserProfile(profile)
                await MainActor.run {
                    self.profileUpdateSuccess = true
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                }
            }
        }
    }
    
    func deleteAccount() {
        Task {
            do {
                try await apiService.deleteAccount()
                try await authService.signOut()
                await MainActor.run {
                    self.accountDeleted = true
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                }
            }
        }
    }
}

class SubscriptionViewModel: ObservableObject {
    @Published var availableProducts: [IAPProduct] = []
    @Published var isLoading = false
    @Published var isPurchasing = false
    @Published var purchaseSuccess = false
    @Published var restoreSuccess = false
    @Published var errorMessage: String?
    
    let iapService: MockIAPService
    private let apiService: MockAPIService
    private let analyticsService: MockAnalyticsService
    
    init(apiService: MockAPIService, iapService: MockIAPService, analyticsService: MockAnalyticsService) {
        self.apiService = apiService
        self.iapService = iapService
        self.analyticsService = analyticsService
    }
    
    func loadProducts() {
        isLoading = true
        
        Task {
            let products = await iapService.loadProducts()
            await MainActor.run {
                self.availableProducts = products
                self.isLoading = false
            }
        }
    }
    
    func purchaseProduct(_ product: IAPProduct) {
        isPurchasing = true
        
        Task {
            do {
                let result = try await iapService.purchaseProduct(product)
                if result.success {
                    try await apiService.validateReceipt(result.receipt!)
                    await MainActor.run {
                        self.purchaseSuccess = true
                        self.isPurchasing = false
                        self.analyticsService.trackEvent("purchase_success")
                    }
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isPurchasing = false
                }
            }
        }
    }
    
    func restorePurchases() {
        Task {
            do {
                try await iapService.restorePurchases()
                await MainActor.run {
                    self.restoreSuccess = true
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                }
            }
        }
    }
}

class SettingsViewModel: ObservableObject {
    @Published var notificationSettings: NotificationSettings?
    @Published var appSettings: AppSettings?
    @Published var isLoading = false
    
    private let analyticsService: MockAnalyticsService
    
    init(analyticsService: MockAnalyticsService) {
        self.analyticsService = analyticsService
    }
    
    func loadSettings() {
        isLoading = true
        
        // Load default settings
        notificationSettings = NotificationSettings(
            enabled: true,
            evThreshold: 5.0,
            enabledSports: ["NFL", "NBA"],
            quietHoursEnabled: false
        )
        
        appSettings = AppSettings(
            analyticsEnabled: true,
            crashReportingEnabled: true,
            theme: .system
        )
        
        isLoading = false
    }
    
    func updateNotificationSettings(_ settings: NotificationSettings) {
        notificationSettings = settings
        analyticsService.trackEvent("notification_settings_updated")
    }
    
    func toggleAnalytics() {
        guard let settings = appSettings else { return }
        
        appSettings = AppSettings(
            analyticsEnabled: !settings.analyticsEnabled,
            crashReportingEnabled: settings.crashReportingEnabled,
            theme: settings.theme
        )
        
        analyticsService.setAnalyticsEnabled(appSettings!.analyticsEnabled)
    }
}

class OpportunityDetailViewModel: ObservableObject {
    @Published var opportunityDetail: OpportunityDetail?
    @Published var isLoading = false
    @Published var isFavorite = false
    @Published var errorMessage: String?
    
    let opportunity: BettingOpportunity
    private let apiService: MockAPIService
    private let analyticsService: MockAnalyticsService
    
    init(opportunity: BettingOpportunity, apiService: MockAPIService, analyticsService: MockAnalyticsService) {
        self.opportunity = opportunity
        self.apiService = apiService
        self.analyticsService = analyticsService
    }
    
    func loadOpportunityDetail() {
        isLoading = true
        
        Task {
            do {
                let detail = try await apiService.loadOpportunityDetail(opportunity.id)
                await MainActor.run {
                    self.opportunityDetail = detail
                    self.isLoading = false
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
    
    func addToFavorites() {
        Task {
            do {
                try await apiService.addToFavorites(opportunity.id)
                await MainActor.run {
                    self.isFavorite = true
                    self.analyticsService.trackEvent("opportunity_favorited")
                }
            } catch {
                await MainActor.run {
                    self.errorMessage = error.localizedDescription
                }
            }
        }
    }
    
    func getShareData() -> ShareData {
        analyticsService.trackEvent("opportunity_shared")
        
        return ShareData(
            title: "Fair-Edge Betting Opportunity",
            text: "\(opportunity.event) - \(opportunity.betDescription) (\(opportunity.bestOdds), \(opportunity.evPercentage)% EV)",
            url: URL(string: "https://fair-edge.com/opportunity/\(opportunity.id)")
        )
    }
}