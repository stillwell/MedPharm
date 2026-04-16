/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct MainTabView: View {
    @EnvironmentObject var authManager: AuthManager

    var body: some View {
        TabView {
            DashboardView()
                .tabItem { Label("Dashboard", systemImage: "heart.text.square") }
            PrescriptionsView()
                .tabItem { Label("Prescriptions", systemImage: "pill") }
            BillingView()
                .tabItem { Label("Billing", systemImage: "dollarsign.circle") }
            AppointmentsView()
                .tabItem { Label("Appointments", systemImage: "calendar") }
            MoreView()
                .tabItem { Label("More", systemImage: "ellipsis.circle") }
        }
        .tint(.teal)
    }
}
