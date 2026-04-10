/*
 * MedPharm ERP - macOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct AppointmentsView: View {
    @State private var appointments: [Appointment] = []
    @State private var isLoading = true

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Appointments").font(.largeTitle).bold()

            if isLoading {
                ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                Table(appointments) {
                    TableColumn("Date/Time") { Text($0.scheduled_datetime ?? "") }
                    TableColumn("Type") { Text($0.appointment_type ?? "") }
                    TableColumn("Provider") { Text($0.provider_name ?? "") }
                    TableColumn("Duration") {
                        Text($0.duration_minutes.map { "\($0) min" } ?? "")
                    }
                    TableColumn("Status", value: \.status)
                    TableColumn("Reason") { Text($0.reason ?? "") }
                }
            }
        }
        .padding(24)
        .task { await load() }
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
