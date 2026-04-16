/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct AppointmentsView: View {
    @State private var appointments: [Appointment] = []
    @State private var isLoading = true

    var body: some View {
        NavigationStack {
            Group {
                if isLoading {
                    ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if appointments.isEmpty {
                    VStack(spacing: 12) {
                        Image(systemName: "calendar.badge.exclamationmark")
                            .font(.system(size: 60))
                            .foregroundColor(.secondary)
                        Text("No appointments scheduled")
                            .foregroundColor(.secondary)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List(appointments) { appt in
                        AppointmentCard(appointment: appt)
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("Appointments")
            .refreshable { await load() }
            .task { await load() }
        }
    }

    private func load() async {
        isLoading = true
        do {
            let resp: AppointmentsResponse = try await APIClient.shared.request(
                "patient/appointments")
            appointments = resp.appointments
        } catch { }
        isLoading = false
    }
}

struct AppointmentCard: View {
    let appointment: Appointment

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "calendar")
                    .foregroundColor(.teal)
                Text(appointment.appointment_type ?? "Appointment")
                    .font(.headline)
                Spacer()
                StatusBadge(status: appointment.status)
            }
            if let provider = appointment.provider_name {
                HStack {
                    Image(systemName: "person.fill")
                        .foregroundColor(.secondary)
                    Text(provider).font(.subheadline)
                }
            }
            if let datetime = appointment.scheduled_datetime {
                HStack {
                    Image(systemName: "clock")
                        .foregroundColor(.secondary)
                    Text(datetime).font(.caption)
                }
            }
            if let duration = appointment.duration_minutes {
                Text("\(duration) minutes").font(.caption2).foregroundColor(.secondary)
            }
            if let reason = appointment.reason, !reason.isEmpty {
                Text(reason).font(.caption).padding(.top, 4)
            }
        }
        .padding(.vertical, 6)
    }
}
