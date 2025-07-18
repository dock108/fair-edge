//
//  PrivacyPolicyView.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import SwiftUI

/// Comprehensive Privacy Policy view for App Store compliance
struct PrivacyPolicyView: View {
    @Environment(\.presentationMode) var presentationMode
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Header
                    headerSection
                    
                    // Information We Collect
                    informationCollectionSection
                    
                    // How We Use Information
                    informationUsageSection
                    
                    // Data Sharing
                    dataSharingSection
                    
                    // Data Security
                    dataSecuritySection
                    
                    // Your Rights
                    userRightsSection
                    
                    // Third-Party Services
                    thirdPartySection
                    
                    // Push Notifications
                    notificationSection
                    
                    // Subscription Information
                    subscriptionSection
                    
                    // Children's Privacy
                    childrensPrivacySection
                    
                    // Changes to Policy
                    policyChangesSection
                    
                    // Contact Information
                    contactSection
                }
                .padding()
            }
            .navigationTitle("Privacy Policy")
            .navigationBarItems(
                trailing: Button("Done") {
                    presentationMode.wrappedValue.dismiss()
                }
            )
        }
    }
    
    // MARK: - Privacy Policy Sections
    
    private var headerSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Fair-Edge Privacy Policy")
                .font(.title)
                .fontWeight(.bold)
            
            Text("Effective Date: January 18, 2025")
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            Text("Fair-Edge (\"we,\" \"our,\" or \"us\") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, and share information about you when you use our mobile application and services.")
                .font(.body)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
    
    private var informationCollectionSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Information We Collect")
            
            subsectionText("Account Information", """
            • Email address for account creation and authentication
            • User preferences for sports, notification settings, and subscription status
            • Device identifiers for push notifications and security
            """)
            
            subsectionText("Usage Data", """
            • App usage patterns and feature interactions
            • Betting opportunities viewed and filtering preferences
            • Performance data for app optimization
            • Crash reports and error logs for debugging
            """)
            
            subsectionText("Device Information", """
            • Device type, operating system version, and app version
            • Network information for API connectivity
            • Push notification tokens for alert delivery
            • Location data (if permitted) for region-specific content
            """)
            
            subsectionText("Subscription Data", """
            • Apple App Store subscription status and transaction history
            • Purchase receipts for subscription validation
            • Payment processing information (handled by Apple)
            """)
        }
    }
    
    private var informationUsageSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("How We Use Your Information")
            
            Text("We use the information we collect to:")
                .font(.subheadline)
                .fontWeight(.semibold)
            
            Text("""
            • Provide and improve our betting analysis services
            • Deliver personalized betting opportunities and notifications
            • Process and manage your subscription
            • Authenticate your account and ensure security
            • Analyze app usage to improve performance and features
            • Provide customer support and respond to inquiries
            • Comply with legal obligations and protect our rights
            • Send important updates about service changes
            """)
                .font(.body)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
    
    private var dataSharingSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Information Sharing and Disclosure")
            
            Text("We do not sell your personal information. We may share your information in the following circumstances:")
                .font(.body)
                .fontWeight(.medium)
            
            subsectionText("Service Providers", """
            • Apple App Store for subscription processing
            • Cloud infrastructure providers for app hosting
            • Analytics services for app performance monitoring
            • Customer support platforms for user assistance
            """)
            
            subsectionText("Legal Requirements", """
            • When required by law, regulation, or legal process
            • To protect the rights, property, or safety of Fair-Edge or others
            • In connection with a merger, acquisition, or sale of assets
            """)
            
            Text("We ensure all third-party providers have appropriate data protection measures in place.")
                .font(.caption)
                .foregroundColor(.secondary)
                .italic()
        }
    }
    
    private var dataSecuritySection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Data Security")
            
            Text("""
            We implement industry-standard security measures to protect your information:
            
            • Encryption in transit using TLS/SSL protocols
            • Secure authentication with JWT tokens
            • Regular security audits and updates
            • Limited access to personal data on a need-to-know basis
            • Secure data storage with reputable cloud providers
            
            While we strive to protect your information, no method of transmission over the internet is 100% secure.
            """)
                .font(.body)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
    
    private var userRightsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Your Privacy Rights")
            
            Text("You have the following rights regarding your personal information:")
                .font(.body)
                .fontWeight(.medium)
            
            Text("""
            • Access: Request access to your personal information
            • Correction: Request correction of inaccurate information
            • Deletion: Request deletion of your personal information
            • Portability: Request a copy of your data in a portable format
            • Opt-out: Unsubscribe from marketing communications
            • Notification Control: Manage push notification preferences
            
            To exercise these rights, contact us at privacy@fair-edge.com
            """)
                .font(.body)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
    
    private var thirdPartySection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Third-Party Services")
            
            Text("Our app integrates with the following third-party services:")
                .font(.body)
                .fontWeight(.medium)
            
            subsectionText("Apple Services", """
            • Sign in with Apple for authentication
            • Apple Push Notification Service for alerts
            • App Store for subscription management
            • StoreKit for in-app purchases
            """)
            
            subsectionText("Sports Data Providers", """
            • Licensed sports data APIs for betting odds
            • Real-time sports information services
            • Market data providers for EV calculations
            """)
            
            Text("Each third-party service has its own privacy policy. We encourage you to review their policies.")
                .font(.caption)
                .foregroundColor(.secondary)
                .italic()
        }
    }
    
    private var notificationSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Push Notifications")
            
            Text("""
            Fair-Edge sends push notifications to provide timely betting opportunities and important updates:
            
            • High-value betting opportunity alerts
            • Subscription status and renewal reminders
            • Important app updates and announcements
            • Security alerts and account notifications
            
            You can control notification preferences in the app settings or your device settings. Disabling notifications may affect your ability to receive timely betting opportunities.
            """)
                .font(.body)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
    
    private var subscriptionSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Subscription Information")
            
            Text("""
            Fair-Edge offers subscription services with the following terms:
            
            • Subscriptions are processed through the Apple App Store
            • Payment is charged to your Apple ID account
            • Subscriptions auto-renew unless cancelled 24 hours before expiration
            • You can manage subscriptions in your Apple ID Account Settings
            • Refunds are subject to Apple's refund policy
            
            Subscription Features:
            • Basic Plan: Access to main betting lines and opportunities
            • Premium Plan: All markets, advanced features, and real-time updates
            
            We do not store your payment information - all transactions are handled securely by Apple.
            """)
                .font(.body)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
    
    private var childrensPrivacySection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Children's Privacy")
            
            Text("""
            Fair-Edge is intended for users 18 years of age and older. We do not knowingly collect personal information from children under 18. 
            
            If you are a parent or guardian and believe your child has provided us with personal information, please contact us immediately at privacy@fair-edge.com.
            
            Sports betting and gambling are restricted to adults in most jurisdictions. Users are responsible for complying with local laws and regulations.
            """)
                .font(.body)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
    
    private var policyChangesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Changes to This Privacy Policy")
            
            Text("""
            We may update this Privacy Policy from time to time. We will notify you of any material changes by:
            
            • Posting the updated policy in the app
            • Sending a push notification about policy changes
            • Updating the "Effective Date" at the top of this policy
            
            Your continued use of Fair-Edge after any changes indicates your acceptance of the updated Privacy Policy.
            """)
                .font(.body)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
    
    private var contactSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Contact Us")
            
            Text("""
            If you have any questions about this Privacy Policy or our privacy practices, please contact us:
            
            Email: privacy@fair-edge.com
            Website: https://fair-edge.com/privacy
            
            Fair-Edge Privacy Team
            1234 Sports Analytics Drive
            Data City, DC 12345
            United States
            
            We aim to respond to all privacy inquiries within 30 days.
            """)
                .font(.body)
                .fixedSize(horizontal: false, vertical: true)
            
            Divider()
            
            Text("This Privacy Policy was last updated on January 18, 2025.")
                .font(.caption)
                .foregroundColor(.secondary)
                .italic()
        }
    }
    
    // MARK: - Helper Views
    
    private func sectionHeader(_ title: String) -> some View {
        Text(title)
            .font(.headline)
            .fontWeight(.semibold)
            .padding(.top, 8)
    }
    
    private func subsectionText(_ title: String, _ content: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.subheadline)
                .fontWeight(.medium)
            
            Text(content)
                .font(.body)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}

// MARK: - Preview

struct PrivacyPolicyView_Previews: PreviewProvider {
    static var previews: some View {
        PrivacyPolicyView()
    }
}