//
//  StoreKitService.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import Foundation
import StoreKit
import Combine

/// StoreKit 2 service for managing in-app purchases and subscriptions
@MainActor
class StoreKitService: ObservableObject {

    // MARK: - Published Properties

    @Published var availableProducts: [Product] = []
    @Published var purchasedProducts: Set<Product> = []
    @Published var subscriptionStatus: SubscriptionStatus = .none
    @Published var isLoading = false
    @Published var errorMessage: String?

    // MARK: - Private Properties

    private let apiService: APIService
    private var updateListenerTask: Task<Void, Error>?
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Product Identifiers

    enum ProductIdentifier: String, CaseIterable {
        case basicMonthly = "com.fairedge.basic_monthly"      // $3.99/month
        case premiumMonthly = "com.fairedge.premium_monthly"  // $9.99/month
        case premiumYearly = "com.fairedge.premium_yearly"    // $89.99/year

        var displayName: String {
            switch self {
            case .basicMonthly:
                return "Basic Monthly"
            case .premiumMonthly:
                return "Premium Monthly"
            case .premiumYearly:
                return "Premium Yearly"
            }
        }

        var userRole: UserRole {
            switch self {
            case .basicMonthly:
                return .basic
            case .premiumMonthly, .premiumYearly:
                return .premium
            }
        }
    }

    // MARK: - Initialization

    init(apiService: APIService = APIService()) {
        self.apiService = apiService

        // Start listening for transaction updates
        updateListenerTask = listenForTransactions()

        // Load products on initialization
        Task {
            await loadProducts()
            await checkSubscriptionStatus()
        }
    }

    deinit {
        updateListenerTask?.cancel()
    }

    // MARK: - Public Methods

    /// Load available products from App Store
    func loadProducts() async {
        isLoading = true
        errorMessage = nil

        do {
            let productIds = ProductIdentifier.allCases.map { $0.rawValue }
            let products = try await Product.products(for: Set(productIds))

            self.availableProducts = products.sorted { product1, product2 in
                // Sort by price: Basic < Premium Monthly < Premium Yearly
                return product1.price < product2.price
            }

        } catch {
            self.errorMessage = "Failed to load products: \(error.localizedDescription)"
        }

        isLoading = false
    }

    /// Purchase a product
    func purchase(_ product: Product) async throws -> Transaction? {
        isLoading = true
        errorMessage = nil

        do {
            let result = try await product.purchase()

            switch result {
            case .success(let verification):
                let transaction = try checkVerified(verification)

                // Validate with backend
                try await validatePurchaseWithBackend(transaction)

                // Finish the transaction
                await transaction.finish()

                // Update subscription status
                await checkSubscriptionStatus()

                isLoading = false
                return transaction

            case .userCancelled:
                isLoading = false
                return nil

            case .pending:
                isLoading = false
                errorMessage = "Purchase is pending approval"
                return nil

            @unknown default:
                isLoading = false
                errorMessage = "Unknown purchase result"
                return nil
            }

        } catch {
            isLoading = false
            errorMessage = "Purchase failed: \(error.localizedDescription)"
            throw error
        }
    }

    /// Restore previous purchases
    func restorePurchases() async throws {
        isLoading = true
        errorMessage = nil

        do {
            try await AppStore.sync()

            // Check current entitlements
            await checkSubscriptionStatus()

            // Notify backend to restore purchases
            try await apiService.restorePurchases()

            isLoading = false

        } catch {
            isLoading = false
            errorMessage = "Failed to restore purchases: \(error.localizedDescription)"
            throw error
        }
    }

    /// Check current subscription status
    func checkSubscriptionStatus() async {
        do {
            // Check for active subscriptions
            for await result in Transaction.currentEntitlements {
                let transaction = try checkVerified(result)

                if let productId = ProductIdentifier(rawValue: transaction.productID) {
                    // Validate current subscription with backend
                    try await validateCurrentSubscription(transaction)
                    break
                }
            }

        } catch {
            print("Failed to check subscription status: \(error)")
        }
    }

    /// Get product by identifier
    func product(for identifier: ProductIdentifier) -> Product? {
        return availableProducts.first { $0.id == identifier.rawValue }
    }

    /// Check if user has active subscription
    var hasActiveSubscription: Bool {
        return subscriptionStatus == .active
    }

    /// Get current subscription product
    var currentSubscriptionProduct: Product? {
        guard hasActiveSubscription else { return nil }
        return purchasedProducts.first
    }

    // MARK: - Private Methods

    /// Listen for transaction updates
    private func listenForTransactions() -> Task<Void, Error> {
        return Task.detached {
            for await result in Transaction.updates {
                do {
                    let transaction = try self.checkVerified(result)

                    // Validate with backend
                    try await self.validatePurchaseWithBackend(transaction)

                    // Update subscription status
                    await self.checkSubscriptionStatus()

                    // Finish the transaction
                    await transaction.finish()

                } catch {
                    print("Transaction update failed: \(error)")
                }
            }
        }
    }

    /// Verify transaction signature
    private func checkVerified<T>(_ result: VerificationResult<T>) throws -> T {
        switch result {
        case .unverified:
            throw StoreKitError.failedVerification
        case .verified(let safe):
            return safe
        }
    }

    /// Validate purchase with backend
    private func validatePurchaseWithBackend(_ transaction: Transaction) async throws {
        // Create receipt validation request
        let receiptData = try await getReceiptData(for: transaction)

        let validationRequest = ReceiptValidationRequest(
            receiptData: receiptData,
            productId: transaction.productID,
            transactionId: String(transaction.id)
        )

        // Send to backend for validation
        let response = try await apiService.validateAppleReceipt(validationRequest)

        if response.success {
            // Update local subscription status
            if let productId = ProductIdentifier(rawValue: transaction.productID) {
                await MainActor.run {
                    self.subscriptionStatus = .active
                    if let product = self.product(for: productId) {
                        self.purchasedProducts.insert(product)
                    }
                }
            }
        } else {
            throw StoreKitError.backendValidationFailed
        }
    }

    /// Validate current subscription with backend
    private func validateCurrentSubscription(_ transaction: Transaction) async throws {
        // Check if subscription is still valid
        if transaction.expirationDate?.timeIntervalSinceNow ?? 0 > 0 {
            // Still active
            await MainActor.run {
                self.subscriptionStatus = .active
                if let productId = ProductIdentifier(rawValue: transaction.productID),
                   let product = self.product(for: productId) {
                    self.purchasedProducts.insert(product)
                }
            }
        } else {
            // Expired
            await MainActor.run {
                self.subscriptionStatus = .expired
                self.purchasedProducts.removeAll()
            }
        }
    }

    /// Get receipt data for transaction
    private func getReceiptData(for transaction: Transaction) async throws -> String {
        // In iOS 15+, we use the transaction's payload data
        if let payloadData = try? await transaction.payloadData {
            return payloadData.base64EncodedString()
        }

        // Fallback to app receipt
        guard let appStoreReceiptURL = Bundle.main.appStoreReceiptURL,
              let receiptData = try? Data(contentsOf: appStoreReceiptURL) else {
            throw StoreKitError.noReceiptData
        }

        return receiptData.base64EncodedString()
    }
}

// MARK: - Supporting Models

/// Receipt validation request for backend
struct ReceiptValidationRequest: Codable {
    let receiptData: String
    let productId: String
    let transactionId: String

    enum CodingKeys: String, CodingKey {
        case receiptData = "receipt_data"
        case productId = "product_id"
        case transactionId = "transaction_id"
    }
}

/// Receipt validation response from backend
struct ReceiptValidationResponse: Codable {
    let success: Bool
    let userRole: String?
    let subscriptionStatus: String?
    let expirationDate: String?
    let message: String?

    enum CodingKeys: String, CodingKey {
        case success
        case userRole = "user_role"
        case subscriptionStatus = "subscription_status"
        case expirationDate = "expiration_date"
        case message
    }
}

// MARK: - StoreKit Errors

enum StoreKitError: Error, LocalizedError {
    case failedVerification
    case noReceiptData
    case backendValidationFailed
    case productNotFound
    case purchaseNotAllowed

    var errorDescription: String? {
        switch self {
        case .failedVerification:
            return "Transaction verification failed"
        case .noReceiptData:
            return "No receipt data available"
        case .backendValidationFailed:
            return "Backend validation failed"
        case .productNotFound:
            return "Product not found"
        case .purchaseNotAllowed:
            return "Purchases are not allowed"
        }
    }
}
