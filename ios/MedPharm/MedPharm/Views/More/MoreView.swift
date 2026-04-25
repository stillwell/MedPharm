/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct MoreView: View {
    @EnvironmentObject var authManager: AuthManager

    var body: some View {
        NavigationStack {
            List {
                Section {
                    NavigationLink(destination: MessagesView()) {
                        Label("Messages", systemImage: "bubble.left.and.bubble.right")
                    }
                    NavigationLink(destination: RecordsView()) {
                        Label("Medical Records", systemImage: "doc.text")
                    }
                    NavigationLink(destination: MedicationsView()) {
                        Label("Medications", systemImage: "pills")
                    }
                    NavigationLink(destination: SymptomsView()) {
                        Label("Symptoms & Conditions", systemImage: "stethoscope")
                    }
                }
                Section("Account") {
                    NavigationLink(destination: ProfileView()) {
                        Label("Profile", systemImage: "person.crop.circle")
                    }
                    NavigationLink(destination: NotificationsView()) {
                        Label("Notifications", systemImage: "bell")
                    }
                }
                Section {
                    Button(role: .destructive) {
                        Task { await authManager.logout() }
                    } label: {
                        Label("Log Out", systemImage: "rectangle.portrait.and.arrow.right")
                    }
                }
                Section {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("MedPharm ERP").font(.caption).bold()
                        Text("Version 1.7.6").font(.caption2).foregroundColor(.secondary)
                        Text("© 2026 Enlightec Ltd.").font(.caption2).foregroundColor(.secondary)
                    }
                }
            }
            .navigationTitle("More")
        }
    }
}
