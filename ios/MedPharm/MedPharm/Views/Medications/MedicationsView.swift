/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct MedicationsView: View {
    @State private var medications: [Medication] = []
    @State private var isLoading = true
    @State private var searchText = ""
    @Environment(\.openURL) private var openURL

    var filtered: [Medication] {
        searchText.isEmpty ? medications : medications.filter {
            $0.brand_name.localizedCaseInsensitiveContains(searchText) ||
            $0.generic_name.localizedCaseInsensitiveContains(searchText)
        }
    }

    var body: some View {
        Group {
            if isLoading {
                ProgressView()
            } else if medications.isEmpty {
                Text("No current medications").foregroundColor(.secondary)
            } else {
                List(filtered) { med in
                    Button(action: { openDrugInfo(for: med) }) {
                        VStack(alignment: .leading, spacing: 6) {
                            HStack {
                                Image(systemName: "pill.fill").foregroundColor(.teal)
                                Text(med.brand_name).font(.headline)
                                Spacer()
                                if let strength = med.strength {
                                    Text(strength).font(.caption).foregroundColor(.secondary)
                                }
                                Image(systemName: "safari")
                                    .foregroundColor(.secondary)
                                    .accessibilityLabel("Look up drug information")
                            }
                            Text(med.generic_name).font(.caption).foregroundColor(.secondary)
                            if let dosage = med.dosage, let freq = med.frequency {
                                Text("\(dosage) - \(freq)").font(.caption)
                            }
                            if let drugClass = med.drug_class {
                                Text(drugClass).font(.caption2)
                                    .padding(.horizontal, 6).padding(.vertical, 2)
                                    .background(Color.blue.opacity(0.1))
                                    .foregroundColor(.blue)
                                    .cornerRadius(4)
                            }
                            if let indications = med.indications {
                                Text("Used for: \(indications)").font(.caption2)
                                    .foregroundColor(.secondary).lineLimit(2)
                            }
                        }
                        .padding(.vertical, 4)
                        .contentShape(Rectangle())
                    }
                    .buttonStyle(.plain)
                    .contextMenu {
                        ForEach(DrugInfoSource.allCases, id: \.self) { source in
                            if let url = DrugInfoURL.url(for: med, source: source) {
                                Button {
                                    openURL(url)
                                } label: {
                                    Label("Open in \(source.displayName)", systemImage: "safari")
                                }
                            }
                        }
                    }
                }
                .listStyle(.plain)
                .searchable(text: $searchText, prompt: "Search medications")
            }
        }
        .navigationTitle("Medications")
        .navigationBarTitleDisplayMode(.inline)
        .task { await load() }
        .refreshable { await load() }
    }

    private func openDrugInfo(for med: Medication) {
        guard let url = DrugInfoURL.url(for: med) else { return }
        openURL(url)
    }

    private func load() async {
        isLoading = true
        do {
            let resp: MedicationsResponse = try await APIClient.shared.request(
                "patient/medications")
            medications = resp.medications
        } catch { }
        isLoading = false
    }
}
