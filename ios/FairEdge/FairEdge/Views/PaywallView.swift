//
//  PaywallView.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import SwiftUI
import StoreKit

/// Paywall view for subscription management and feature comparison
struct PaywallView: View {
    @StateObject private var storeKitService = StoreKitService()
    @EnvironmentObject var authenticationService: AuthenticationService
    @Environment(\.presentationMode) var presentationMode
    
    @State private var selectedProduct: Product?
    @State private var showingPurchaseConfirmation = false
    @State private var showingTerms = false
    @State private var showingPrivacy = false
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 24) {
                    // Header
                    headerSection
                    
                    // Feature comparison
                    featureComparisonSection
                    
                    // Pricing plans
                    pricingPlansSection
                    
                    // Purchase button
                    purchaseButtonSection
                    
                    // Restore purchases
                    restorePurchasesSection
                    
                    // Terms and privacy
                    legalLinksSection
                }
                .padding()
            }
            .navigationTitle("Upgrade to Premium")
            .navigationBarItems(
                leading: Button("Cancel") {
                    presentationMode.wrappedValue.dismiss()
                }
            )
            .onAppear {
                Task {
                    await storeKitService.loadProducts()
                }
            }
            .alert("Purchase Successful", isPresented: $showingPurchaseConfirmation) {
                Button("Continue") {
                    presentationMode.wrappedValue.dismiss()
                }
            } message: {
                Text("Welcome to Fair-Edge Premium! You now have access to all features.")
            }
            .alert("Error", isPresented: .constant(storeKitService.errorMessage != nil)) {
                Button("OK") {
                    storeKitService.errorMessage = nil
                }
            } message: {
                if let errorMessage = storeKitService.errorMessage {
                    Text(errorMessage)
                }
            }
        }
    }
    
    // MARK: - Header Section
    
    private var headerSection: some View {
        VStack(spacing: 16) {
            Image(systemName: "chart.line.uptrend.xyaxis.circle.fill")
                .font(.system(size: 60))
                .foregroundColor(.blue)
            
            Text("Unlock Premium Features")
                .font(.title)
                .fontWeight(.bold)
                .multilineTextAlignment(.center)
            
            Text("Get access to all betting opportunities, advanced filtering, and exclusive features")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
    }
    
    // MARK: - Feature Comparison Section
    
    private var featureComparisonSection: some View {
        VStack(spacing: 16) {
            Text("Feature Comparison")
                .font(.headline)
                .fontWeight(.semibold)
            
            VStack(spacing: 12) {
                featureRow(title: "Betting Opportunities", free: "Limited to 10", premium: "Unlimited")
                featureRow(title: "Market Types", free: "Main lines only", premium: "All markets + props")
                featureRow(title: "Search & Filter", free: "Basic", premium: "Advanced filtering")
                featureRow(title: "Push Notifications", free: "❌", premium: "✅")
                featureRow(title: "Data Export", free: "❌", premium: "✅")
                featureRow(title: "Real-time Updates", free: "❌", premium: "✅")
                featureRow(title: "EV Threshold Alerts", free: "❌", premium: "✅")
            }
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(12)
        }
    }
    
    private func featureRow(title: String, free: String, premium: String) -> some View {
        HStack {
            Text(title)
                .font(.subheadline)
                .frame(maxWidth: .infinity, alignment: .leading)
            
            VStack(spacing: 4) {
                Text("Free")
                    .font(.caption)
                    .foregroundColor(.secondary)
                Text(free)
                    .font(.caption)
                    .foregroundColor(free.contains("❌") ? .red : .secondary)
            }
            .frame(width: 80)
            
            VStack(spacing: 4) {
                Text("Premium")
                    .font(.caption)
                    .foregroundColor(.blue)
                Text(premium)
                    .font(.caption)
                    .foregroundColor(premium.contains("✅") ? .green : .blue)
            }
            .frame(width: 80)
        }
    }
    
    // MARK: - Pricing Plans Section
    
    private var pricingPlansSection: some View {
        VStack(spacing: 16) {
            Text("Choose Your Plan")
                .font(.headline)
                .fontWeight(.semibold)
            
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 16) {
                ForEach(storeKitService.availableProducts, id: \.id) { product in
                    PricingCardView(
                        product: product,
                        isSelected: selectedProduct?.id == product.id,
                        onTap: {
                            selectedProduct = product
                        }
                    )
                }
            }
        }
    }
    
    // MARK: - Purchase Button Section
    
    private var purchaseButtonSection: some View {
        VStack(spacing: 12) {
            if let product = selectedProduct {
                Button(action: {
                    Task {
                        do {
                            if let _ = try await storeKitService.purchase(product) {
                                showingPurchaseConfirmation = true
                            }
                        } catch {
                            // Error is handled by StoreKitService
                        }
                    }
                }) {
                    HStack {
                        if storeKitService.isLoading {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                .scaleEffect(0.8)
                        }
                        
                        Text(storeKitService.isLoading ? "Processing..." : "Subscribe to \(product.displayName)")
                            .font(.headline)
                            .foregroundColor(.white)
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .cornerRadius(12)
                }
                .disabled(storeKitService.isLoading)
                
                Text("Cancel anytime in Settings")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
            } else {
                Text("Select a plan to continue")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(Color(.systemGray5))
                    .cornerRadius(12)
            }
        }
    }
    
    // MARK: - Restore Purchases Section
    
    private var restorePurchasesSection: some View {
        VStack(spacing: 8) {
            Divider()
            
            Button("Restore Purchases") {
                Task {
                    do {
                        try await storeKitService.restorePurchases()
                        // Check if restoration was successful
                        if storeKitService.hasActiveSubscription {
                            presentationMode.wrappedValue.dismiss()
                        }
                    } catch {
                        // Error is handled by StoreKitService
                    }
                }
            }
            .foregroundColor(.blue)
            .disabled(storeKitService.isLoading)
            
            Text("Already purchased? Restore your subscription")
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }
    
    // MARK: - Legal Links Section
    
    private var legalLinksSection: some View {
        VStack(spacing: 8) {
            HStack {
                Button("Terms of Service") {
                    showingTerms = true
                }
                .font(.caption)
                .foregroundColor(.blue)
                
                Text("•")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Button("Privacy Policy") {
                    showingPrivacy = true
                }
                .font(.caption)
                .foregroundColor(.blue)
            }
            
            Text("Subscriptions auto-renew unless cancelled 24 hours before the end of the current period")
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
        .sheet(isPresented: $showingTerms) {
            WebView(url: "https://fair-edge.com/terms")
        }
        .sheet(isPresented: $showingPrivacy) {
            PrivacyPolicyView()
        }
    }
}

// MARK: - Pricing Card View

struct PricingCardView: View {
    let product: Product
    let isSelected: Bool
    let onTap: () -> Void
    
    private var productIdentifier: StoreKitService.ProductIdentifier? {
        return StoreKitService.ProductIdentifier(rawValue: product.id)
    }
    
    private var isPopular: Bool {
        return product.id == "com.fairedge.premium_yearly"
    }
    
    private var savings: String? {
        if product.id == "com.fairedge.premium_yearly" {
            return "Save 25%"
        }
        return nil
    }
    
    var body: some View {
        VStack(spacing: 12) {
            // Popular badge
            if isPopular {
                Text("Most Popular")
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.white)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 4)
                    .background(Color.orange)
                    .cornerRadius(12)
            }
            
            // Product name
            Text(productIdentifier?.displayName ?? product.displayName)
                .font(.headline)
                .fontWeight(.semibold)
                .multilineTextAlignment(.center)
            
            // Price
            Text(product.displayPrice)
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(.blue)
            
            // Period
            if let subscription = product.subscription {
                Text("per \(subscription.subscriptionPeriod.localizedDescription)")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            
            // Savings
            if let savings = savings {
                Text(savings)
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .foregroundColor(.green)
            }
            
            // Features
            VStack(alignment: .leading, spacing: 4) {
                featureBullet("All betting opportunities")
                featureBullet("Advanced filtering")
                featureBullet("Push notifications")
                if product.id.contains("premium") {
                    featureBullet("Data export")
                    featureBullet("Real-time updates")
                }
            }
            .padding(.top, 8)
            
            Spacer()
        }
        .padding()
        .frame(maxWidth: .infinity, minHeight: 200)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(isSelected ? Color.blue.opacity(0.1) : Color(.systemGray6))
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(isSelected ? Color.blue : Color.clear, lineWidth: 2)
                )
        )
        .onTapGesture {
            onTap()
        }
    }
    
    private func featureBullet(_ text: String) -> some View {
        HStack(spacing: 6) {
            Image(systemName: "checkmark.circle.fill")
                .font(.caption)
                .foregroundColor(.green)
            Text(text)
                .font(.caption)
                .foregroundColor(.primary)
            Spacer()
        }
    }
}

// MARK: - Web View for Terms and Privacy

struct WebView: View {
    let url: String
    @Environment(\.presentationMode) var presentationMode
    
    var body: some View {
        NavigationView {
            VStack {
                Text("Loading...")
                    .foregroundColor(.secondary)
                Spacer()
            }
            .navigationTitle("Legal")
            .navigationBarItems(
                trailing: Button("Done") {
                    presentationMode.wrappedValue.dismiss()
                }
            )
        }
    }
}

// MARK: - Preview

struct PaywallView_Previews: PreviewProvider {
    static var previews: some View {
        PaywallView()
            .environmentObject(AuthenticationService())
    }
}