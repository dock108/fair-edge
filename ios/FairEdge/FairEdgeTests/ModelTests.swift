//
//  ModelTests.swift
//  FairEdgeTests
//
//  Unit tests for iOS data models
//  Tests model validation, serialization, and business logic

import XCTest
@testable import FairEdge

class ModelTests: XCTestCase {
    
    // MARK: - User Model Tests
    
    func testUserModel_Initialization() throws {
        // Given: User data
        let userID = "user_12345"
        let email = "test@fair-edge.com"
        let role = UserRole.premium
        let subscriptionStatus = SubscriptionStatus.active
        let deviceID = "device_67890"
        
        // When: Creating user model
        let user = User(
            id: userID,
            email: email,
            role: role,
            subscriptionStatus: subscriptionStatus,
            deviceId: deviceID
        )
        
        // Then: Should initialize correctly
        XCTAssertEqual(user.id, userID)
        XCTAssertEqual(user.email, email)
        XCTAssertEqual(user.role, role)
        XCTAssertEqual(user.subscriptionStatus, subscriptionStatus)
        XCTAssertEqual(user.deviceId, deviceID)
    }
    
    func testUserModel_RolePermissions() throws {
        // Given: Users with different roles
        let freeUser = User(id: "1", email: "free@test.com", role: .free, subscriptionStatus: .none, deviceId: "device1")
        let basicUser = User(id: "2", email: "basic@test.com", role: .basic, subscriptionStatus: .active, deviceId: "device2")
        let premiumUser = User(id: "3", email: "premium@test.com", role: .premium, subscriptionStatus: .active, deviceId: "device3")
        let adminUser = User(id: "4", email: "admin@test.com", role: .admin, subscriptionStatus: .active, deviceId: "device4")
        
        // When: Checking permissions
        // Then: Should have correct permissions
        XCTAssertFalse(freeUser.canAccessPremiumFeatures)
        XCTAssertFalse(freeUser.canExportData)
        XCTAssertTrue(freeUser.canViewBasicOpportunities)
        
        XCTAssertFalse(basicUser.canAccessPremiumFeatures)
        XCTAssertFalse(basicUser.canExportData)
        XCTAssertTrue(basicUser.canViewBasicOpportunities)
        XCTAssertTrue(basicUser.canSearchOpportunities)
        
        XCTAssertTrue(premiumUser.canAccessPremiumFeatures)
        XCTAssertTrue(premiumUser.canExportData)
        XCTAssertTrue(premiumUser.canViewBasicOpportunities)
        XCTAssertTrue(premiumUser.canSearchOpportunities)
        
        XCTAssertTrue(adminUser.canAccessPremiumFeatures)
        XCTAssertTrue(adminUser.canExportData)
        XCTAssertTrue(adminUser.canViewBasicOpportunities)
        XCTAssertTrue(adminUser.isAdmin)
    }
    
    func testUserModel_SubscriptionValidation() throws {
        // Given: User with active subscription
        let activeUser = User(id: "1", email: "test@test.com", role: .premium, subscriptionStatus: .active, deviceId: "device1")
        let expiredUser = User(id: "2", email: "test2@test.com", role: .premium, subscriptionStatus: .expired, deviceId: "device2")
        let trialUser = User(id: "3", email: "test3@test.com", role: .premium, subscriptionStatus: .trialing, deviceId: "device3")
        
        // When: Checking subscription status
        // Then: Should validate correctly
        XCTAssertTrue(activeUser.hasActiveSubscription)
        XCTAssertFalse(expiredUser.hasActiveSubscription)
        XCTAssertTrue(trialUser.hasActiveSubscription)
        
        XCTAssertTrue(activeUser.canAccessPremiumFeatures)
        XCTAssertFalse(expiredUser.canAccessPremiumFeatures)
        XCTAssertTrue(trialUser.canAccessPremiumFeatures)
    }
    
    func testUserModel_JSONSerialization() throws {
        // Given: User model
        let user = User(
            id: "user_123",
            email: "test@fair-edge.com",
            role: .premium,
            subscriptionStatus: .active,
            deviceId: "device_456"
        )
        
        // When: Encoding to JSON
        let encoder = JSONEncoder()
        let jsonData = try encoder.encode(user)
        
        // Then: Should encode successfully
        XCTAssertNotNil(jsonData)
        
        // When: Decoding from JSON
        let decoder = JSONDecoder()
        let decodedUser = try decoder.decode(User.self, from: jsonData)
        
        // Then: Should decode correctly
        XCTAssertEqual(decodedUser.id, user.id)
        XCTAssertEqual(decodedUser.email, user.email)
        XCTAssertEqual(decodedUser.role, user.role)
        XCTAssertEqual(decodedUser.subscriptionStatus, user.subscriptionStatus)
        XCTAssertEqual(decodedUser.deviceId, user.deviceId)
    }
    
    // MARK: - BettingOpportunity Model Tests
    
    func testBettingOpportunityModel_Initialization() throws {
        // Given: Opportunity data
        let opportunity = BettingOpportunity(
            id: "opp_123",
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
        
        // Then: Should initialize correctly
        XCTAssertEqual(opportunity.id, "opp_123")
        XCTAssertEqual(opportunity.event, "Lakers vs Warriors")
        XCTAssertEqual(opportunity.betDescription, "LeBron Points Over 25.5")
        XCTAssertEqual(opportunity.betType, .playerProps)
        XCTAssertEqual(opportunity.sport, "NBA")
        XCTAssertEqual(opportunity.evPercentage, 12.5)
        XCTAssertEqual(opportunity.bestOdds, "+150")
        XCTAssertEqual(opportunity.fairOdds, "+120")
        XCTAssertEqual(opportunity.bestSource, "DraftKings")
        XCTAssertEqual(opportunity.classification, .great)
    }
    
    func testBettingOpportunityModel_Classifications() throws {
        // Given: Opportunities with different EV percentages
        let greatOpportunity = BettingOpportunity(
            id: "1", event: "Test", betDescription: "Test", betType: .moneyline,
            sport: "NFL", evPercentage: 15.0, bestOdds: "+150", fairOdds: "+120",
            bestSource: "DraftKings", gameTime: Date(), classification: .great
        )
        
        let goodOpportunity = BettingOpportunity(
            id: "2", event: "Test", betDescription: "Test", betType: .moneyline,
            sport: "NFL", evPercentage: 8.0, bestOdds: "+150", fairOdds: "+120",
            bestSource: "DraftKings", gameTime: Date(), classification: .good
        )
        
        let marginalOpportunity = BettingOpportunity(
            id: "3", event: "Test", betDescription: "Test", betType: .moneyline,
            sport: "NFL", evPercentage: 3.0, bestOdds: "+150", fairOdds: "+120",
            bestSource: "DraftKings", gameTime: Date(), classification: .marginal
        )
        
        // When: Checking classifications
        // Then: Should have correct properties
        XCTAssertTrue(greatOpportunity.isHighValue)
        XCTAssertTrue(greatOpportunity.shouldNotify)
        XCTAssertEqual(greatOpportunity.displayColor, .green)
        
        XCTAssertTrue(goodOpportunity.isRecommended)
        XCTAssertTrue(goodOpportunity.shouldNotify)
        XCTAssertEqual(goodOpportunity.displayColor, .blue)
        
        XCTAssertFalse(marginalOpportunity.isHighValue)
        XCTAssertFalse(marginalOpportunity.shouldNotify)
        XCTAssertEqual(marginalOpportunity.displayColor, .yellow)
    }
    
    func testBettingOpportunityModel_TimeValidation() throws {
        // Given: Opportunities with different game times
        let futureOpportunity = BettingOpportunity(
            id: "1", event: "Test", betDescription: "Test", betType: .moneyline,
            sport: "NFL", evPercentage: 10.0, bestOdds: "+150", fairOdds: "+120",
            bestSource: "DraftKings", gameTime: Date().addingTimeInterval(3600), classification: .great
        )
        
        let pastOpportunity = BettingOpportunity(
            id: "2", event: "Test", betDescription: "Test", betType: .moneyline,
            sport: "NFL", evPercentage: 10.0, bestOdds: "+150", fairOdds: "+120",
            bestSource: "DraftKings", gameTime: Date().addingTimeInterval(-3600), classification: .great
        )
        
        let soonOpportunity = BettingOpportunity(
            id: "3", event: "Test", betDescription: "Test", betType: .moneyline,
            sport: "NFL", evPercentage: 10.0, bestOdds: "+150", fairOdds: "+120",
            bestSource: "DraftKings", gameTime: Date().addingTimeInterval(300), classification: .great // 5 minutes
        )
        
        // When: Checking time validity
        // Then: Should validate correctly
        XCTAssertTrue(futureOpportunity.isStillValid)
        XCTAssertFalse(pastOpportunity.isStillValid)
        XCTAssertTrue(soonOpportunity.isStillValid)
        XCTAssertTrue(soonOpportunity.isStartingSoon)
        XCTAssertFalse(futureOpportunity.isStartingSoon)
    }
    
    func testBettingOpportunityModel_OddsConversion() throws {
        // Given: Opportunity with American odds
        let opportunity = BettingOpportunity(
            id: "1", event: "Test", betDescription: "Test", betType: .moneyline,
            sport: "NFL", evPercentage: 10.0, bestOdds: "+150", fairOdds: "-110",
            bestSource: "DraftKings", gameTime: Date(), classification: .great
        )
        
        // When: Converting odds
        let bestDecimalOdds = opportunity.bestOddsDecimal
        let fairDecimalOdds = opportunity.fairOddsDecimal
        
        // Then: Should convert correctly
        XCTAssertEqual(bestDecimalOdds, 2.5, accuracy: 0.01) // +150 = 2.5
        XCTAssertEqual(fairDecimalOdds, 1.909, accuracy: 0.01) // -110 = 1.909
    }
    
    func testBettingOpportunityModel_JSONSerialization() throws {
        // Given: Betting opportunity
        let opportunity = BettingOpportunity(
            id: "opp_123",
            event: "Lakers vs Warriors",
            betDescription: "LeBron Points Over 25.5",
            betType: .playerProps,
            sport: "NBA",
            evPercentage: 12.5,
            bestOdds: "+150",
            fairOdds: "+120",
            bestSource: "DraftKings",
            gameTime: Date(),
            classification: .great
        )
        
        // When: Encoding and decoding
        let encoder = JSONEncoder()
        let decoder = JSONDecoder()
        
        let jsonData = try encoder.encode(opportunity)
        let decodedOpportunity = try decoder.decode(BettingOpportunity.self, from: jsonData)
        
        // Then: Should serialize correctly
        XCTAssertEqual(decodedOpportunity.id, opportunity.id)
        XCTAssertEqual(decodedOpportunity.event, opportunity.event)
        XCTAssertEqual(decodedOpportunity.betType, opportunity.betType)
        XCTAssertEqual(decodedOpportunity.evPercentage, opportunity.evPercentage)
        XCTAssertEqual(decodedOpportunity.classification, opportunity.classification)
    }
    
    // MARK: - AppleIAP Model Tests
    
    func testAppleIAPModel_ProductInfo() throws {
        // Given: IAP product info
        let productInfo = AppleIAPProductInfo(
            productId: "com.fairedge.premium.monthly",
            displayName: "Premium Monthly",
            description: "Monthly premium subscription",
            price: 9.99,
            priceLocale: Locale(identifier: "en_US"),
            subscriptionPeriod: .monthly
        )
        
        // Then: Should initialize correctly
        XCTAssertEqual(productInfo.productId, "com.fairedge.premium.monthly")
        XCTAssertEqual(productInfo.displayName, "Premium Monthly")
        XCTAssertEqual(productInfo.price, 9.99)
        XCTAssertEqual(productInfo.subscriptionPeriod, .monthly)
        XCTAssertEqual(productInfo.formattedPrice, "$9.99")
        XCTAssertTrue(productInfo.isSubscription)
    }
    
    func testAppleIAPModel_PurchaseResult() throws {
        // Given: Purchase result
        let successResult = AppleIAPPurchaseResult(
            success: true,
            productId: "com.fairedge.premium.monthly",
            transactionId: "txn_12345",
            receipt: "receipt_data_base64",
            error: nil
        )
        
        let failureResult = AppleIAPPurchaseResult(
            success: false,
            productId: "com.fairedge.premium.monthly",
            transactionId: nil,
            receipt: nil,
            error: "Purchase cancelled by user"
        )
        
        // Then: Should represent results correctly
        XCTAssertTrue(successResult.success)
        XCTAssertNotNil(successResult.transactionId)
        XCTAssertNotNil(successResult.receipt)
        XCTAssertNil(successResult.error)
        
        XCTAssertFalse(failureResult.success)
        XCTAssertNil(failureResult.transactionId)
        XCTAssertNil(failureResult.receipt)
        XCTAssertNotNil(failureResult.error)
    }
    
    func testAppleIAPModel_SubscriptionStatus() throws {
        // Given: Subscription status
        let activeStatus = AppleIAPSubscriptionStatus(
            isActive: true,
            productId: "com.fairedge.premium.monthly",
            expirationDate: Date().addingTimeInterval(2592000), // 30 days
            autoRenewEnabled: true,
            isInGracePeriod: false,
            isInBillingRetryPeriod: false
        )
        
        let expiredStatus = AppleIAPSubscriptionStatus(
            isActive: false,
            productId: "com.fairedge.premium.monthly",
            expirationDate: Date().addingTimeInterval(-86400), // 1 day ago
            autoRenewEnabled: false,
            isInGracePeriod: false,
            isInBillingRetryPeriod: false
        )
        
        let gracePeriodStatus = AppleIAPSubscriptionStatus(
            isActive: true,
            productId: "com.fairedge.premium.monthly",
            expirationDate: Date().addingTimeInterval(-3600), // 1 hour ago
            autoRenewEnabled: true,
            isInGracePeriod: true,
            isInBillingRetryPeriod: false
        )
        
        // Then: Should validate status correctly
        XCTAssertTrue(activeStatus.isActive)
        XCTAssertTrue(activeStatus.shouldAllowAccess)
        XCTAssertFalse(activeStatus.needsAttention)
        
        XCTAssertFalse(expiredStatus.isActive)
        XCTAssertFalse(expiredStatus.shouldAllowAccess)
        XCTAssertTrue(expiredStatus.needsAttention)
        
        XCTAssertTrue(gracePeriodStatus.isActive)
        XCTAssertTrue(gracePeriodStatus.shouldAllowAccess)
        XCTAssertTrue(gracePeriodStatus.needsAttention)
    }
    
    // MARK: - MobileConfig Model Tests
    
    func testMobileConfigModel_FeatureFlags() throws {
        // Given: Mobile config with feature flags
        let config = MobileConfig(
            apiVersion: "v1",
            features: MobileFeatures(
                pushNotifications: true,
                realTimeUpdates: true,
                offlineMode: false,
                exportData: true
            ),
            endpoints: MobileEndpoints(
                opportunities: "/api/opportunities",
                subscriptionStatus: "/api/iap/subscription-status",
                validateReceipt: "/api/iap/validate-receipt"
            ),
            performanceSettings: PerformanceSettings(
                cacheDuration: 300,
                backgroundRefreshInterval: 900,
                networkTimeout: 30
            )
        )
        
        // Then: Should configure correctly
        XCTAssertEqual(config.apiVersion, "v1")
        XCTAssertTrue(config.features.pushNotifications)
        XCTAssertTrue(config.features.realTimeUpdates)
        XCTAssertFalse(config.features.offlineMode)
        XCTAssertTrue(config.features.exportData)
        
        XCTAssertEqual(config.endpoints.opportunities, "/api/opportunities")
        XCTAssertEqual(config.performanceSettings.cacheDuration, 300)
    }
    
    func testMobileConfigModel_RoleBasedFeatures() throws {
        // Given: Configs for different user roles
        let freeUserConfig = MobileConfig.forUserRole(.free)
        let premiumUserConfig = MobileConfig.forUserRole(.premium)
        let adminUserConfig = MobileConfig.forUserRole(.admin)
        
        // Then: Should have role-appropriate features
        XCTAssertFalse(freeUserConfig.features.exportData)
        XCTAssertFalse(freeUserConfig.features.realTimeUpdates)
        
        XCTAssertTrue(premiumUserConfig.features.exportData)
        XCTAssertTrue(premiumUserConfig.features.realTimeUpdates)
        
        XCTAssertTrue(adminUserConfig.features.exportData)
        XCTAssertTrue(adminUserConfig.features.realTimeUpdates)
        XCTAssertTrue(adminUserConfig.features.debugMode)
    }
    
    func testMobileConfigModel_JSONSerialization() throws {
        // Given: Mobile config
        let config = MobileConfig.defaultConfig()
        
        // When: Encoding and decoding
        let encoder = JSONEncoder()
        let decoder = JSONDecoder()
        
        let jsonData = try encoder.encode(config)
        let decodedConfig = try decoder.decode(MobileConfig.self, from: jsonData)
        
        // Then: Should serialize correctly
        XCTAssertEqual(decodedConfig.apiVersion, config.apiVersion)
        XCTAssertEqual(decodedConfig.features.pushNotifications, config.features.pushNotifications)
        XCTAssertEqual(decodedConfig.endpoints.opportunities, config.endpoints.opportunities)
    }
    
    // MARK: - Authentication Model Tests
    
    func testAuthenticationModel_Credentials() throws {
        // Given: Authentication credentials
        let credentials = AuthenticationCredentials(
            accessToken: "access_token_123",
            refreshToken: "refresh_token_456",
            tokenType: "Bearer",
            expiresIn: 3600,
            scope: "read write"
        )
        
        // Then: Should initialize correctly
        XCTAssertEqual(credentials.accessToken, "access_token_123")
        XCTAssertEqual(credentials.refreshToken, "refresh_token_456")
        XCTAssertEqual(credentials.tokenType, "Bearer")
        XCTAssertEqual(credentials.expiresIn, 3600)
        XCTAssertEqual(credentials.scope, "read write")
        
        // When: Checking expiration
        let isExpired = credentials.isExpired
        let expirationDate = credentials.expirationDate
        
        // Then: Should calculate expiration correctly
        XCTAssertFalse(isExpired)
        XCTAssertNotNil(expirationDate)
    }
    
    func testAuthenticationModel_AppleIDCredential() throws {
        // Given: Apple ID credential
        let appleCredential = AppleIDCredential(
            user: "user_12345",
            identityToken: "identity_token_data",
            authorizationCode: "auth_code_data",
            email: "user@icloud.com",
            fullName: PersonNameComponents()
        )
        
        // Then: Should initialize correctly
        XCTAssertEqual(appleCredential.user, "user_12345")
        XCTAssertEqual(appleCredential.identityToken, "identity_token_data")
        XCTAssertEqual(appleCredential.authorizationCode, "auth_code_data")
        XCTAssertEqual(appleCredential.email, "user@icloud.com")
        XCTAssertNotNil(appleCredential.fullName)
    }
    
    // MARK: - Model Validation Tests
    
    func testModelValidation_EmailFormat() throws {
        // Given: Valid and invalid emails
        let validEmails = [
            "test@fair-edge.com",
            "user.name+tag@example.co.uk",
            "simple@example.org"
        ]
        
        let invalidEmails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user name@domain.com"
        ]
        
        // When: Validating emails
        for email in validEmails {
            // Then: Should be valid
            XCTAssertTrue(User.isValidEmail(email), "Email should be valid: \(email)")
        }
        
        for email in invalidEmails {
            // Then: Should be invalid
            XCTAssertFalse(User.isValidEmail(email), "Email should be invalid: \(email)")
        }
    }
    
    func testModelValidation_OpportunityEV() throws {
        // Given: EV percentages
        let validEVs = [0.1, 5.0, 15.0, 25.0]
        let invalidEVs = [-5.0, -1.0, 100.0, 150.0]
        
        // When: Validating EV percentages
        for ev in validEVs {
            // Then: Should be valid
            XCTAssertTrue(BettingOpportunity.isValidEVPercentage(ev), "EV should be valid: \(ev)")
        }
        
        for ev in invalidEVs {
            // Then: Should be invalid
            XCTAssertFalse(BettingOpportunity.isValidEVPercentage(ev), "EV should be invalid: \(ev)")
        }
    }
    
    func testModelValidation_ProductID() throws {
        // Given: Product IDs
        let validProductIDs = [
            "com.fairedge.premium.monthly",
            "com.fairedge.basic.yearly",
            "com.company.product.subscription"
        ]
        
        let invalidProductIDs = [
            "",
            "invalid_product_id",
            "com.",
            ".com.product"
        ]
        
        // When: Validating product IDs
        for productID in validProductIDs {
            // Then: Should be valid
            XCTAssertTrue(AppleIAPProductInfo.isValidProductID(productID), "Product ID should be valid: \(productID)")
        }
        
        for productID in invalidProductIDs {
            // Then: Should be invalid
            XCTAssertFalse(AppleIAPProductInfo.isValidProductID(productID), "Product ID should be invalid: \(productID)")
        }
    }
    
    // MARK: - Model Comparison Tests
    
    func testModelEquality_User() throws {
        // Given: Identical users
        let user1 = User(id: "1", email: "test@test.com", role: .premium, subscriptionStatus: .active, deviceId: "device1")
        let user2 = User(id: "1", email: "test@test.com", role: .premium, subscriptionStatus: .active, deviceId: "device1")
        let user3 = User(id: "2", email: "test@test.com", role: .premium, subscriptionStatus: .active, deviceId: "device1")
        
        // When: Comparing users
        // Then: Should compare correctly
        XCTAssertEqual(user1, user2)
        XCTAssertNotEqual(user1, user3)
    }
    
    func testModelEquality_BettingOpportunity() throws {
        // Given: Identical opportunities
        let opportunity1 = BettingOpportunity(
            id: "1", event: "Test", betDescription: "Test", betType: .moneyline,
            sport: "NFL", evPercentage: 10.0, bestOdds: "+150", fairOdds: "+120",
            bestSource: "DraftKings", gameTime: Date(), classification: .great
        )
        
        let opportunity2 = BettingOpportunity(
            id: "1", event: "Test", betDescription: "Test", betType: .moneyline,
            sport: "NFL", evPercentage: 10.0, bestOdds: "+150", fairOdds: "+120",
            bestSource: "DraftKings", gameTime: opportunity1.gameTime, classification: .great
        )
        
        let opportunity3 = BettingOpportunity(
            id: "2", event: "Test", betDescription: "Test", betType: .moneyline,
            sport: "NFL", evPercentage: 10.0, bestOdds: "+150", fairOdds: "+120",
            bestSource: "DraftKings", gameTime: Date(), classification: .great
        )
        
        // When: Comparing opportunities
        // Then: Should compare correctly
        XCTAssertEqual(opportunity1, opportunity2)
        XCTAssertNotEqual(opportunity1, opportunity3)
    }
    
    // MARK: - Performance Tests
    
    func testModelPerformance_JSONSerialization() throws {
        // Given: Large array of opportunities
        let opportunities = Array(0..<1000).map { index in
            BettingOpportunity(
                id: "opp_\(index)",
                event: "Event \(index)",
                betDescription: "Bet \(index)",
                betType: .moneyline,
                sport: "NFL",
                evPercentage: Double(index % 20),
                bestOdds: "+150",
                fairOdds: "+120",
                bestSource: "DraftKings",
                gameTime: Date(),
                classification: .great
            )
        }
        
        // When: Measuring serialization performance
        measure {
            let encoder = JSONEncoder()
            let decoder = JSONDecoder()
            
            do {
                let jsonData = try encoder.encode(opportunities)
                _ = try decoder.decode([BettingOpportunity].self, from: jsonData)
            } catch {
                XCTFail("Serialization failed: \(error)")
            }
        }
    }
}