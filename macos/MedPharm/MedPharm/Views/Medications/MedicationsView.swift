/*
 * MedPharm ERP - macOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct MedicationsView: View {
    @State private var medications: [Medication] = []
    @State private var searchText = ""
    @State private var isLoading = true

    var filtered: [Medication] {
        searchText.isEmpty ? medications : medications.filter {
            $0.brand_name.localizedCaseInsensitiveContains(searchText) ||
            $0.generic_name.localizedCaseInsensitiveContains(searchText)
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Medications").font(.largeTitle).bold()
                Spacer()
                TextField("Search...", text: $searchText)
                    .textFieldStyle(.roundedBorder)
                    .frame(width: 240)
            }

            if isLoading {
                ProgressView().frame(maxWidth: .infinity)
            } else {
                Table(filtered) {
                    TableColumn("Brand Name") { med in
                        // Brand name acts as a hyperlink to MedlinePlus.
                        // Visible affordance: blue text + Safari icon.
                        if let url = DrugInfoURL.url(for: med) {
                            Link(destination: url) {
                                HStack(spacing: 4) {
                                    Text(med.brand_name).foregroundColor(.accentColor)
                                    Image(systemName: "safari").foregroundColor(.secondary)
                                }
                            }
                            .help("Look up \(med.brand_name) on MedlinePlus")
                        } else {
                            Text(med.brand_name)
                        }
                    }
                    TableColumn("Generic Name", value: \.generic_name)
                    TableColumn("Class") { Text($0.drug_class ?? "") }
                    TableColumn("Strength") { Text($0.strength ?? "") }
                    TableColumn("Form") { Text($0.form ?? "") }
                    TableColumn("Indications") {
                        Text($0.indications ?? "").lineLimit(1)
                    }
                    TableColumn("Drug Info") { med in
                        if let url = DrugInfoURL.url(for: med) {
                            Link("MedlinePlus ↗", destination: url)
                                .help("Open MedlinePlus drug information in your default browser")
                        }
                    }
                    .width(110)
                }
            }
        }
        .padding(24)
        .task { await load() }
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
