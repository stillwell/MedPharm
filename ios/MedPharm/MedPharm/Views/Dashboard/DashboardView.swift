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
            ScrollView {
                if isLoading {
                    ProgressView("Loading...").padding(.top, 50)
                } else if let data = dashboard {
                    VStack(spacing: 16) {
                        // KPI Cards
                        HStack(spacing: 12) {
                            KPICard(title: "Active Rx", value: "\(data.active_prescriptions)", color: .teal)
                            KPICard(title: "Appointments", value: "\(data.upcoming_appointments)", color: .blue)
                            KPICard(title: "Balance", value: String(format: "$%.2f", data.outstanding_balance), color: .red)
                        }.padding(.horizontal)

                        // Recent Prescriptions
                        if !data.recent_prescriptions.isEmpty {
                            SectionHeader(title: "Recent Prescriptions")
                            ForEach(data.recent_prescriptions) { rx in
                                PrescriptionRow(prescription: rx).padding(.horizontal)
                            }
                        }

                        // Upcoming Appointments
                        if !data.next_appointments.isEmpty {
                            SectionHeader(title: "Upcoming Appointments")
                            ForEach(data.next_appointments) { appt in
                                AppointmentRow(appointment: appt).padding(.horizontal)
                            }
                        }
                    }.padding(.top)
                } else if let error = errorMessage {
                    Text(error).foregroundColor(.red).padding()
                }
            }
            .navigationTitle("Dashboard")
            .refreshable { await loadDashboard() }
            .task { await loadDashboard() }
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

struct KPICard: View {
    let title: String; let value: String; let color: Color
    var body: some View {
        VStack(spacing: 4) {
            Text(value).font(.title2).bold().foregroundColor(color)
            Text(title).font(.caption).foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.05), radius: 4)
    }
}

struct SectionHeader: View {
    let title: String
    var body: some View {
        Text(title).font(.headline).frame(maxWidth: .infinity, alignment: .leading).padding(.horizontal)
    }
}

struct PrescriptionRow: View {
    let prescription: Prescription
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(prescription.rx_number).font(.headline).foregroundColor(.teal)
                Spacer()
                StatusBadge(status: prescription.status)
            }
            if let prescriber = prescription.prescriber_name { Text(prescriber).font(.caption).foregroundColor(.secondary) }
            if let items = prescription.items {
                ForEach(items) { item in
                    Text("\(item.medication_name ?? "Medication") - \(item.dosage), \(item.frequency)")
                        .font(.caption2)
                }
            }
        }.padding().background(Color(.systemBackground)).cornerRadius(10).shadow(color: .black.opacity(0.03), radius: 2)
    }
}

struct AppointmentRow: View {
    let appointment: Appointment
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(appointment.scheduled_datetime ?? "TBD").font(.subheadline).bold()
                Text(appointment.provider_name ?? "").font(.caption).foregroundColor(.secondary)
                if let reason = appointment.reason { Text(reason).font(.caption2).foregroundColor(.secondary) }
            }
            Spacer()
            StatusBadge(status: appointment.status)
        }.padding().background(Color(.systemBackground)).cornerRadius(10).shadow(color: .black.opacity(0.03), radius: 2)
    }
}

struct StatusBadge: View {
    let status: String
    var color: Color {
        switch status {
        case "active", "completed", "approved": return .green
        case "pending", "scheduled", "confirmed", "submitted": return .orange
        case "expired", "cancelled", "denied": return .gray
        case "overdue": return .red
        default: return .blue
        }
    }
    var body: some View {
        Text(status.capitalized).font(.caption2).bold().padding(.horizontal, 8).padding(.vertical, 3)
            .background(color.opacity(0.15)).foregroundColor(color).cornerRadius(6)
    }
}
