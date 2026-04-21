/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct DashboardView: View {
    @State private var dashboard: DashboardData?
    @State private var isLoading = true
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            ZStack {
                MPBackground()

                ScrollView {
                    if isLoading {
                        ProgressView().tint(MPColor.primary).padding(.top, 80)
                    } else if let data = dashboard {
                        VStack(spacing: 16) {
                            MPHeroBanner(
                                title: "Your health at a glance",
                                subtitle: "REAL-TIME · HIPAA-SECURE · TLS ENCRYPTED",
                                systemImage: "heart.text.square.fill"
                            )
                            .padding(.horizontal, 16)

                            // KPI Cards
                            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                                MPKpiCard(
                                    label: "Active Rx",
                                    value: "\(data.active_prescriptions)",
                                    systemImage: "pills.fill",
                                    tint: MPGradient.primary
                                )
                                MPKpiCard(
                                    label: "Appointments",
                                    value: "\(data.upcoming_appointments)",
                                    systemImage: "calendar.badge.clock",
                                    tint: LinearGradient(colors: [MPColor.info, MPColor.primary],
                                                         startPoint: .topLeading, endPoint: .bottomTrailing)
                                )
                                MPKpiCard(
                                    label: "Balance",
                                    value: String(format: "$%.2f", data.outstanding_balance),
                                    systemImage: "creditcard.fill",
                                    tint: MPGradient.danger
                                )
                                MPKpiCard(
                                    label: "Status",
                                    value: "Good",
                                    systemImage: "waveform.path.ecg",
                                    tint: MPGradient.success
                                )
                            }
                            .padding(.horizontal, 16)

                            // Recent Prescriptions
                            if !data.recent_prescriptions.isEmpty {
                                SectionHeader(title: "Active Prescriptions", systemImage: "pills.fill")
                                VStack(spacing: 10) {
                                    ForEach(data.recent_prescriptions) { rx in
                                        PrescriptionRow(prescription: rx)
                                    }
                                }
                                .padding(.horizontal, 16)
                            }

                            // Upcoming Appointments
                            if !data.next_appointments.isEmpty {
                                SectionHeader(title: "Upcoming Appointments", systemImage: "calendar.badge.clock")
                                VStack(spacing: 10) {
                                    ForEach(data.next_appointments) { appt in
                                        AppointmentRow(appointment: appt)
                                    }
                                }
                                .padding(.horizontal, 16)
                            }

                            Spacer().frame(height: 24)
                        }
                        .padding(.top, 12)
                    } else if let error = errorMessage {
                        Text(error).foregroundColor(MPColor.danger).padding()
                    }
                }
            }
            .navigationTitle("Dashboard")
            .navigationBarTitleDisplayMode(.inline)
            .toolbarBackground(MPColor.bg, for: .navigationBar)
            .toolbarColorScheme(.dark, for: .navigationBar)
            .refreshable { await loadDashboard() }
            .task { await loadDashboard() }
            .preferredColorScheme(.dark)
        }
    }

    private func loadDashboard() async {
        isLoading = true
        do {
            dashboard = try await APIClient.shared.request("patient/dashboard")
        } catch { errorMessage = error.localizedDescription }
        isLoading = false
    }
}

struct SectionHeader: View {
    let title: String
    var systemImage: String = "circle.fill"
    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: systemImage)
                .font(.system(size: 16, weight: .semibold))
                .foregroundStyle(MPGradient.primary)
            Text(title)
                .font(.system(size: 18, weight: .bold))
                .foregroundColor(MPColor.text)
            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.top, 8)
    }
}

struct PrescriptionRow: View {
    let prescription: Prescription
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(prescription.rx_number)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(MPColor.primary)
                Spacer()
                StatusBadge(status: prescription.status)
            }
            if let prescriber = prescription.prescriber_name {
                Text(prescriber).font(.caption).foregroundColor(MPColor.textMuted)
            }
            if let items = prescription.items {
                ForEach(items) { item in
                    Text("\(item.medication_name ?? "Medication") · \(item.dosage) · \(item.frequency)")
                        .font(.caption2)
                        .foregroundColor(MPColor.textMuted)
                }
            }
        }
        .mpCard(padding: 16)
    }
}

struct AppointmentRow: View {
    let appointment: Appointment
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 3) {
                Text(appointment.scheduled_datetime ?? "TBD")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(MPColor.text)
                Text(appointment.provider_name ?? "")
                    .font(.caption).foregroundColor(MPColor.textMuted)
                if let reason = appointment.reason {
                    Text(reason).font(.caption2).foregroundColor(MPColor.textMuted)
                }
            }
            Spacer()
            StatusBadge(status: appointment.status)
        }
        .mpCard(padding: 16)
    }
}

struct StatusBadge: View {
    let status: String
    var color: Color {
        switch status {
        case "active", "completed", "approved": return MPColor.success
        case "pending", "scheduled", "confirmed", "submitted": return MPColor.warning
        case "expired", "cancelled", "denied": return MPColor.textDim
        case "overdue": return MPColor.danger
        default: return MPColor.info
        }
    }
    var body: some View {
        Text(status.uppercased())
            .font(.system(size: 10, weight: .bold))
            .kerning(1.0)
            .padding(.horizontal, 10)
            .padding(.vertical, 4)
            .background(
                Capsule().fill(color.opacity(0.18))
                    .overlay(Capsule().strokeBorder(color.opacity(0.35), lineWidth: 1))
            )
            .foregroundColor(color)
    }
}
