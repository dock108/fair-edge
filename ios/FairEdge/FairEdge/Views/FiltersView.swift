//
//  FiltersView.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import SwiftUI

/// Filters view for customizing opportunities display
struct FiltersView: View {
    @ObservedObject var viewModel: OpportunitiesViewModel
    @Environment(\.presentationMode) var presentationMode
    
    var body: some View {
        NavigationView {
            Form {
                // Sport selection
                sportSection
                
                // EV threshold
                evThresholdSection
                
                // Classification filter
                classificationSection
                
                // Summary
                summarySection
            }
            .navigationTitle("Filters")
            .navigationBarItems(
                leading: Button("Clear All") {
                    viewModel.clearFilters()
                },
                trailing: Button("Done") {
                    presentationMode.wrappedValue.dismiss()
                }
            )
        }
    }
    
    // MARK: - Sport Section
    
    private var sportSection: some View {
        Section("Sport") {
            Picker("Sport", selection: $viewModel.selectedSport) {
                ForEach(viewModel.availableSports, id: \.self) { sport in
                    Text(sport).tag(sport)
                }
            }
            .pickerStyle(SegmentedPickerStyle())
        }
    }
    
    // MARK: - EV Threshold Section
    
    private var evThresholdSection: some View {
        Section("Minimum Expected Value") {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Minimum EV:")
                    Spacer()
                    Text(viewModel.minimumEV.asPercentage())
                        .fontWeight(.medium)
                        .foregroundColor(.blue)
                }
                
                Slider(value: $viewModel.minimumEV, in: 0...20, step: 0.5)
                    .accentColor(.blue)
                
                HStack {
                    Text("0%")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                    Text("20%")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            .padding(.vertical, 4)
        }
    }
    
    // MARK: - Classification Section
    
    private var classificationSection: some View {
        Section("EV Classification") {
            VStack(spacing: 8) {
                ForEach(EVClassification.allCases, id: \.self) { classification in
                    HStack {
                        Button(action: {
                            if viewModel.selectedClassification == classification {
                                viewModel.selectedClassification = nil
                            } else {
                                viewModel.selectedClassification = classification
                            }
                        }) {
                            HStack {
                                Image(systemName: viewModel.selectedClassification == classification ? "checkmark.circle.fill" : "circle")
                                    .foregroundColor(viewModel.selectedClassification == classification ? .blue : .gray)
                                
                                Text(classification.displayName)
                                    .foregroundColor(.primary)
                                
                                Spacer()
                                
                                Text("\(viewModel.count(for: classification))")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 2)
                                    .background(Color(.systemGray5))
                                    .cornerRadius(4)
                            }
                        }
                        .buttonStyle(PlainButtonStyle())
                    }
                }
            }
        }
    }
    
    // MARK: - Summary Section
    
    private var summarySection: some View {
        Section("Filter Summary") {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Total Opportunities:")
                    Spacer()
                    Text("\(viewModel.opportunities.count)")
                        .fontWeight(.medium)
                }
                
                HStack {
                    Text("Filtered Results:")
                    Spacer()
                    Text("\(viewModel.filteredOpportunities.count)")
                        .fontWeight(.medium)
                        .foregroundColor(.blue)
                }
                
                if viewModel.filteredOpportunities.count > 0 {
                    HStack {
                        Text("Average EV:")
                        Spacer()
                        Text(viewModel.averageEV.asPercentage())
                            .fontWeight(.medium)
                            .foregroundColor(.green)
                    }
                }
            }
        }
    }
}

// MARK: - Preview

struct FiltersView_Previews: PreviewProvider {
    static var previews: some View {
        FiltersView(viewModel: OpportunitiesViewModel())
    }
}