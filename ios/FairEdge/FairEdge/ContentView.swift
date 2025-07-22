//
//  ContentView.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var authenticationService: AuthenticationService
    @Environment(\.horizontalSizeClass) var horizontalSizeClass

    var body: some View {
        Group {
            if horizontalSizeClass == .regular {
                // iPad layout with NavigationSplitView
                NavigationSplitView {
                    if authenticationService.isAuthenticated {
                        iPadSidebarView()
                    } else {
                        Text("Sign In Required")
                            .foregroundColor(.secondary)
                    }
                } detail: {
                    if authenticationService.isAuthenticated {
                        OpportunitiesListView()
                    } else {
                        AuthenticationView()
                    }
                }
            } else {
                // iPhone layout with NavigationView
                NavigationView {
                    if authenticationService.isAuthenticated {
                        OpportunitiesListView()
                    } else {
                        AuthenticationView()
                    }
                }
            }
        }
        .onAppear {
            authenticationService.checkAuthenticationStatus()
        }
    }

    // MARK: - iPad Sidebar

    @ViewBuilder
    private func iPadSidebarView() -> some View {
        List {
            Section("Opportunities") {
                NavigationLink(destination: OpportunitiesListView()) {
                    Label("All Opportunities", systemImage: "chart.line.uptrend.xyaxis")
                }

                NavigationLink(destination: OpportunitiesListView()) {
                    Label("High Value (>10%)", systemImage: "star.fill")
                }

                NavigationLink(destination: OpportunitiesListView()) {
                    Label("Recent Updates", systemImage: "clock.fill")
                }
            }

            Section("Sports") {
                NavigationLink(destination: EmptyView()) {
                    Label("NFL", systemImage: "sportscourt.fill")
                }
                NavigationLink(destination: EmptyView()) {
                    Label("NBA", systemImage: "basketball.fill")
                }
                NavigationLink(destination: EmptyView()) {
                    Label("MLB", systemImage: "baseball.fill")
                }
                NavigationLink(destination: EmptyView()) {
                    Label("NHL", systemImage: "hockey.puck.fill")
                }
            }

            Section("Account") {
                NavigationLink(destination: ProfileView()) {
                    Label("Profile", systemImage: "person.circle")
                }
                NavigationLink(destination: SubscriptionManagementView()) {
                    Label("Subscription", systemImage: "star.circle")
                }
            }
        }
        .listStyle(SidebarListStyle())
        .navigationTitle("Fair-Edge")
    }
}
