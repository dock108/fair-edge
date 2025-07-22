//
//  NotificationSettingsView.swift
//  FairEdge
//
//  Created by Fair-Edge on 1/18/25.
//

import SwiftUI
import UserNotifications

/// Notification settings and preferences view
struct NotificationSettingsView: View {
    @EnvironmentObject var pushNotificationService: PushNotificationService
    @Environment(\.presentationMode) var presentationMode

    @State private var evThreshold: Double = UserDefaults.standard.notificationEVThreshold
    @State private var enabledSports: Set<String> = Set(UserDefaults.standard.notificationEnabledSports)
    @State private var quietHoursEnabled: Bool = UserDefaults.standard.notificationQuietHoursEnabled
    @State private var quietHoursStart: Int = UserDefaults.standard.notificationQuietHoursStart
    @State private var quietHoursEnd: Int = UserDefaults.standard.notificationQuietHoursEnd

    private let availableSports = ["NFL", "NBA", "MLB", "NHL", "Soccer"]

    var body: some View {
        NavigationView {
            List {
                // Permission status section
                permissionStatusSection

                // EV threshold section
                evThresholdSection

                // Sports selection section
                sportsSelectionSection

                // Quiet hours section
                quietHoursSection

                // Test notification section
                testNotificationSection
            }
            .navigationTitle("Notifications")
            .navigationBarItems(
                leading: Button("Cancel") {
                    presentationMode.wrappedValue.dismiss()
                },
                trailing: Button("Save") {
                    saveSettings()
                    presentationMode.wrappedValue.dismiss()
                }
            )
        }
    }

    // MARK: - Permission Status Section

    private var permissionStatusSection: some View {
        Section {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Image(systemName: notificationStatusIcon)
                        .foregroundColor(notificationStatusColor)
                        .font(.title2)

                    VStack(alignment: .leading, spacing: 2) {
                        Text("Notification Status")
                            .font(.headline)
                        Text(notificationStatusText)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }

                    Spacer()
                }

                if pushNotificationService.authorizationStatus == .denied {
                    Button("Open Settings") {
                        pushNotificationService.openNotificationSettings()
                    }
                    .buttonStyle(.borderedProminent)
                } else if pushNotificationService.authorizationStatus == .notDetermined {
                    Button("Enable Notifications") {
                        Task {
                            await pushNotificationService.requestNotificationPermissions()
                        }
                    }
                    .buttonStyle(.borderedProminent)
                }
            }
            .padding(.vertical, 4)
        }
    }

    // MARK: - EV Threshold Section

    private var evThresholdSection: some View {
        Section("Opportunity Alerts") {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Text("Minimum EV for Alerts:")
                    Spacer()
                    Text(evThreshold.asPercentage())
                        .fontWeight(.medium)
                        .foregroundColor(.blue)
                }

                Slider(value: $evThreshold, in: 1...20, step: 0.5)
                    .accentColor(.blue)

                HStack {
                    Text("1%")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                    Text("20%")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Text("You'll receive notifications for opportunities with EV above this threshold")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(.vertical, 4)
        }
    }

    // MARK: - Sports Selection Section

    private var sportsSelectionSection: some View {
        Section("Sports") {
            VStack(alignment: .leading, spacing: 8) {
                Text("Receive notifications for:")
                    .font(.subheadline)
                    .foregroundColor(.secondary)

                ForEach(availableSports, id: \.self) { sport in
                    HStack {
                        Button(action: {
                            if enabledSports.contains(sport) {
                                enabledSports.remove(sport)
                            } else {
                                enabledSports.insert(sport)
                            }
                        }, label: {
                            HStack {
                                Image(systemName: enabledSports.contains(sport) ? "checkmark.square.fill" : "square")
                                    .foregroundColor(enabledSports.contains(sport) ? .blue : .gray)

                                Text(sport)
                                    .foregroundColor(.primary)

                                Spacer()
                            }
                        }
                        .buttonStyle(PlainButtonStyle())
                    }
                }
            }
            .padding(.vertical, 4)
        }
    }

    // MARK: - Quiet Hours Section

    private var quietHoursSection: some View {
        Section("Quiet Hours") {
            Toggle("Enable Quiet Hours", isOn: $quietHoursEnabled)

            if quietHoursEnabled {
                VStack(spacing: 12) {
                    HStack {
                        Text("Start Time:")
                        Spacer()
                        Picker("Start", selection: $quietHoursStart) {
                            ForEach(0..<24, id: \.self) { hour in
                                Text(formatHour(hour)).tag(hour)
                            }
                        }
                        .pickerStyle(MenuPickerStyle())
                    }

                    HStack {
                        Text("End Time:")
                        Spacer()
                        Picker("End", selection: $quietHoursEnd) {
                            ForEach(0..<24, id: \.self) { hour in
                                Text(formatHour(hour)).tag(hour)
                            }
                        }
                        .pickerStyle(MenuPickerStyle())
                    }

                    Text("No notifications will be sent during quiet hours")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.vertical, 4)
            }
        }
    }

    // MARK: - Test Notification Section

    private var testNotificationSection: some View {
        Section("Test") {
            Button("Send Test Notification") {
                sendTestNotification()
            }
            .disabled(pushNotificationService.authorizationStatus != .authorized)

            Text("Send a test notification to verify your settings")
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }

    // MARK: - Helper Properties

    private var notificationStatusIcon: String {
        switch pushNotificationService.authorizationStatus {
        case .authorized:
            return "checkmark.circle.fill"
        case .denied:
            return "xmark.circle.fill"
        case .notDetermined:
            return "questionmark.circle.fill"
        case .provisional:
            return "exclamationmark.circle.fill"
        case .ephemeral:
            return "clock.circle.fill"
        @unknown default:
            return "questionmark.circle.fill"
        }
    }

    private var notificationStatusColor: Color {
        switch pushNotificationService.authorizationStatus {
        case .authorized:
            return .green
        case .denied:
            return .red
        case .notDetermined:
            return .orange
        case .provisional:
            return .yellow
        case .ephemeral:
            return .blue
        @unknown default:
            return .gray
        }
    }

    private var notificationStatusText: String {
        switch pushNotificationService.authorizationStatus {
        case .authorized:
            return "Notifications are enabled"
        case .denied:
            return "Notifications are disabled. Enable in Settings to receive alerts."
        case .notDetermined:
            return "Notification permission not requested"
        case .provisional:
            return "Provisional authorization granted"
        case .ephemeral:
            return "Ephemeral authorization granted"
        @unknown default:
            return "Unknown notification status"
        }
    }

    // MARK: - Helper Methods

    private func formatHour(_ hour: Int) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "h:mm a"

        let calendar = Calendar.current
        let date = calendar.date(bySettingHour: hour, minute: 0, second: 0, of: Date()) ?? Date()

        return formatter.string(from: date)
    }

    private func saveSettings() {
        UserDefaults.standard.notificationEVThreshold = evThreshold
        UserDefaults.standard.notificationEnabledSports = Array(enabledSports)
        UserDefaults.standard.notificationQuietHoursEnabled = quietHoursEnabled
        UserDefaults.standard.notificationQuietHoursStart = quietHoursStart
        UserDefaults.standard.notificationQuietHoursEnd = quietHoursEnd
    }

    private func sendTestNotification() {
        let testOpportunity = BettingOpportunity(
            id: "test_notification",
            event: "Test Game vs. Sample Team",
            betDesc: "Test bet description",
            betType: "Moneyline",
            evPct: evThreshold + 1.0,
            evClass: .great,
            bestOdds: "+150",
            bestSource: "Test Sportsbook",
            fairOdds: "+120",
            sport: "Test Sport",
            actionUrl: nil
        )

        pushNotificationService.scheduleOpportunityAlert(for: testOpportunity)
    }
}

// MARK: - Preview

struct NotificationSettingsView_Previews: PreviewProvider {
    static var previews: some View {
        NotificationSettingsView()
            .environmentObject(PushNotificationService())
    }
}
