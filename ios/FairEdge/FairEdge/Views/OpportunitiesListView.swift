//
//  OpportunitiesListView.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import SwiftUI

/// Main opportunities list view with mobile-optimized display
struct OpportunitiesListView: View {
    @StateObject private var viewModel = OpportunitiesViewModel()
    @EnvironmentObject var authenticationService: AuthenticationService
    @EnvironmentObject var storeKitService: StoreKitService
    @EnvironmentObject var pushNotificationService: PushNotificationService
    
    @State private var showingFilters = false
    @State private var showingProfile = false
    @State private var showingPaywall = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Status bar
                statusBar
                
                // Opportunities list
                opportunitiesList
            }
            .navigationTitle("Fair-Edge")
            .navigationBarItems(
                leading: profileButton,
                trailing: HStack {
                    filterButton
                    refreshButton
                }
            )
            .searchable(text: $viewModel.searchText, prompt: "Search opportunities...")
            .sheet(isPresented: $showingFilters) {
                FiltersView(viewModel: viewModel)
            }
            .sheet(isPresented: $showingProfile) {
                ProfileView()
            }
            .sheet(isPresented: $showingPaywall) {
                PaywallView()
            }
            .onAppear {
                viewModel.loadOpportunities()
                
                // Request notification permissions for authenticated users
                if authenticationService.isAuthenticated {
                    Task {
                        await pushNotificationService.requestNotificationPermissions()
                    }
                }
            }
        }
    }
    
    // MARK: - Status Bar
    
    private var statusBar: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(viewModel.statusText)
                    .font(.caption)
                    .foregroundColor(.primary)
                
                HStack(spacing: 8) {
                    Text(viewModel.cacheStatusText)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    
                    if !viewModel.performanceText.isEmpty {
                        Text(viewModel.performanceText)
                            .font(.caption2)
                            .foregroundColor(.green)
                    }
                }
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 2) {
                if viewModel.filteredOpportunities.count > 0 {
                    Text("Avg EV: \(viewModel.averageEV.asPercentage())")
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundColor(.blue)
                }
                
                Text("Updated \(viewModel.lastUpdateText)")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
        .background(Color(.systemGray6))
    }
    
    // MARK: - Opportunities List
    
    private var opportunitiesList: some View {
        Group {
            if viewModel.isLoading && viewModel.opportunities.isEmpty {
                LoadingView()
            } else if viewModel.filteredOpportunities.isEmpty {
                EmptyStateView(
                    title: "No Opportunities",
                    message: viewModel.searchText.isEmpty ? 
                        "Check back soon for new betting opportunities" : 
                        "No opportunities match your search",
                    systemImage: "magnifyingglass"
                )
            } else {
                List {
                    // Show limited opportunities for free users
                    ForEach(limitedOpportunities) { opportunity in
                        OpportunityRowView(opportunity: opportunity)
                            .listRowInsets(EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16))
                    }
                    
                    // Show upgrade prompt for free users
                    if shouldShowUpgradePrompt {
                        upgradePromptRow
                    }
                }
                .listStyle(PlainListStyle())
                .refreshable {
                    viewModel.refreshOpportunities()
                }
            }
        }
    }
    
    // MARK: - Navigation Bar Items
    
    private var profileButton: some View {
        Button(action: { showingProfile = true }) {
            Image(systemName: "person.circle")
                .font(.title2)
        }
    }
    
    private var filterButton: some View {
        Button(action: { showingFilters = true }) {
            Image(systemName: hasActiveFilters ? "line.horizontal.3.decrease.circle.fill" : "line.horizontal.3.decrease.circle")
                .font(.title2)
                .foregroundColor(hasActiveFilters ? .blue : .primary)
        }
    }
    
    private var refreshButton: some View {
        Button(action: { viewModel.refreshOpportunities() }) {
            Image(systemName: "arrow.clockwise")
                .font(.title2)
                .rotationEffect(.degrees(viewModel.isRefreshing ? 360 : 0))
                .animation(viewModel.isRefreshing ? Animation.linear(duration: 1).repeatForever(autoreverses: false) : .default, value: viewModel.isRefreshing)
        }
        .disabled(viewModel.isRefreshing)
    }
    
    // MARK: - Helper Properties
    
    private var hasActiveFilters: Bool {
        return !viewModel.searchText.isEmpty ||
               viewModel.selectedSport != "All" ||
               viewModel.minimumEV > 0 ||
               viewModel.selectedClassification != nil
    }
    
    private var userRole: UserRole {
        return authenticationService.currentUser?.role ?? .free
    }
    
    private var limitedOpportunities: [BettingOpportunity] {
        let opportunities = viewModel.filteredOpportunities
        
        switch userRole {
        case .free:
            // Free users: Limited to 10 opportunities, main lines only
            return Array(opportunities.prefix(10))
        case .basic, .premium, .admin:
            // Paid users: Full access
            return opportunities
        }
    }
    
    private var shouldShowUpgradePrompt: Bool {
        return userRole == .free && viewModel.filteredOpportunities.count > 10
    }
    
    // MARK: - Upgrade Prompt Row
    
    private var upgradePromptRow: some View {
        VStack(spacing: 16) {
            Image(systemName: "star.circle.fill")
                .font(.system(size: 40))
                .foregroundColor(.blue)
            
            VStack(spacing: 8) {
                Text("Unlock All Opportunities")
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Text("You're seeing \(limitedOpportunities.count) of \(viewModel.filteredOpportunities.count) opportunities. Upgrade to access all betting lines and advanced features.")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
            }
            
            Button(action: {
                showingPaywall = true
            }) {
                Text("Upgrade to Premium")
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .cornerRadius(12)
            }
            
            Text("Starting at $3.99/month")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
        .listRowInsets(EdgeInsets(top: 16, leading: 16, bottom: 16, trailing: 16))
    }
}

// MARK: - Opportunity Row View

struct OpportunityRowView: View {
    let opportunity: BettingOpportunity
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Header with event and EV
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(opportunity.displayEvent)
                        .font(.headline)
                        .lineLimit(2)
                    
                    if let sport = opportunity.sport {
                        Text(sport.uppercased())
                            .font(.caption)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 2)
                            .background(Color.blue.opacity(0.1))
                            .foregroundColor(.blue)
                            .cornerRadius(4)
                    }
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 2) {
                    Text(opportunity.formattedEVPercentage)
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundColor(evColor)
                    
                    Text(opportunity.evClass.displayName)
                        .font(.caption)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 1)
                        .background(evColor.opacity(0.1))
                        .foregroundColor(evColor)
                        .cornerRadius(3)
                }
            }
            
            // Bet description
            Text(opportunity.displayBetDescription)
                .font(.subheadline)
                .foregroundColor(.secondary)
                .lineLimit(2)
            
            // Odds information
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Best Odds")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(opportunity.bestOdds)
                        .font(.subheadline)
                        .fontWeight(.medium)
                }
                
                Spacer()
                
                VStack(alignment: .leading, spacing: 2) {
                    Text("Fair Odds")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(opportunity.fairOdds)
                        .font(.subheadline)
                        .fontWeight(.medium)
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 2) {
                    Text("Source")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(opportunity.bestSource)
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(.blue)
                }
            }
        }
        .padding(.vertical, 4)
        .contentShape(Rectangle())
        .onTapGesture {
            if let actionUrl = opportunity.actionUrl, let url = URL(string: actionUrl) {
                UIApplication.shared.open(url)
            }
        }
    }
    
    private var evColor: Color {
        switch opportunity.evClass {
        case .great:
            return .green
        case .good:
            return .blue
        case .neutral:
            return .gray
        case .poor:
            return .red
        }
    }
}

// MARK: - Loading View

struct LoadingView: View {
    var body: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.5)
            
            Text("Loading opportunities...")
                .font(.headline)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - Empty State View

struct EmptyStateView: View {
    let title: String
    let message: String
    let systemImage: String
    
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: systemImage)
                .font(.system(size: 48))
                .foregroundColor(.gray)
            
            Text(title)
                .font(.title2)
                .fontWeight(.semibold)
            
            Text(message)
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - Preview

struct OpportunitiesListView_Previews: PreviewProvider {
    static var previews: some View {
        OpportunitiesListView()
            .environmentObject(AuthenticationService())
    }
}