//
//  OpportunitiesViewModel.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import Foundation
import Combine

/// ViewModel for betting opportunities with mobile API optimization
class OpportunitiesViewModel: ObservableObject {
    
    // MARK: - Published Properties
    
    @Published var opportunities: [BettingOpportunity] = []
    @Published var filteredOpportunities: [BettingOpportunity] = []
    @Published var isLoading = false
    @Published var isRefreshing = false
    @Published var errorMessage: String?
    @Published var searchText = ""
    @Published var selectedSport: String = "All"
    @Published var minimumEV: Double = 0.0
    @Published var selectedClassification: EVClassification?
    
    // Metadata from mobile API
    @Published var totalCount = 0
    @Published var cacheStatus = "unknown"
    @Published var lastUpdateTime: Date?
    @Published var payloadReduction = ""
    
    // MARK: - Private Properties
    
    private let apiService: APIService
    private var cancellables = Set<AnyCancellable>()
    private var refreshTimer: Timer?
    
    // Available sports for filtering
    let availableSports = ["All", "NFL", "NBA", "MLB", "NHL", "Soccer"]
    
    // MARK: - Initialization
    
    init(apiService: APIService = APIService()) {
        self.apiService = apiService
        setupBindings()
        loadOpportunities()
        startAutoRefresh()
    }
    
    deinit {
        refreshTimer?.invalidate()
    }
    
    // MARK: - Public Methods
    
    /// Load opportunities from mobile-optimized API
    func loadOpportunities() {
        guard !isLoading else { return }
        
        isLoading = true
        errorMessage = nil
        
        apiService.fetchOpportunities()
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { [weak self] completion in
                    self?.isLoading = false
                    self?.isRefreshing = false
                    
                    switch completion {
                    case .finished:
                        break
                    case .failure(let error):
                        self?.errorMessage = error.localizedDescription
                    }
                },
                receiveValue: { [weak self] response in
                    self?.updateOpportunities(response)
                }
            )
            .store(in: &cancellables)
    }
    
    /// Refresh opportunities (pull-to-refresh)
    func refreshOpportunities() {
        guard !isRefreshing else { return }
        
        isRefreshing = true
        loadOpportunities()
    }
    
    /// Clear all filters
    func clearFilters() {
        searchText = ""
        selectedSport = "All"
        minimumEV = 0.0
        selectedClassification = nil
    }
    
    /// Get opportunities count for specific classification
    func count(for classification: EVClassification) -> Int {
        return opportunities.filtered(by: classification).count
    }
    
    /// Get average EV for current opportunities
    var averageEV: Double {
        guard !opportunities.isEmpty else { return 0.0 }
        let total = opportunities.reduce(0.0) { $0 + $1.evPct }
        return total / Double(opportunities.count)
    }
    
    // MARK: - Private Methods
    
    /// Set up Combine bindings for filtering
    private func setupBindings() {
        // Combine search text, sport, EV threshold, and classification filters
        Publishers.CombineLatest4($searchText, $selectedSport, $minimumEV, $selectedClassification)
            .debounce(for: .milliseconds(300), scheduler: RunLoop.main)
            .sink { [weak self] searchText, sport, minEV, classification in
                self?.applyFilters(searchText: searchText, sport: sport, minimumEV: minEV, classification: classification)
            }
            .store(in: &cancellables)
    }
    
    /// Apply all active filters
    private func applyFilters(searchText: String, sport: String, minimumEV: Double, classification: EVClassification?) {
        var filtered = opportunities
        
        // Apply search filter
        if !searchText.isEmpty {
            filtered = filtered.filter { opportunity in
                opportunity.event.localizedCaseInsensitiveContains(searchText) ||
                opportunity.betDesc.localizedCaseInsensitiveContains(searchText) ||
                opportunity.betType.localizedCaseInsensitiveContains(searchText)
            }
        }
        
        // Apply sport filter
        if sport != "All" {
            filtered = filtered.filtered(by: sport)
        }
        
        // Apply minimum EV filter
        if minimumEV > 0 {
            filtered = filtered.filtered(minimumEV: minimumEV)
        }
        
        // Apply classification filter
        if let classification = classification {
            filtered = filtered.filtered(by: classification)
        }
        
        // Sort by EV percentage (highest first)
        filteredOpportunities = filtered.sortedByEV()
    }
    
    /// Update opportunities from API response
    private func updateOpportunities(_ response: OpportunitiesResponse) {
        self.opportunities = response.opportunities
        self.totalCount = response.metadata.totalCount
        self.cacheStatus = response.metadata.cacheStatus
        self.payloadReduction = response.metadata.payloadReduction
        
        // Parse update time
        let formatter = ISO8601DateFormatter()
        self.lastUpdateTime = formatter.date(from: response.metadata.cacheTimestamp)
        
        // Trigger filter reapplication
        applyFilters(
            searchText: searchText,
            sport: selectedSport,
            minimumEV: minimumEV,
            classification: selectedClassification
        )
    }
    
    /// Start automatic refresh timer (every 5 minutes)
    private func startAutoRefresh() {
        refreshTimer = Timer.scheduledTimer(withTimeInterval: 300, repeats: true) { [weak self] _ in
            // Only auto-refresh if app is active and not currently loading
            guard !self?.isLoading ?? true, !self?.isRefreshing ?? true else { return }
            self?.loadOpportunities()
        }
    }
}

// MARK: - Computed Properties for UI

extension OpportunitiesViewModel {
    
    /// Status text for UI display
    var statusText: String {
        if isLoading {
            return "Loading opportunities..."
        } else if isRefreshing {
            return "Refreshing..."
        } else if opportunities.isEmpty {
            return "No opportunities available"
        } else {
            let filtered = filteredOpportunities.count
            let total = opportunities.count
            if filtered == total {
                return "\(total) opportunities"
            } else {
                return "\(filtered) of \(total) opportunities"
            }
        }
    }
    
    /// Cache status for UI display
    var cacheStatusText: String {
        switch cacheStatus {
        case "hit":
            return "📦 Cached"
        case "miss":
            return "🌐 Fresh"
        case "expired":
            return "⏰ Updated"
        default:
            return "❓ Unknown"
        }
    }
    
    /// Last update text for UI
    var lastUpdateText: String {
        guard let lastUpdate = lastUpdateTime else {
            return "Never"
        }
        
        let formatter = RelativeDateTimeFormatter()
        formatter.dateTimeStyle = .named
        return formatter.localizedString(for: lastUpdate, relativeTo: Date())
    }
    
    /// Performance info text
    var performanceText: String {
        if !payloadReduction.isEmpty {
            return "⚡ \(payloadReduction) reduction"
        }
        return ""
    }
}