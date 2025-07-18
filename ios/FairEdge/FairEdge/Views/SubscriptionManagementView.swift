//
//  SubscriptionManagementView.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import SwiftUI
import StoreKit

/// Subscription management view for existing subscribers
struct SubscriptionManagementView: View {
    @StateObject private var storeKitService = StoreKitService()
    @EnvironmentObject var authenticationService: AuthenticationService
    @Environment(\.presentationMode) var presentationMode
    
    @State private var subscriptionStatus: SubscriptionStatusResponse?
    @State private var showingCancellationConfirmation = false
    @State private var showingUpgradeOptions = false
    
    var body: some View {
        NavigationView {
            List {
                // Current subscription section
                currentSubscriptionSection
                
                // Usage and features section
                usageFeaturesSection
                
                // Manage subscription section
                manageSubscriptionSection
                
                // Billing information section
                billingInformationSection
                
                // Support section
                supportSection
            }
            .navigationTitle("Subscription")
            .navigationBarItems(
                trailing: Button("Done") {
                    presentationMode.wrappedValue.dismiss()
                }
            )
            .onAppear {
                loadSubscriptionStatus()
            }
            .refreshable {
                loadSubscriptionStatus()
            }
            .sheet(isPresented: $showingUpgradeOptions) {
                PaywallView()
            }
            .alert("Manage Subscription", isPresented: $showingCancellationConfirmation) {
                Button("Cancel Subscription", role: .destructive) {
                    openManageSubscriptions()
                }
                Button("Keep Subscription", role: .cancel) { }
            } message: {
                Text("To cancel your subscription, you'll be redirected to your App Store account settings.")
            }
        }
    }
    
    // MARK: - Current Subscription Section
    
    private var currentSubscriptionSection: some View {
        Section("Current Plan") {
            if let status = subscriptionStatus {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        subscriptionBadge(for: status.currentPlan ?? "Free")
                        
                        Spacer()
                        
                        if status.hasActiveSubscription {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.green)
                        }
                    }
                    
                    if let plan = status.currentPlan {
                        Text(planDisplayName(for: plan))
                            .font(.headline)
                            .fontWeight(.semibold)
                    }
                    
                    Text(subscriptionStatusText(status))
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    
                    if let expirationDate = status.expirationDate {
                        HStack {
                            Image(systemName: "calendar")
                                .foregroundColor(.blue)
                            Text("Expires: \(formatDate(expirationDate))")
                                .font(.subheadline)
                        }
                    }
                    
                    if let nextBillingDate = status.nextBillingDate {
                        HStack {
                            Image(systemName: "creditcard")
                                .foregroundColor(.green)
                            Text("Next billing: \(formatDate(nextBillingDate))")
                                .font(.subheadline)
                        }
                    }
                }
                .padding(.vertical, 4)
            } else {
                HStack {
                    ProgressView()
                        .scaleEffect(0.8)
                    Text("Loading subscription status...")
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 8)
            }
        }
    }
    
    // MARK: - Usage and Features Section
    
    private var usageFeaturesSection: some View {
        Section("Available Features") {
            if let status = subscriptionStatus {
                ForEach(status.features, id: \.self) { feature in
                    HStack {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.green)
                        Text(feature)
                        Spacer()
                    }
                }
                
                if status.canUpgrade && !status.availableUpgrades.isEmpty {
                    Button(action: {
                        showingUpgradeOptions = true
                    }) {
                        HStack {
                            Image(systemName: "arrow.up.circle")
                                .foregroundColor(.blue)
                            Text("Upgrade to Premium")
                            Spacer()
                            Image(systemName: "chevron.right")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
        }
    }
    
    // MARK: - Manage Subscription Section
    
    private var manageSubscriptionSection: some View {
        Section("Manage Subscription") {
            Button(action: {
                Task {
                    do {
                        try await storeKitService.restorePurchases()
                        loadSubscriptionStatus()
                    } catch {
                        // Error handled by StoreKitService
                    }
                }
            }) {
                HStack {
                    Image(systemName: "arrow.clockwise")
                        .foregroundColor(.blue)
                    Text("Restore Purchases")
                    Spacer()
                    if storeKitService.isLoading {
                        ProgressView()
                            .scaleEffect(0.8)
                    }
                }
            }
            .disabled(storeKitService.isLoading)
            
            Button(action: {
                openManageSubscriptions()
            }) {
                HStack {
                    Image(systemName: "gearshape")
                        .foregroundColor(.blue)
                    Text("Manage in App Store")
                    Spacer()
                    Image(systemName: "arrow.up.right")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            if subscriptionStatus?.hasActiveSubscription == true {
                Button(action: {
                    showingCancellationConfirmation = true
                }) {
                    HStack {
                        Image(systemName: "xmark.circle")
                            .foregroundColor(.red)
                        Text("Cancel Subscription")
                            .foregroundColor(.red)
                        Spacer()
                    }
                }
            }
        }
    }
    
    // MARK: - Billing Information Section
    
    private var billingInformationSection: some View {
        Section("Billing Information") {
            Button(action: {
                openManageSubscriptions()
            }) {
                HStack {
                    Image(systemName: "creditcard")
                        .foregroundColor(.blue)
                    Text("Payment Method")
                    Spacer()
                    Text("Manage in App Store")
                        .foregroundColor(.secondary)
                    Image(systemName: "chevron.right")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Button(action: {
                openPurchaseHistory()
            }) {
                HStack {
                    Image(systemName: "doc.text")
                        .foregroundColor(.blue)
                    Text("Purchase History")
                    Spacer()
                    Image(systemName: "chevron.right")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
    }
    
    // MARK: - Support Section
    
    private var supportSection: some View {
        Section("Support") {
            Button(action: {
                openSupportPage()
            }) {
                HStack {
                    Image(systemName: "questionmark.circle")
                        .foregroundColor(.blue)
                    Text("Subscription Help")
                    Spacer()
                    Image(systemName: "chevron.right")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Button(action: {
                sendSupportEmail()
            }) {
                HStack {
                    Image(systemName: "envelope")
                        .foregroundColor(.blue)
                    Text("Contact Support")
                    Spacer()
                    Image(systemName: "chevron.right")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
    }
    
    // MARK: - Helper Methods
    
    private func loadSubscriptionStatus() {
        Task {
            do {
                let apiService = APIService()
                let status = try await apiService.getSubscriptionStatus()
                    .values
                    .first(where: { _ in true })
                
                await MainActor.run {
                    self.subscriptionStatus = status
                }
            } catch {
                print("Failed to load subscription status: \(error)")
            }
        }
    }
    
    private func subscriptionBadge(for plan: String) -> some View {
        Text(plan.capitalized)
            .font(.caption)
            .fontWeight(.medium)
            .foregroundColor(badgeTextColor(for: plan))
            .padding(.horizontal, 8)
            .padding(.vertical, 2)
            .background(badgeBackgroundColor(for: plan))
            .cornerRadius(4)
    }
    
    private func badgeTextColor(for plan: String) -> Color {
        switch plan.lowercased() {
        case "free":
            return .gray
        case "basic":
            return .blue
        case "premium":
            return .purple
        default:
            return .gray
        }
    }
    
    private func badgeBackgroundColor(for plan: String) -> Color {
        switch plan.lowercased() {
        case "free":
            return .gray.opacity(0.1)
        case "basic":
            return .blue.opacity(0.1)
        case "premium":
            return .purple.opacity(0.1)
        default:
            return .gray.opacity(0.1)
        }
    }
    
    private func planDisplayName(for plan: String) -> String {
        switch plan.lowercased() {
        case "basic_monthly":
            return "Basic Monthly Plan"
        case "premium_monthly":
            return "Premium Monthly Plan"
        case "premium_yearly":
            return "Premium Yearly Plan"
        default:
            return plan.capitalized
        }
    }
    
    private func subscriptionStatusText(_ status: SubscriptionStatusResponse) -> String {
        if status.hasActiveSubscription {
            return "Active subscription with auto-renewal"
        } else {
            switch status.subscriptionStatus.lowercased() {
            case "expired":
                return "Subscription expired"
            case "cancelled":
                return "Subscription cancelled"
            case "pending":
                return "Subscription pending"
            default:
                return "No active subscription"
            }
        }
    }
    
    private func formatDate(_ dateString: String) -> String {
        let formatter = ISO8601DateFormatter()
        guard let date = formatter.date(from: dateString) else {
            return dateString
        }
        
        let displayFormatter = DateFormatter()
        displayFormatter.dateStyle = .medium
        displayFormatter.timeStyle = .none
        return displayFormatter.string(from: date)
    }
    
    private func openManageSubscriptions() {
        if let url = URL(string: "https://apps.apple.com/account/subscriptions") {
            UIApplication.shared.open(url)
        }
    }
    
    private func openPurchaseHistory() {
        if let url = URL(string: "https://reportaproblem.apple.com/") {
            UIApplication.shared.open(url)
        }
    }
    
    private func openSupportPage() {
        if let url = URL(string: "https://fair-edge.com/support/subscriptions") {
            UIApplication.shared.open(url)
        }
    }
    
    private func sendSupportEmail() {
        if let url = URL(string: "mailto:support@fair-edge.com?subject=Subscription Support") {
            UIApplication.shared.open(url)
        }
    }
}

// MARK: - Preview

struct SubscriptionManagementView_Previews: PreviewProvider {
    static var previews: some View {
        SubscriptionManagementView()
            .environmentObject(AuthenticationService())
    }
}