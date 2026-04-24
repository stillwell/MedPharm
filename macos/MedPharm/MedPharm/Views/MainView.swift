/*
 * MedPharm ERP - macOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import SwiftUI

enum NavigationDestination: Hashable, CaseIterable {
    case dashboard, prescriptions, billing, appointments, records,
         medications, messages, insurance, profile

    var label: String {
        switch self {
        case .dashboard: return "Dashboard"
        case .prescriptions: return "Prescriptions"
        case .billing: return "Billing & Payments"
        case .appointments: return "Appointments"
        case .records: return "Medical Records"
        case .medications: return "Medications"
        case .messages: return "Messages"
        case .insurance: return "Insurance Claims"
        case .profile: return "Profile"
        }
    }

    var icon: String {
        switch self {
        case .dashboard: return "heart.text.square"
        case .prescriptions: return "pill"
        case .billing: return "dollarsign.circle"
        case .appointments: return "calendar"
        case .records: return "doc.text"
        case .medications: return "pills"
        case .messages: return "bubble.left.and.bubble.right"
        case .insurance: return "shield.checkered"
        case .profile: return "person.crop.circle"
        }
    }
}

struct MainView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var selection: NavigationDestination? = .dashboard

    var body: some View {
        NavigationSplitView {
            ZStack {
                MPColor.bg.ignoresSafeArea()
                List(NavigationDestination.allCases, id: \.self, selection: $selection) { dest in
                    Label(dest.label, systemImage: dest.icon).tag(dest)
                        .foregroundColor(selection == dest ? MPColor.primary : MPColor.textMuted)
                }
                .scrollContentBackground(.hidden)
                .navigationTitle("MedPharm")
                .listStyle(.sidebar)
                .safeAreaInset(edge: .bottom) {
                    VStack(spacing: 0) {
                        Divider().overlay(MPColor.border)
                        Button {
                            Task { await authManager.logout() }
                        } label: {
                            Label("Log Out", systemImage: "rectangle.portrait.and.arrow.right")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(MPColor.danger)
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 10)
                        }
                        .buttonStyle(.borderless)
                        .padding(12)
                    }
                }
            }
        } detail: {
            ZStack {
                MPBackground()
                Group {
                    switch selection ?? .dashboard {
                    case .dashboard: DashboardView()
                    case .prescriptions: PrescriptionsView()
                    case .billing: BillingView()
                    case .appointments: AppointmentsView()
                    case .records: RecordsView()
                    case .medications: MedicationsView()
                    case .messages: MessagesView()
                    case .insurance: InsuranceClaimsView()
                    case .profile: ProfileView()
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .preferredColorScheme(.dark)
    }
}
