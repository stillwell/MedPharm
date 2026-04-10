/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct PrescriptionsView: View {
    @State private var prescriptions: [Prescription] = []
    @State private var isLoading = true
    @State private var filter: String? = nil

    var body: some View {
        NavigationStack {
            VStack {
                Picker("Filter", selection: $filter) {
                    Text("All").tag(nil as String?)
                    Text("Active").tag("active" as String?)
                    Text("Expired").tag("expired" as String?)
                }.pickerStyle(.segmented).padding(.horizontal)
                    .onChange(of: filter) { _ in Task { await load() } }

                if isLoading {
                    ProgressView().padding(.top, 50)
                } else if prescriptions.isEmpty {
                    Text("No prescriptions").foregroundColor(.secondary).padding(.top, 50)
                } else {
                    List(prescriptions) { rx in
                        VStack(alignment: .leading, spacing: 6) {
                            HStack {
                                Text(rx.rx_number).font(.headline).foregroundColor(.teal)
                                Spacer()
                                StatusBadge(status: rx.status)
                            }
                            Text(rx.prescriber_name ?? "").font(.caption).foregroundColor(.secondary)
                            Text(rx.prescribed_date ?? "").font(.caption2).foregroundColor(.secondary)
                            if let items = rx.items {
                                ForEach(items) { item in
                                    HStack {
                                        Text("\(item.medication_name ?? "Med") \(item.dosage)")
                                        Spacer()
                                        Text(item.frequency).font(.caption)
                                    }.font(.caption2).padding(.top, 2)
                                }
                            }
                            if rx.status == "active", let items = rx.items,
                               items.contains(where: { $0.refills_remaining > 0 }) {
                                Button("Request Refill") { Task { await refill(rx.id) } }
                                    .font(.caption).foregroundColor(.teal)
                            }
                        }
                    }.listStyle(.plain)
                }
            }
            .navigationTitle("Prescriptions")
            .refreshable { await load() }
            .task { await load() }
        }
    }

    private func load() async {
        isLoading = true
        do {
            let resp: PrescriptionListResponse = try await APIClient.shared.request(
                "patient/prescriptions\(filter.map { "?status=\($0)" } ?? "")")
            prescriptions = resp.prescriptions
        } catch { }
        isLoading = false
    }

    private func refill(_ id: Int) async {
        let _: MessageResponse? = try? await APIClient.shared.request(
            "patient/prescriptions/\(id)/refill", method: "POST")
        await load()
    }
}
