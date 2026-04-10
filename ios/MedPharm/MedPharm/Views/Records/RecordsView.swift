/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct RecordsView: View {
    @State private var records: [MedicalRecord] = []
    @State private var isLoading = true

    var body: some View {
        Group {
            if isLoading {
                ProgressView()
            } else if records.isEmpty {
                Text("No records").foregroundColor(.secondary)
            } else {
                List(records) { record in
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text(record.record_type.uppercased())
                                .font(.caption2).bold()
                                .padding(.horizontal, 8).padding(.vertical, 3)
                                .background(Color.teal.opacity(0.15))
                                .foregroundColor(.teal)
                                .cornerRadius(4)
                            Spacer()
                            Text(record.record_date ?? "").font(.caption2)
                                .foregroundColor(.secondary)
                        }
                        Text(record.title).font(.headline)
                        if let provider = record.provider_name {
                            Text(provider).font(.caption).foregroundColor(.secondary)
                        }
                        if let content = record.content {
                            Text(content).font(.caption).lineLimit(3)
                        }
                    }
                    .padding(.vertical, 4)
                }
                .listStyle(.plain)
            }
        }
        .navigationTitle("Medical Records")
        .navigationBarTitleDisplayMode(.inline)
        .task { await load() }
        .refreshable { await load() }
    }

    private func load() async {
        isLoading = true
        do {
            let resp: RecordsResponse = try await APIClient.shared.request("patient/records")
            records = resp.records
        } catch { }
        isLoading = false
    }
}
