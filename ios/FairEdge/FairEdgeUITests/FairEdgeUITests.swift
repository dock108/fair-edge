//
//  FairEdgeUITests.swift
//  FairEdgeUITests
//
//  UI tests for Fair-Edge iOS app
//  Tests complete user flows, navigation, and UI interactions

import XCTest

final class FairEdgeUITests: XCTestCase {
    
    // MARK: - Properties
    
    var app: XCUIApplication!
    
    // MARK: - Setup & Teardown
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        // Initialize application
        app = XCUIApplication()
        
        // Configure test environment
        app.launchArguments.append("--uitesting")
        app.launchEnvironment["ENABLE_TESTING"] = "1"
        app.launchEnvironment["MOCK_DATA"] = "1"
        
        // Continue after failure for comprehensive testing
        continueAfterFailure = false
        
        // Launch the app
        app.launch()
    }
    
    override func tearDownWithError() throws {
        app.terminate()
        app = nil
        try super.tearDownWithError()
    }
    
    // MARK: - App Launch and Initial State Tests
    
    func testAppLaunch() throws {
        // Then: App should launch successfully
        XCTAssertTrue(app.exists)
        
        // Should show splash screen or onboarding
        let splashScreen = app.otherElements["splashScreen"]
        let onboardingScreen = app.otherElements["onboardingScreen"]
        
        XCTAssertTrue(splashScreen.exists || onboardingScreen.exists)
    }
    
    func testOnboardingFlow() throws {
        // Given: First time user
        if app.buttons["getStartedButton"].exists {
            
            // When: Tapping through onboarding
            app.buttons["getStartedButton"].tap()
            
            // Then: Should show onboarding screens
            XCTAssertTrue(app.staticTexts["Welcome to Fair-Edge"].exists)
            
            // Navigate through onboarding
            app.buttons["nextButton"].tap()
            XCTAssertTrue(app.staticTexts["Find Betting Opportunities"].exists)
            
            app.buttons["nextButton"].tap()
            XCTAssertTrue(app.staticTexts["Get Premium Insights"].exists)
            
            app.buttons["finishButton"].tap()
            
            // Should reach main screen
            XCTAssertTrue(app.tabBars.element.exists)
        }
    }
    
    func testSkipOnboarding() throws {
        // Given: Onboarding screen
        if app.buttons["skipButton"].exists {
            
            // When: Skipping onboarding
            app.buttons["skipButton"].tap()
            
            // Then: Should reach main screen
            XCTAssertTrue(app.tabBars.element.exists)
        }
    }
    
    // MARK: - Authentication Tests
    
    func testSignInWithApple() throws {
        // Given: Not authenticated user
        navigateToAuthenticationIfNeeded()
        
        // When: Tapping Sign in with Apple
        let signInButton = app.buttons["signInWithAppleButton"]
        XCTAssertTrue(signInButton.exists)
        signInButton.tap()
        
        // Note: In UI tests, we can't actually test Apple Sign In
        // We would mock this in the test environment
        
        // Then: Should show loading state
        let loadingIndicator = app.activityIndicators["authLoadingIndicator"]
        XCTAssertTrue(loadingIndicator.exists)
    }
    
    func testSignInFormValidation() throws {
        // Given: Authentication screen
        navigateToAuthenticationIfNeeded()
        
        // When: Entering invalid email
        let emailField = app.textFields["emailTextField"]
        emailField.tap()
        emailField.typeText("invalid-email")
        
        let passwordField = app.secureTextFields["passwordTextField"]
        passwordField.tap()
        passwordField.typeText("short")
        
        let signInButton = app.buttons["signInButton"]
        signInButton.tap()
        
        // Then: Should show validation errors
        XCTAssertTrue(app.staticTexts["Invalid email format"].exists)
        XCTAssertTrue(app.staticTexts["Password must be at least 8 characters"].exists)
    }
    
    func testSignOut() throws {
        // Given: Authenticated user
        authenticateUser()
        
        // When: Navigating to profile and signing out
        app.tabBars.buttons["Profile"].tap()
        
        let settingsButton = app.buttons["settingsButton"]
        settingsButton.tap()
        
        let signOutButton = app.buttons["signOutButton"]
        signOutButton.tap()
        
        // Confirm sign out
        app.alerts.buttons["Sign Out"].tap()
        
        // Then: Should return to authentication screen
        XCTAssertTrue(app.buttons["signInWithAppleButton"].exists)
    }
    
    // MARK: - Opportunities List Tests
    
    func testOpportunitiesListLoad() throws {
        // Given: Authenticated user
        authenticateUser()
        
        // When: Viewing opportunities list
        app.tabBars.buttons["Opportunities"].tap()
        
        // Then: Should load opportunities
        let opportunitiesList = app.collectionViews["opportunitiesList"]
        XCTAssertTrue(opportunitiesList.exists)
        
        // Should have at least one opportunity
        let firstOpportunity = opportunitiesList.cells.element(boundBy: 0)
        XCTAssertTrue(firstOpportunity.exists)
        
        // Should show opportunity details
        XCTAssertTrue(firstOpportunity.staticTexts.matching(identifier: "eventLabel").firstMatch.exists)
        XCTAssertTrue(firstOpportunity.staticTexts.matching(identifier: "evLabel").firstMatch.exists)
    }
    
    func testOpportunitiesListRefresh() throws {
        // Given: Opportunities list
        authenticateUser()
        app.tabBars.buttons["Opportunities"].tap()
        
        let opportunitiesList = app.collectionViews["opportunitiesList"]
        
        // When: Pull to refresh
        opportunitiesList.swipeDown()
        
        // Then: Should show refresh indicator
        let refreshIndicator = app.activityIndicators["refreshIndicator"]
        XCTAssertTrue(refreshIndicator.exists)
        
        // Wait for refresh to complete
        let refreshCompleted = refreshIndicator.waitForNonExistence(timeout: 10)
        XCTAssertTrue(refreshCompleted)
    }
    
    func testOpportunitiesFilter() throws {
        // Given: Opportunities list
        authenticateUser()
        app.tabBars.buttons["Opportunities"].tap()
        
        // When: Opening filter
        let filterButton = app.buttons["filterButton"]
        filterButton.tap()
        
        // Then: Should show filter options
        XCTAssertTrue(app.sheets["filterSheet"].exists)
        
        // When: Selecting NFL filter
        app.buttons["filterNFL"].tap()
        app.buttons["applyFilterButton"].tap()
        
        // Then: Should filter opportunities
        let opportunitiesList = app.collectionViews["opportunitiesList"]
        let filteredOpportunities = opportunitiesList.cells
        
        // Verify all visible opportunities are NFL
        for i in 0..<min(filteredOpportunities.count, 5) {
            let cell = filteredOpportunities.element(boundBy: i)
            XCTAssertTrue(cell.staticTexts["NFL"].exists)
        }
    }
    
    func testOpportunitiesSearch() throws {
        // Given: Opportunities list
        authenticateUser()
        app.tabBars.buttons["Opportunities"].tap()
        
        // When: Using search
        let searchField = app.searchFields["searchOpportunities"]
        searchField.tap()
        searchField.typeText("Lakers")
        
        // Then: Should filter search results
        let opportunitiesList = app.collectionViews["opportunitiesList"]
        let searchResults = opportunitiesList.cells
        
        // Verify search results contain "Lakers"
        if searchResults.count > 0 {
            let firstResult = searchResults.element(boundBy: 0)
            XCTAssertTrue(firstResult.staticTexts.containing(NSPredicate(format: "label CONTAINS 'Lakers'")).firstMatch.exists)
        }
    }
    
    func testOpportunityTap() throws {
        // Given: Opportunities list
        authenticateUser()
        app.tabBars.buttons["Opportunities"].tap()
        
        let opportunitiesList = app.collectionViews["opportunitiesList"]
        let firstOpportunity = opportunitiesList.cells.element(boundBy: 0)
        
        // When: Tapping on opportunity
        firstOpportunity.tap()
        
        // Then: Should navigate to opportunity detail
        XCTAssertTrue(app.navigationBars["Opportunity Detail"].exists)
        XCTAssertTrue(app.staticTexts["eventDetailLabel"].exists)
        XCTAssertTrue(app.staticTexts["betDescriptionLabel"].exists)
        XCTAssertTrue(app.staticTexts["oddsLabel"].exists)
    }
    
    // MARK: - Opportunity Detail Tests
    
    func testOpportunityDetailDisplay() throws {
        // Given: Opportunity detail screen
        navigateToOpportunityDetail()
        
        // Then: Should display all opportunity information
        XCTAssertTrue(app.staticTexts["eventDetailLabel"].exists)
        XCTAssertTrue(app.staticTexts["betDescriptionLabel"].exists)
        XCTAssertTrue(app.staticTexts["sportLabel"].exists)
        XCTAssertTrue(app.staticTexts["evPercentageLabel"].exists)
        XCTAssertTrue(app.staticTexts["bestOddsLabel"].exists)
        XCTAssertTrue(app.staticTexts["fairOddsLabel"].exists)
        XCTAssertTrue(app.staticTexts["bestSourceLabel"].exists)
        XCTAssertTrue(app.staticTexts["gameTimeLabel"].exists)
    }
    
    func testAddToFavorites() throws {
        // Given: Opportunity detail screen
        navigateToOpportunityDetail()
        
        // When: Tapping favorite button
        let favoriteButton = app.buttons["favoriteButton"]
        favoriteButton.tap()
        
        // Then: Should show favorite state
        XCTAssertTrue(app.buttons["favoriteButtonFilled"].exists)
        
        // Should show success message
        XCTAssertTrue(app.staticTexts["Added to favorites"].exists)
    }
    
    func testShareOpportunity() throws {
        // Given: Opportunity detail screen
        navigateToOpportunityDetail()
        
        // When: Tapping share button
        let shareButton = app.buttons["shareButton"]
        shareButton.tap()
        
        // Then: Should show share sheet
        XCTAssertTrue(app.sheets["shareSheet"].exists)
        
        // Cancel share
        app.buttons["Cancel"].tap()
    }
    
    func testOpportunityDetailBookmakerComparison() throws {
        // Given: Opportunity detail screen
        navigateToOpportunityDetail()
        
        // When: Scrolling to bookmaker comparison
        app.scrollViews.element.swipeUp()
        
        // Then: Should show bookmaker comparison
        XCTAssertTrue(app.staticTexts["Bookmaker Comparison"].exists)
        
        let bookmakerList = app.collectionViews["bookmakerComparisonList"]
        XCTAssertTrue(bookmakerList.exists)
        
        // Should have at least one bookmaker
        XCTAssertTrue(bookmakerList.cells.count > 0)
    }
    
    // MARK: - Profile Tests
    
    func testProfileDisplay() throws {
        // Given: Authenticated user
        authenticateUser()
        
        // When: Viewing profile
        app.tabBars.buttons["Profile"].tap()
        
        // Then: Should display user information
        XCTAssertTrue(app.staticTexts["userNameLabel"].exists)
        XCTAssertTrue(app.staticTexts["userEmailLabel"].exists)
        XCTAssertTrue(app.staticTexts["subscriptionStatusLabel"].exists)
        
        // Should show profile actions
        XCTAssertTrue(app.buttons["editProfileButton"].exists)
        XCTAssertTrue(app.buttons["settingsButton"].exists)
        XCTAssertTrue(app.buttons["subscriptionButton"].exists)
    }
    
    func testEditProfile() throws {
        // Given: Profile screen
        authenticateUser()
        app.tabBars.buttons["Profile"].tap()
        
        // When: Editing profile
        app.buttons["editProfileButton"].tap()
        
        // Then: Should show edit form
        XCTAssertTrue(app.navigationBars["Edit Profile"].exists)
        
        let firstNameField = app.textFields["firstNameTextField"]
        let lastNameField = app.textFields["lastNameTextField"]
        
        // Update fields
        firstNameField.tap()
        firstNameField.clearAndEnterText("John")
        
        lastNameField.tap()
        lastNameField.clearAndEnterText("Doe")
        
        // Save changes
        app.buttons["saveButton"].tap()
        
        // Should return to profile
        XCTAssertTrue(app.staticTexts["Profile"].exists)
        XCTAssertTrue(app.staticTexts["John Doe"].exists)
    }
    
    // MARK: - Settings Tests
    
    func testSettingsDisplay() throws {
        // Given: Profile screen
        authenticateUser()
        app.tabBars.buttons["Profile"].tap()
        
        // When: Opening settings
        app.buttons["settingsButton"].tap()
        
        // Then: Should display settings options
        XCTAssertTrue(app.navigationBars["Settings"].exists)
        XCTAssertTrue(app.staticTexts["Notifications"].exists)
        XCTAssertTrue(app.staticTexts["Privacy"].exists)
        XCTAssertTrue(app.staticTexts["About"].exists)
    }
    
    func testNotificationSettings() throws {
        // Given: Settings screen
        navigateToSettings()
        
        // When: Tapping notification settings
        app.staticTexts["Notifications"].tap()
        
        // Then: Should show notification options
        XCTAssertTrue(app.navigationBars["Notification Settings"].exists)
        
        let pushNotificationsSwitch = app.switches["pushNotificationsSwitch"]
        let evThresholdSlider = app.sliders["evThresholdSlider"]
        
        XCTAssertTrue(pushNotificationsSwitch.exists)
        XCTAssertTrue(evThresholdSlider.exists)
        
        // Toggle notifications
        pushNotificationsSwitch.tap()
        
        // Adjust EV threshold
        evThresholdSlider.adjust(toNormalizedSliderPosition: 0.7)
        
        // Save settings
        app.buttons["saveButton"].tap()
    }
    
    func testPrivacySettings() throws {
        // Given: Settings screen
        navigateToSettings()
        
        // When: Tapping privacy settings
        app.staticTexts["Privacy"].tap()
        
        // Then: Should show privacy options
        XCTAssertTrue(app.navigationBars["Privacy Settings"].exists)
        
        let analyticsSwitch = app.switches["analyticsSwitch"]
        let crashReportingSwitch = app.switches["crashReportingSwitch"]
        
        XCTAssertTrue(analyticsSwitch.exists)
        XCTAssertTrue(crashReportingSwitch.exists)
        
        // Toggle analytics
        analyticsSwitch.tap()
        
        // Should show confirmation alert
        XCTAssertTrue(app.alerts["Disable Analytics?"].exists)
        app.alerts.buttons["Confirm"].tap()
    }
    
    // MARK: - Subscription Tests
    
    func testSubscriptionScreen() throws {
        // Given: Profile screen
        authenticateUser()
        app.tabBars.buttons["Profile"].tap()
        
        // When: Tapping subscription
        app.buttons["subscriptionButton"].tap()
        
        // Then: Should show subscription options
        XCTAssertTrue(app.navigationBars["Subscription"].exists)
        XCTAssertTrue(app.staticTexts["Choose Your Plan"].exists)
        
        // Should show subscription plans
        let monthlyPlan = app.buttons["monthlyPlanButton"]
        let yearlyPlan = app.buttons["yearlyPlanButton"]
        
        XCTAssertTrue(monthlyPlan.exists)
        XCTAssertTrue(yearlyPlan.exists)
        
        // Should show plan details
        XCTAssertTrue(app.staticTexts["$9.99/month"].exists)
        XCTAssertTrue(app.staticTexts["$99.99/year"].exists)
    }
    
    func testSubscriptionPurchase() throws {
        // Given: Subscription screen
        navigateToSubscription()
        
        // When: Selecting monthly plan
        let monthlyPlan = app.buttons["monthlyPlanButton"]
        monthlyPlan.tap()
        
        // Then: Should show purchase confirmation
        XCTAssertTrue(app.alerts["Confirm Purchase"].exists)
        app.alerts.buttons["Purchase"].tap()
        
        // Should show processing state
        let processingIndicator = app.activityIndicators["purchaseProcessingIndicator"]
        XCTAssertTrue(processingIndicator.exists)
        
        // Note: In UI tests, IAP would be mocked
    }
    
    func testRestorePurchases() throws {
        // Given: Subscription screen
        navigateToSubscription()
        
        // When: Tapping restore purchases
        let restoreButton = app.buttons["restorePurchasesButton"]
        restoreButton.tap()
        
        // Then: Should show restore process
        let processingIndicator = app.activityIndicators["restoreProcessingIndicator"]
        XCTAssertTrue(processingIndicator.exists)
    }
    
    // MARK: - Navigation Tests
    
    func testTabBarNavigation() throws {
        // Given: Authenticated user
        authenticateUser()
        
        // When: Tapping each tab
        let tabBar = app.tabBars.element
        
        // Opportunities tab
        tabBar.buttons["Opportunities"].tap()
        XCTAssertTrue(app.navigationBars["Opportunities"].exists)
        
        // Favorites tab
        tabBar.buttons["Favorites"].tap()
        XCTAssertTrue(app.navigationBars["Favorites"].exists)
        
        // Profile tab
        tabBar.buttons["Profile"].tap()
        XCTAssertTrue(app.navigationBars["Profile"].exists)
        
        // Then: All tabs should be accessible
        XCTAssertTrue(tabBar.exists)
    }
    
    func testNavigationBackButton() throws {
        // Given: Opportunity detail screen
        navigateToOpportunityDetail()
        
        // When: Tapping back button
        app.navigationBars.buttons.element(boundBy: 0).tap()
        
        // Then: Should return to opportunities list
        XCTAssertTrue(app.navigationBars["Opportunities"].exists)
    }
    
    // MARK: - Error Handling Tests
    
    func testNetworkErrorHandling() throws {
        // Given: App with network error simulation
        app.launchEnvironment["SIMULATE_NETWORK_ERROR"] = "1"
        app.terminate()
        app.launch()
        
        authenticateUser()
        
        // When: Trying to load opportunities
        app.tabBars.buttons["Opportunities"].tap()
        
        // Then: Should show error message
        XCTAssertTrue(app.staticTexts["Network Error"].exists)
        XCTAssertTrue(app.buttons["retryButton"].exists)
        
        // When: Tapping retry
        app.buttons["retryButton"].tap()
        
        // Should attempt to reload
        let loadingIndicator = app.activityIndicators["loadingIndicator"]
        XCTAssertTrue(loadingIndicator.exists)
    }
    
    func testEmptyStateDisplay() throws {
        // Given: App with no opportunities
        app.launchEnvironment["EMPTY_OPPORTUNITIES"] = "1"
        app.terminate()
        app.launch()
        
        authenticateUser()
        
        // When: Viewing opportunities
        app.tabBars.buttons["Opportunities"].tap()
        
        // Then: Should show empty state
        XCTAssertTrue(app.staticTexts["No opportunities available"].exists)
        XCTAssertTrue(app.buttons["refreshButton"].exists)
    }
    
    // MARK: - Accessibility Tests
    
    func testAccessibilityLabels() throws {
        // Given: Authenticated user on opportunities screen
        authenticateUser()
        app.tabBars.buttons["Opportunities"].tap()
        
        // Then: All important elements should have accessibility labels
        let opportunitiesList = app.collectionViews["opportunitiesList"]
        let firstOpportunity = opportunitiesList.cells.element(boundBy: 0)
        
        XCTAssertNotNil(firstOpportunity.accessibilityLabel)
        XCTAssertNotNil(app.buttons["filterButton"].accessibilityLabel)
        XCTAssertNotNil(app.searchFields["searchOpportunities"].accessibilityLabel)
    }
    
    func testVoiceOverNavigation() throws {
        // Given: VoiceOver enabled
        app.launchEnvironment["VOICEOVER_ENABLED"] = "1"
        app.terminate()
        app.launch()
        
        authenticateUser()
        
        // When: Navigating with VoiceOver
        // Note: This would require more sophisticated VoiceOver testing
        // which is typically done with specific accessibility testing frameworks
        
        // Then: Elements should be properly announced
        let opportunitiesTab = app.tabBars.buttons["Opportunities"]
        XCTAssertTrue(opportunitiesTab.exists)
        XCTAssertTrue(opportunitiesTab.isAccessibilityElement)
    }
    
    // MARK: - Performance Tests
    
    func testLaunchPerformance() throws {
        // Measure app launch time
        measure(metrics: [XCTApplicationLaunchMetric()]) {
            XCUIApplication().launch()
        }
    }
    
    func testScrollPerformance() throws {
        // Given: Large list of opportunities
        authenticateUser()
        app.tabBars.buttons["Opportunities"].tap()
        
        let opportunitiesList = app.collectionViews["opportunitiesList"]
        
        // When: Scrolling through list
        measure(metrics: [XCTOSSignpostMetric.scrollingAndDecelerationMetric]) {
            opportunitiesList.swipeUp()
            opportunitiesList.swipeUp()
            opportunitiesList.swipeUp()
            opportunitiesList.swipeDown()
            opportunitiesList.swipeDown()
            opportunitiesList.swipeDown()
        }
    }
    
    // MARK: - Helper Methods
    
    private func navigateToAuthenticationIfNeeded() {
        // If not on authentication screen, navigate there
        if !app.buttons["signInWithAppleButton"].exists {
            // App might be logged in or on onboarding
            if app.buttons["skipButton"].exists {
                app.buttons["skipButton"].tap()
            }
            
            // If logged in, sign out first
            if app.tabBars.element.exists {
                app.tabBars.buttons["Profile"].tap()
                app.buttons["settingsButton"].tap()
                app.buttons["signOutButton"].tap()
                app.alerts.buttons["Sign Out"].tap()
            }
        }
    }
    
    private func authenticateUser() {
        // For UI testing, we mock authentication
        if app.buttons["signInWithAppleButton"].exists {
            app.buttons["signInWithAppleButton"].tap()
            
            // Wait for authentication to complete (mocked)
            let authenticated = app.tabBars.element.waitForExistence(timeout: 10)
            XCTAssertTrue(authenticated, "Authentication failed")
        }
    }
    
    private func navigateToOpportunityDetail() {
        authenticateUser()
        app.tabBars.buttons["Opportunities"].tap()
        
        let opportunitiesList = app.collectionViews["opportunitiesList"]
        let firstOpportunity = opportunitiesList.cells.element(boundBy: 0)
        firstOpportunity.tap()
        
        XCTAssertTrue(app.navigationBars["Opportunity Detail"].exists)
    }
    
    private func navigateToSettings() {
        authenticateUser()
        app.tabBars.buttons["Profile"].tap()
        app.buttons["settingsButton"].tap()
        
        XCTAssertTrue(app.navigationBars["Settings"].exists)
    }
    
    private func navigateToSubscription() {
        authenticateUser()
        app.tabBars.buttons["Profile"].tap()
        app.buttons["subscriptionButton"].tap()
        
        XCTAssertTrue(app.navigationBars["Subscription"].exists)
    }
}

// MARK: - XCUIElement Extensions

extension XCUIElement {
    func clearAndEnterText(_ text: String) {
        guard let stringValue = self.value as? String else {
            XCTFail("Tried to clear and enter text into a non string value")
            return
        }
        
        self.tap()
        
        let deleteString = String(repeating: XCUIKeyboardKey.delete.rawValue, count: stringValue.count)
        self.typeText(deleteString)
        self.typeText(text)
    }
}

// MARK: - Additional UI Test Classes

class FairEdgeUIAccessibilityTests: XCTestCase {
    
    var app: XCUIApplication!
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        app = XCUIApplication()
        app.launchArguments.append("--uitesting")
        app.launchEnvironment["ENABLE_TESTING"] = "1"
        continueAfterFailure = false
        app.launch()
    }
    
    func testDynamicTypeSupport() throws {
        // Test app behavior with different text sizes
        app.launchEnvironment["DYNAMIC_TYPE_SIZE"] = "extraLarge"
        app.terminate()
        app.launch()
        
        // Verify text is properly sized and layout is not broken
        // This would require specific layout validation
    }
    
    func testHighContrastSupport() throws {
        // Test app with high contrast mode
        app.launchEnvironment["HIGH_CONTRAST"] = "1"
        app.terminate()
        app.launch()
        
        // Verify colors and contrast meet accessibility standards
    }
    
    func testReduceMotionSupport() throws {
        // Test app with reduced motion
        app.launchEnvironment["REDUCE_MOTION"] = "1"
        app.terminate()
        app.launch()
        
        // Verify animations are reduced or disabled
    }
}

class FairEdgeUIPerformanceTests: XCTestCase {
    
    var app: XCUIApplication!
    
    override func setUpWithError() throws {
        try super.setUpWithError()
        
        app = XCUIApplication()
        app.launchArguments.append("--uitesting")
        app.launchEnvironment["ENABLE_TESTING"] = "1"
        continueAfterFailure = false
    }
    
    func testAppLaunchPerformance() throws {
        measure(metrics: [XCTApplicationLaunchMetric()]) {
            app.launch()
            app.terminate()
        }
    }
    
    func testMemoryUsage() throws {
        app.launch()
        
        measure(metrics: [XCTMemoryMetric()]) {
            // Perform memory-intensive operations
            let tabBar = app.tabBars.element
            
            for _ in 0..<10 {
                tabBar.buttons["Opportunities"].tap()
                tabBar.buttons["Favorites"].tap()
                tabBar.buttons["Profile"].tap()
            }
        }
    }
    
    func testScrollingPerformance() throws {
        app.launch()
        
        // Navigate to opportunities list
        let tabBar = app.tabBars.element
        if tabBar.waitForExistence(timeout: 10) {
            tabBar.buttons["Opportunities"].tap()
            
            let opportunitiesList = app.collectionViews["opportunitiesList"]
            
            measure(metrics: [XCTOSSignpostMetric.scrollingAndDecelerationMetric]) {
                for _ in 0..<5 {
                    opportunitiesList.swipeUp()
                }
                for _ in 0..<5 {
                    opportunitiesList.swipeDown()
                }
            }
        }
    }
}