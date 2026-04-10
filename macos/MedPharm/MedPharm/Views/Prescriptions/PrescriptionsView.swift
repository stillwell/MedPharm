/*
 * MedPharm ERP - macOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct PrescriptionsView: View {
    @State private var prescriptions: [Prescription] = []
    @State private var filter: String? = nil
    @State private var isLoading = true

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Prescriptions").font(.largeTitle).bold()
                Spacer()
                Picker("", selection: $filter) {
                    Text("All").tag(nil as String?)
                    Text("Active").tag("active" as String?)
                    Text("Expired").tag("expired" as String?)
                }
                .pickerStyle(.segmented)
                .frame(width: 280)
                .onChange(of: filter) { _ in Task { await load() } }
            }

            Table(prescriptions) {
                TableColumn("Rx Number", value: \.rx_number)
                TableColumn("Prescriber") { Text($0.prescriber_name ?? "") }
                TableColumn("Date") { Text($0.prescribed_date ?? "") }
                TableColumn("Expires") { Text($0.expiry_date ?? "") }
                TableColumn("Status", value: \.status)
            }
            .overlay {
                if isLoading {
                    ProgressView()
                } else if prescriptions.isEmpty {
                    Text("No prescriptions").foregroundColor(.secondary)
                }
            }
        }
        .padding(24)
        .task { await load() }
    }

    private func load() async {
        isLoading = true
        do {
            let endpoint = "patient/prescriptions\(filter.map { "?status=\($0)" } ?? "")"
            let resp: PrescriptionListResponse = try await APIClient.shared.request(endpoint)
            prescriptions = resp.prescriptions
        } catch { }
        isLoading = false
    }
}
