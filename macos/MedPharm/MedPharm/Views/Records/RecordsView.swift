/*
 * MedPharm ERP - macOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct RecordsView: View {
    @State private var records: [MedicalRecord] = []
    @State private var isLoading = true
    @State private var selectedId: Int?

    var selected: MedicalRecord? {
        records.first { $0.id == selectedId }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Medical Records").font(.largeTitle).bold()

            HSplitView {
                List(records, selection: $selectedId) { record in
                    VStack(alignment: .leading, spacing: 4) {
                        Text(record.title).font(.headline)
                        HStack {
                            Text(record.record_type.uppercased())
                                .font(.caption2).bold()
                                .foregroundColor(.teal)
                            Spacer()
                            Text(record.record_date ?? "")
                                .font(.caption2)
                                .foregroundColor(.secondary)
                        }
                    }
                    .tag(record.id)
                }
                .frame(minWidth: 340)

                Group {
                    if let record = selected {
                        ScrollView {
                            VStack(alignment: .leading, spacing: 12) {
                                Text(record.title).font(.title2).bold()
                                Text(record.record_type.uppercased())
                                    .font(.caption).foregroundColor(.teal)
                                if let date = record.record_date {
                                    Text("Date: \(date)").font(.caption)
                                        .foregroundColor(.secondary)
                                }
                                if let provider = record.provider_name {
                                    Text("Provider: \(provider)").font(.caption)
                                        .foregroundColor(.secondary)
                                }
                                Divider()
                                Text(record.content ?? "No details")
                                    .font(.body)
                            }
                            .padding()
                            .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    } else {
                        Text("Select a record to view details")
                            .foregroundColor(.secondary)
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                    }
                }
                .frame(minWidth: 300)
            }
        }
        .padding(24)
        .task { await load() }
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
