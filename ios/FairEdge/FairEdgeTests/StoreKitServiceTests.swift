//
//  StoreKitServiceTests.swift
//  FairEdgeTests
//
//  Unit tests for StoreKitService
//  Tests in-app purchase functionality and subscription management

import XCTest
import Combine
import StoreKit
@testable import FairEdge

class StoreKitServiceTests: XCTestCase {

    // MARK: - Properties

    var storeKitService: StoreKitService!
    var mockStoreKit: MockStoreKit!
    var cancellables: Set<AnyCancellable>!

    // MARK: - Setup & Teardown

    override func setUpWithError() throws {
        try super.setUpWithError()

        mockStoreKit = MockStoreKit()
        storeKitService = StoreKitService(storeKit: mockStoreKit)
        cancellables = Set<AnyCancellable>()
    }

    override func tearDownWithError() throws {
        storeKitService = nil
        mockStoreKit = nil
        cancellables.removeAll()
        cancellables = nil
        try super.tearDownWithError()
    }

    // MARK: - Product Loading Tests

    func testLoadProducts_Success() async throws {
        // Given: Mock products available
        let mockProducts = [
            createMockProduct(id: "com.fairedge.basic.monthly", price: 3.99),
            createMockProduct(id: "com.fairedge.premium.monthly", price: 9.99),
            createMockProduct(id: "com.fairedge.premium.yearly", price: 89.99)
        ]
        mockStoreKit.products = mockProducts

        // When: Loading products
        await storeKitService.loadProducts()

        // Then: Products should be available
        XCTAssertEqual(storeKitService.products.count, 3)
        XCTAssertTrue(storeKitService.productsLoaded)

        let basicProduct = storeKitService.products.first { $0.id == "com.fairedge.basic.monthly" }
        XCTAssertNotNil(basicProduct)
        XCTAssertEqual(basicProduct?.price, Decimal(3.99))
    }

    func testLoadProducts_StoreKitError() async throws {
        // Given: StoreKit error
        mockStoreKit.shouldFailProductRequest = true
        mockStoreKit.error = SKError(.productNotAvailable)

        // When: Loading products
        await storeKitService.loadProducts()

        // Then: Should handle error gracefully
        XCTAssertFalse(storeKitService.productsLoaded)
        XCTAssertTrue(storeKitService.products.isEmpty)
        XCTAssertNotNil(storeKitService.errorMessage)
    }

    func testLoadProducts_NoProductsAvailable() async throws {
        // Given: No products available
        mockStoreKit.products = []

        // When: Loading products
        await storeKitService.loadProducts()

        // Then: Should indicate no products loaded
        XCTAssertTrue(storeKitService.products.isEmpty)
        XCTAssertFalse(storeKitService.productsLoaded)
    }

    // MARK: - Purchase Tests

    func testPurchaseProduct_Success() async throws {
        // Given: Successful purchase setup
        let mockProduct = createMockProduct(id: "com.fairedge.premium.monthly", price: 9.99)
        mockStoreKit.products = [mockProduct]
        await storeKitService.loadProducts()

        mockStoreKit.shouldSucceedPurchase = true
        mockStoreKit.mockTransaction = createMockTransaction(productId: "com.fairedge.premium.monthly")

        let expectation = XCTestExpectation(description: "Purchase succeeds")

        // When: Purchasing product
        guard let product = storeKitService.products.first else {
            XCTFail("Product not found")
            return
        }

        try await storeKitService.purchaseProduct(product)

        // Then: Purchase should succeed
        storeKitService.$lastPurchaseResult
            .compactMap { $0 }
            .sink { result in
                if case .success(let transaction) = result {
                    XCTAssertEqual(transaction.productID, "com.fairedge.premium.monthly")
                    expectation.fulfill()
                } else {
                    XCTFail("Purchase should succeed")
                }
            }
            .store(in: &cancellables)

        await fulfillment(of: [expectation], timeout: 5.0)
    }

    func testPurchaseProduct_UserCancelled() async throws {
        // Given: User cancellation setup
        let mockProduct = createMockProduct(id: "com.fairedge.premium.monthly", price: 9.99)
        mockStoreKit.products = [mockProduct]
        await storeKitService.loadProducts()

        mockStoreKit.shouldSucceedPurchase = false
        mockStoreKit.error = SKError(.paymentCancelled)

        let expectation = XCTestExpectation(description: "Purchase cancelled")

        // When: Attempting purchase
        guard let product = storeKitService.products.first else {
            XCTFail("Product not found")
            return
        }

        do {
            try await storeKitService.purchaseProduct(product)
        } catch {
            // Then: Should handle cancellation gracefully
            XCTAssertTrue(error is SKError)
            if let skError = error as? SKError {
                XCTAssertEqual(skError.code, .paymentCancelled)
            }
            expectation.fulfill()
        }

        await fulfillment(of: [expectation], timeout: 5.0)
    }

    func testPurchaseProduct_PaymentNotAllowed() async throws {
        // Given: Payment not allowed
        let mockProduct = createMockProduct(id: "com.fairedge.premium.monthly", price: 9.99)
        mockStoreKit.products = [mockProduct]
        await storeKitService.loadProducts()

        mockStoreKit.shouldSucceedPurchase = false
        mockStoreKit.error = SKError(.paymentNotAllowed)

        // When: Attempting purchase
        guard let product = storeKitService.products.first else {
            XCTFail("Product not found")
            return
        }

        do {
            try await storeKitService.purchaseProduct(product)
            XCTFail("Should throw error")
        } catch {
            // Then: Should throw appropriate error
            XCTAssertTrue(error is SKError)
            if let skError = error as? SKError {
                XCTAssertEqual(skError.code, .paymentNotAllowed)
            }
        }
    }

    // MARK: - Restore Purchases Tests

    func testRestorePurchases_Success() async throws {
        // Given: Previous purchases available
        let mockTransactions = [
            createMockTransaction(productId: "com.fairedge.premium.monthly"),
            createMockTransaction(productId: "com.fairedge.basic.monthly")
        ]
        mockStoreKit.restoredTransactions = mockTransactions

        let expectation = XCTestExpectation(description: "Restore succeeds")

        // When: Restoring purchases
        try await storeKitService.restorePurchases()

        // Then: Should restore previous purchases
        storeKitService.$restoredTransactions
            .dropFirst()
            .sink { transactions in
                XCTAssertEqual(transactions.count, 2)
                XCTAssertTrue(transactions.contains { $0.productID == "com.fairedge.premium.monthly" })
                expectation.fulfill()
            }
            .store(in: &cancellables)

        await fulfillment(of: [expectation], timeout: 5.0)
    }

    func testRestorePurchases_NoPreviousPurchases() async throws {
        // Given: No previous purchases
        mockStoreKit.restoredTransactions = []

        // When: Restoring purchases
        try await storeKitService.restorePurchases()

        // Then: Should handle gracefully
        XCTAssertTrue(storeKitService.restoredTransactions.isEmpty)
        XCTAssertNil(storeKitService.errorMessage)
    }

    func testRestorePurchases_StoreKitError() async throws {
        // Given: StoreKit error during restore
        mockStoreKit.shouldFailRestore = true
        mockStoreKit.error = SKError(.unknown)

        // When: Restoring purchases
        do {
            try await storeKitService.restorePurchases()
            XCTFail("Should throw error")
        } catch {
            // Then: Should throw appropriate error
            XCTAssertTrue(error is SKError)
        }
    }

    // MARK: - Transaction Validation Tests

    func testTransactionValidation_ValidTransaction() throws {
        // Given: Valid transaction
        let transaction = createMockTransaction(productId: "com.fairedge.premium.monthly")

        // When: Validating transaction
        let isValid = storeKitService.validateTransaction(transaction)

        // Then: Should be valid
        XCTAssertTrue(isValid)
    }

    func testTransactionValidation_InvalidTransaction() throws {
        // Given: Invalid transaction (expired)
        let transaction = createMockTransaction(
            productId: "com.fairedge.premium.monthly",
            expirationDate: Date().addingTimeInterval(-86400) // Expired yesterday
        )

        // When: Validating transaction
        let isValid = storeKitService.validateTransaction(transaction)

        // Then: Should be invalid
        XCTAssertFalse(isValid)
    }

    // MARK: - Receipt Validation Tests

    func testReceiptValidation_ValidReceipt() async throws {
        // Given: Valid receipt data
        let mockReceiptData = "mock_receipt_data_base64_encoded"
        mockStoreKit.receiptData = mockReceiptData.data(using: .utf8)

        // When: Getting receipt for validation
        let receiptData = storeKitService.getReceiptData()

        // Then: Should return receipt data
        XCTAssertNotNil(receiptData)
        XCTAssertEqual(String(data: receiptData!, encoding: .utf8), mockReceiptData)
    }

    func testReceiptValidation_NoReceipt() throws {
        // Given: No receipt available
        mockStoreKit.receiptData = nil

        // When: Getting receipt for validation
        let receiptData = storeKitService.getReceiptData()

        // Then: Should return nil
        XCTAssertNil(receiptData)
    }

    // MARK: - Subscription Status Tests

    func testSubscriptionStatus_ActiveSubscription() throws {
        // Given: Active subscription transaction
        let transaction = createMockTransaction(
            productId: "com.fairedge.premium.monthly",
            expirationDate: Date().addingTimeInterval(86400) // Expires tomorrow
        )
        storeKitService.restoredTransactions = [transaction]

        // When: Checking subscription status
        let status = storeKitService.getSubscriptionStatus()

        // Then: Should be active
        XCTAssertEqual(status.isActive, true)
        XCTAssertEqual(status.productId, "com.fairedge.premium.monthly")
        XCTAssertNotNil(status.expirationDate)
    }

    func testSubscriptionStatus_ExpiredSubscription() throws {
        // Given: Expired subscription transaction
        let transaction = createMockTransaction(
            productId: "com.fairedge.premium.monthly",
            expirationDate: Date().addingTimeInterval(-86400) // Expired yesterday
        )
        storeKitService.restoredTransactions = [transaction]

        // When: Checking subscription status
        let status = storeKitService.getSubscriptionStatus()

        // Then: Should be inactive
        XCTAssertEqual(status.isActive, false)
        XCTAssertNil(status.productId)
        XCTAssertNil(status.expirationDate)
    }

    func testSubscriptionStatus_NoSubscription() throws {
        // Given: No subscription transactions
        storeKitService.restoredTransactions = []

        // When: Checking subscription status
        let status = storeKitService.getSubscriptionStatus()

        // Then: Should be inactive
        XCTAssertEqual(status.isActive, false)
        XCTAssertNil(status.productId)
        XCTAssertNil(status.expirationDate)
    }

    // MARK: - Product Info Tests

    func testProductInfo_BasicMonthly() async throws {
        // Given: Basic monthly product loaded
        let mockProduct = createMockProduct(id: "com.fairedge.basic.monthly", price: 3.99)
        mockStoreKit.products = [mockProduct]
        await storeKitService.loadProducts()

        // When: Getting product info
        let productInfo = storeKitService.getProductInfo(for: "com.fairedge.basic.monthly")

        // Then: Should return correct info
        XCTAssertNotNil(productInfo)
        XCTAssertEqual(productInfo?.price, Decimal(3.99))
        XCTAssertEqual(productInfo?.displayName, "Fair-Edge Basic")
        XCTAssertEqual(productInfo?.billingPeriod, .monthly)
    }

    func testProductInfo_PremiumYearly() async throws {
        // Given: Premium yearly product loaded
        let mockProduct = createMockProduct(id: "com.fairedge.premium.yearly", price: 89.99)
        mockStoreKit.products = [mockProduct]
        await storeKitService.loadProducts()

        // When: Getting product info
        let productInfo = storeKitService.getProductInfo(for: "com.fairedge.premium.yearly")

        // Then: Should return correct info
        XCTAssertNotNil(productInfo)
        XCTAssertEqual(productInfo?.price, Decimal(89.99))
        XCTAssertEqual(productInfo?.displayName, "Fair-Edge Premium")
        XCTAssertEqual(productInfo?.billingPeriod, .yearly)
    }

    func testProductInfo_UnknownProduct() async throws {
        // Given: Products loaded but unknown product requested
        await storeKitService.loadProducts()

        // When: Getting info for unknown product
        let productInfo = storeKitService.getProductInfo(for: "com.unknown.product")

        // Then: Should return nil
        XCTAssertNil(productInfo)
    }

    // MARK: - Error Handling Tests

    func testErrorHandling_NetworkError() async throws {
        // Given: Network error during product load
        mockStoreKit.shouldFailProductRequest = true
        mockStoreKit.error = URLError(.notConnectedToInternet)

        // When: Loading products
        await storeKitService.loadProducts()

        // Then: Should handle network error
        XCTAssertFalse(storeKitService.productsLoaded)
        XCTAssertNotNil(storeKitService.errorMessage)
        XCTAssertTrue(storeKitService.errorMessage?.contains("network") ?? false)
    }

    func testErrorHandling_StoreNotAvailable() async throws {
        // Given: Store not available
        mockStoreKit.shouldFailProductRequest = true
        mockStoreKit.error = SKError(.storeProductNotAvailable)

        // When: Loading products
        await storeKitService.loadProducts()

        // Then: Should handle store error
        XCTAssertFalse(storeKitService.productsLoaded)
        XCTAssertNotNil(storeKitService.errorMessage)
    }

    // MARK: - Performance Tests

    func testPerformance_ProductLoading() async throws {
        // Given: Large number of mock products
        let products = Array(0..<100).map { index in
            createMockProduct(id: "com.fairedge.product.\(index)", price: Double(index + 1))
        }
        mockStoreKit.products = products

        // When: Measuring product loading performance
        measure {
            Task {
                await storeKitService.loadProducts()
            }
        }
    }

    func testPerformance_TransactionValidation() throws {
        // Given: Large number of transactions
        let transactions = Array(0..<1000).map { index in
            createMockTransaction(productId: "com.fairedge.product.\(index)")
        }

        // When: Measuring validation performance
        measure {
            for transaction in transactions {
                _ = storeKitService.validateTransaction(transaction)
            }
        }
    }
}

// MARK: - Test Utilities

extension StoreKitServiceTests {

    func createMockProduct(id: String, price: Double) -> Product {
        return MockProduct(
            id: id,
            displayName: "Fair-Edge \(id.contains("basic") ? "Basic" : "Premium")",
            price: Decimal(price)
        )
    }

    func createMockTransaction(productId: String, expirationDate: Date? = nil) -> Transaction {
        return MockTransaction(
            productID: productId,
            purchaseDate: Date(),
            expirationDate: expirationDate
        )
    }
}

// MARK: - Mock Classes

class MockStoreKit {
    var products: [Product] = []
    var shouldFailProductRequest = false
    var shouldSucceedPurchase = true
    var shouldFailRestore = false
    var error: Error?
    var mockTransaction: Transaction?
    var restoredTransactions: [Transaction] = []
    var receiptData: Data?

    func requestProducts(withIdentifiers identifiers: Set<String>) async throws -> [Product] {
        if shouldFailProductRequest {
            throw error ?? SKError(.productNotAvailable)
        }
        return products.filter { identifiers.contains($0.id) }
    }

    func purchase(_ product: Product) async throws -> Transaction {
        if !shouldSucceedPurchase {
            throw error ?? SKError(.paymentCancelled)
        }
        return mockTransaction ?? MockTransaction(productID: product.id, purchaseDate: Date(), expirationDate: nil)
    }

    func restoreCompletedTransactions() async throws -> [Transaction] {
        if shouldFailRestore {
            throw error ?? SKError(.unknown)
        }
        return restoredTransactions
    }
}

// MARK: - Mock Product

struct MockProduct: Product {
    let id: String
    let displayName: String
    let price: Decimal

    var description: String { displayName }
    var type: Product.ProductType { .autoRenewable }
}

// MARK: - Mock Transaction

struct MockTransaction: Transaction {
    let productID: String
    let purchaseDate: Date
    let expirationDate: Date?

    var id: UInt64 { 123456789 }
    var originalID: UInt64 { 123456789 }
    var appBundleID: String { "com.fairedge.app" }
    var subscriptionGroupID: String? { "premium_group" }
    var webOrderLineItemID: String? { "web_order_123" }
    var signedDate: Date { purchaseDate }
    var revocationDate: Date? { nil }
    var revocationReason: Transaction.RevocationReason? { nil }
    var isUpgraded: Bool { false }
    var offerType: Transaction.OfferType? { nil }
    var offerID: String? { nil }
    var environment: AppStore.Environment { .sandbox }
    var ownershipType: Transaction.OwnershipType { .purchased }
    var storefront: String? { "USA" }
    var storefrontID: String? { "143441" }
    var jsonRepresentation: Data { Data() }
}
