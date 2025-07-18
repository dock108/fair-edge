//
//  ProfileView.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import SwiftUI

/// User profile and settings view
struct ProfileView: View {
    @EnvironmentObject var authenticationService: AuthenticationService
    @EnvironmentObject var storeKitService: StoreKitService
    @EnvironmentObject var pushNotificationService: PushNotificationService
    @Environment(\.presentationMode) var presentationMode
    
    @State private var showingPaywall = false
    @State private var showingSubscriptionManagement = false
    @State private var showingNotificationSettings = false
    
    var body: some View {
        NavigationView {
            List {
                // User info section
                userInfoSection
                
                // Subscription section
                subscriptionSection
                
                // App settings section
                appSettingsSection
                
                // About section
                aboutSection
                
                // Sign out section
                signOutSection
            }
            .navigationTitle("Profile")
            .navigationBarItems(trailing: Button("Done") {
                presentationMode.wrappedValue.dismiss()
            })
            .sheet(isPresented: $showingPaywall) {
                PaywallView()
            }
            .sheet(isPresented: $showingSubscriptionManagement) {
                SubscriptionManagementView()
            }
            .sheet(isPresented: $showingNotificationSettings) {
                NotificationSettingsView()
            }
        }
    }
    
    // MARK: - User Info Section
    
    private var userInfoSection: some View {
        Section {
            if let user = authenticationService.currentUser {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Image(systemName: "person.circle.fill")
                            .font(.title)
                            .foregroundColor(.blue)
                        
                        VStack(alignment: .leading, spacing: 2) {
                            Text(user.displayName)
                                .font(.headline)
                            
                            Text(user.email)
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                    }
                    
                    HStack {
                        subscriptionBadge(for: user.role)
                        
                        Spacer()
                        
                        if user.subscriptionStatus.isActive {
                            Text("✓ Active")
                                .font(.caption)
                                .foregroundColor(.green)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 2)
                                .background(Color.green.opacity(0.1))
                                .cornerRadius(4)
                        }
                    }
                }
                .padding(.vertical, 8)
            }
        }
    }
    
    // MARK: - Subscription Section
    
    private var subscriptionSection: some View {
        Section("Subscription") {
            if let user = authenticationService.currentUser {
                HStack {
                    Image(systemName: "star.circle.fill")
                        .foregroundColor(.purple)
                    
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Current Plan")
                            .font(.subheadline)
                        Text(user.role.displayName)
                            .font(.headline)
                            .fontWeight(.semibold)
                    }
                    
                    Spacer()
                    
                    if storeKitService.hasActiveSubscription {
                        Text("Active")
                            .font(.caption)
                            .foregroundColor(.green)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 2)
                            .background(Color.green.opacity(0.1))
                            .cornerRadius(4)
                    }
                }
                
                if storeKitService.hasActiveSubscription {
                    Button(action: {
                        showingSubscriptionManagement = true
                    }) {
                        HStack {
                            Image(systemName: "gearshape")
                                .foregroundColor(.blue)
                            Text("Manage Subscription")
                            Spacer()
                            Image(systemName: "chevron.right")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                } else {
                    Button(action: {
                        showingPaywall = true
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
    
    // MARK: - App Settings Section
    
    private var appSettingsSection: some View {
        Section("Settings") {
            Button(action: {
                showingNotificationSettings = true
            }) {
                HStack {
                    Image(systemName: "bell")
                        .foregroundColor(.orange)
                    Text("Notifications")
                    Spacer()
                    
                    if pushNotificationService.authorizationStatus == .authorized {
                        Text("Enabled")
                            .foregroundColor(.green)
                    } else {
                        Text("Disabled")
                            .foregroundColor(.red)
                    }
                    
                    Image(systemName: "chevron.right")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            HStack {
                Image(systemName: "slider.horizontal.3")
                    .foregroundColor(.blue)
                Text("EV Threshold")
                Spacer()
                Text("\(UserDefaults.standard.evThreshold.asPercentage())")
                    .foregroundColor(.secondary)
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            HStack {
                Image(systemName: "sportscourt")
                    .foregroundColor(.green)
                Text("Favorite Sports")
                Spacer()
                Text("All")
                    .foregroundColor(.secondary)
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
    }
    
    // MARK: - About Section
    
    private var aboutSection: some View {
        Section("About") {
            HStack {
                Image(systemName: "info.circle")
                    .foregroundColor(.blue)
                Text("App Version")
                Spacer()
                Text(Bundle.main.fullVersion)
                    .foregroundColor(.secondary)
            }
            
            HStack {
                Image(systemName: "network")
                    .foregroundColor(.green)
                Text("API Status")
                Spacer()
                Text("Connected")
                    .foregroundColor(.green)
            }
            
            HStack {
                Image(systemName: "doc.text")
                    .foregroundColor(.gray)
                Text("Privacy Policy")
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            HStack {
                Image(systemName: "questionmark.circle")
                    .foregroundColor(.gray)
                Text("Support")
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
    }
    
    // MARK: - Sign Out Section
    
    private var signOutSection: some View {
        Section {
            Button(action: {
                authenticationService.signOut()
                presentationMode.wrappedValue.dismiss()
            }) {
                HStack {
                    Image(systemName: "rectangle.portrait.and.arrow.right")
                        .foregroundColor(.red)
                    Text("Sign Out")
                        .foregroundColor(.red)
                }
            }
        }
    }
    
    // MARK: - Helper Views
    
    private func subscriptionBadge(for role: UserRole) -> some View {
        Text(role.displayName)
            .font(.caption)
            .fontWeight(.medium)
            .foregroundColor(badgeTextColor(for: role))
            .padding(.horizontal, 8)
            .padding(.vertical, 2)
            .background(badgeBackgroundColor(for: role))
            .cornerRadius(4)
    }
    
    private func badgeTextColor(for role: UserRole) -> Color {
        switch role {
        case .free:
            return .gray
        case .basic:
            return .blue
        case .premium:
            return .purple
        case .admin:
            return .red
        }
    }
    
    private func badgeBackgroundColor(for role: UserRole) -> Color {
        switch role {
        case .free:
            return .gray.opacity(0.1)
        case .basic:
            return .blue.opacity(0.1)
        case .premium:
            return .purple.opacity(0.1)
        case .admin:
            return .red.opacity(0.1)
        }
    }
}

// MARK: - Preview

struct ProfileView_Previews: PreviewProvider {
    static var previews: some View {
        ProfileView()
            .environmentObject(AuthenticationService())
    }
}