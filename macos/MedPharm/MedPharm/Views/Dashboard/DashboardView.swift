/*
 * MedPharm ERP - macOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct DashboardView: View {
    @State private var data: DashboardData?
    @State private var isLoading = true

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("Dashboard").font(.largeTitle).bold()

                if isLoading {
                    ProgressView().frame(maxWidth: .infinity).padding(.top, 40)
                } else if let data = data {
                    HStack(spacing: 16) {
                        KPICard(title: "Active Prescriptions",
                                value: "\(data.active_prescriptions)",
                                icon: "pill.fill", color: .teal)
                        KPICard(title: "Upcoming Appointments",
                                value: "\(data.upcoming_appointments)",
                                icon: "calendar", color: .blue)
                        KPICard(title: "Outstanding Balance",
                                value: String(format: "$%.2f", data.outstanding_balance),
                                icon: "dollarsign.circle.fill",
                                color: data.outstanding_balance > 0 ? .orange : .green)
                    }

                    SectionBox(title: "Recent Prescriptions") {
                        if data.recent_prescriptions.isEmpty {
                            Text("None").foregroundColor(.secondary)
                        } else {
                            ForEach(data.recent_prescriptions.prefix(5)) { rx in
                                HStack {
                                    Text(rx.rx_number).font(.headline)
                                    Spacer()
                                    Text(rx.prescriber_name ?? "").font(.caption)
                                        .foregroundColor(.secondary)
                                    StatusBadge(status: rx.status)
                                }
                                .padding(.vertical, 4)
                                Divider()
                            }
                        }
                    }

                    SectionBox(title: "Next Appointments") {
                        if data.next_appointments.isEmpty {
                            Text("None").foregroundColor(.secondary)
                        } else {
                            ForEach(data.next_appointments.prefix(5)) { appt in
                                HStack {
                                    Text(appt.appointment_type ?? "Appointment").font(.headline)
                                    Spacer()
                                    Text(appt.scheduled_datetime ?? "").font(.caption)
                                        .foregroundColor(.secondary)
                                }
                                .padding(.vertical, 4)
                                Divider()
                            }
                        }
                    }
                }
            }
            .padding(24)
        }
        .task { await load() }
    }

    private func load() async {
        isLoading = true
        do {
            data = try await APIClient.shared.request("patient/dashboard")
        } catch { }
        isLoading = false
    }
}

struct KPICard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon).foregroundColor(color)
                Text(title).font(.caption).foregroundColor(.secondary)
            }
            Text(value).font(.system(size: 32, weight: .bold)).foregroundColor(color)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
        .shadow(color: .black.opacity(0.05), radius: 4, y: 2)
    }
}

struct SectionBox<Content: View>: View {
    let title: String
    @ViewBuilder let content: () -> Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title).font(.title3).bold()
            content()
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
        .shadow(color: .black.opacity(0.05), radius: 4, y: 2)
    }
}

struct StatusBadge: View {
    let status: String

    var body: some View {
        Text(status.uppercased())
            .font(.caption2).bold()
            .padding(.horizontal, 8).padding(.vertical, 3)
            .background(color.opacity(0.15))
            .foregroundColor(color)
            .cornerRadius(4)
    }

    private var color: Color {
        switch status.lowercased() {
        case "active", "paid", "approved", "completed": return .green
        case "pending", "submitted", "in_review": return .orange
        case "expired", "denied", "cancelled": return .red
        default: return .gray
        }
    }
}
