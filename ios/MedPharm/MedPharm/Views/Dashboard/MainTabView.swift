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

    init() {
        let appearance = UITabBarAppearance()
        appearance.configureWithOpaqueBackground()
        appearance.backgroundColor = UIColor(MPColor.bg)
        appearance.stackedLayoutAppearance.normal.iconColor = UIColor(MPColor.textMuted)
        appearance.stackedLayoutAppearance.normal.titleTextAttributes = [
            .foregroundColor: UIColor(MPColor.textMuted),
            .font: UIFont.systemFont(ofSize: 10, weight: .semibold)
        ]
        appearance.stackedLayoutAppearance.selected.iconColor = UIColor(MPColor.primary)
        appearance.stackedLayoutAppearance.selected.titleTextAttributes = [
            .foregroundColor: UIColor(MPColor.primary),
            .font: UIFont.systemFont(ofSize: 10, weight: .bold)
        ]
        UITabBar.appearance().standardAppearance = appearance
        UITabBar.appearance().scrollEdgeAppearance = appearance

        let navAppearance = UINavigationBarAppearance()
        navAppearance.configureWithOpaqueBackground()
        navAppearance.backgroundColor = UIColor(MPColor.bg)
        navAppearance.titleTextAttributes = [.foregroundColor: UIColor(MPColor.text)]
        navAppearance.largeTitleTextAttributes = [.foregroundColor: UIColor(MPColor.text)]
        UINavigationBar.appearance().standardAppearance = navAppearance
        UINavigationBar.appearance().scrollEdgeAppearance = navAppearance
    }

    var body: some View {
        TabView {
            DashboardView()
                .tabItem { Label("Dashboard", systemImage: "heart.text.square.fill") }
            PrescriptionsView()
                .tabItem { Label("Prescriptions", systemImage: "pill.fill") }
            BillingView()
                .tabItem { Label("Billing", systemImage: "creditcard.fill") }
            AppointmentsView()
                .tabItem { Label("Appointments", systemImage: "calendar") }
            MoreView()
                .tabItem { Label("More", systemImage: "ellipsis.circle.fill") }
        }
        .tint(MPColor.primary)
        .preferredColorScheme(.dark)
    }
}
