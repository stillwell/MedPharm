/*
 * MedPharm ERP - macOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct ProfileView: View {
    @State private var profile: PatientProfile?
    @State private var isLoading = true
    @State private var isEditing = false
    @State private var email = ""
    @State private var phone = ""
    @State private var address = ""
    @State private var city = ""
    @State private var state = ""
    @State private var zip = ""
    @State private var message: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                HStack {
                    Text("Profile").font(.largeTitle).bold()
                    Spacer()
                    if profile != nil {
                        Button(isEditing ? "Save" : "Edit") {
                            if isEditing {
                                Task { await save() }
                            } else {
                                startEditing()
                            }
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.teal)
                    }
                }

                if isLoading {
                    ProgressView()
                } else if let profile = profile {
                    SectionBox(title: "Patient Information") {
                        Grid(alignment: .leading, horizontalSpacing: 16, verticalSpacing: 8) {
                            infoRow("Name", profile.patient.full_name)
                            infoRow("Date of Birth", profile.patient.dob ?? "—")
                            infoRow("Age", profile.patient.age.map(String.init) ?? "—")
                            infoRow("Gender", profile.patient.gender ?? "—")
                            infoRow("Blood Type", profile.patient.blood_type ?? "—")
                        }
                    }

                    SectionBox(title: "Contact") {
                        Grid(alignment: .leading, horizontalSpacing: 16, verticalSpacing: 10) {
                            if isEditing {
                                editRow("Email", $email)
                                editRow("Phone", $phone)
                                editRow("Address", $address)
                                editRow("City", $city)
                                editRow("State", $state)
                                editRow("Zip", $zip)
                            } else {
                                infoRow("Email", profile.patient.email ?? "—")
                                infoRow("Phone", profile.patient.phone ?? "—")
                                infoRow("Address", profile.patient.address ?? "—")
                                infoRow("City", profile.patient.city ?? "—")
                                infoRow("State", profile.patient.state ?? "—")
                                infoRow("Zip", profile.patient.zip_code ?? "—")
                            }
                        }
                    }

                    SectionBox(title: "Insurance (\(profile.insurance.count))") {
                        if profile.insurance.isEmpty {
                            Text("No insurance on file").foregroundColor(.secondary)
                        } else {
                            ForEach(profile.insurance.indices, id: \.self) { idx in
                                let ins = profile.insurance[idx]
                                VStack(alignment: .leading) {
                                    Text((ins["provider_name"]?.value as? String) ?? "—")
                                        .font(.headline)
                                    if let policy = ins["policy_number"]?.value as? String {
                                        Text("Policy: \(policy)").font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                }
                                .padding(.vertical, 4)
                                if idx < profile.insurance.count - 1 { Divider() }
                            }
                        }
                    }

                    SectionBox(title: "Allergies (\(profile.allergies.count))") {
                        if profile.allergies.isEmpty {
                            Text("No known allergies").foregroundColor(.secondary)
                        } else {
                            ForEach(profile.allergies.indices, id: \.self) { idx in
                                let a = profile.allergies[idx]
                                HStack {
                                    Image(systemName: "exclamationmark.triangle.fill")
                                        .foregroundColor(.orange)
                                    Text((a["allergen"]?.value as? String) ?? "—")
                                    Spacer()
                                    if let sev = a["severity"]?.value as? String {
                                        Text(sev).font(.caption).foregroundColor(.secondary)
                                    }
                                }
                            }
                        }
                    }

                    if let msg = message {
                        Text(msg).foregroundColor(.green).font(.caption)
                    }
                }
            }
            .padding(24)
        }
        .task { await load() }
    }

    @ViewBuilder
    private func infoRow(_ label: String, _ value: String) -> some View {
        GridRow {
            Text(label).foregroundColor(.secondary).gridColumnAlignment(.trailing)
            Text(value)
        }
    }

    @ViewBuilder
    private func editRow(_ label: String, _ binding: Binding<String>) -> some View {
        GridRow {
            Text(label).foregroundColor(.secondary).gridColumnAlignment(.trailing)
            TextField("", text: binding).textFieldStyle(.roundedBorder)
        }
    }

    private func load() async {
        isLoading = true
        do {
            profile = try await APIClient.shared.request("patient/profile")
        } catch { }
        isLoading = false
    }

    private func startEditing() {
        guard let p = profile?.patient else { return }
        email = p.email ?? ""
        phone = p.phone ?? ""
        address = p.address ?? ""
        city = p.city ?? ""
        state = p.state ?? ""
        zip = p.zip_code ?? ""
        isEditing = true
    }

    private func save() async {
        let req = ProfileUpdateRequest(
            email: email, phone: phone, address: address,
            city: city, state: state, zip_code: zip)
        do {
            let _: MessageResponse = try await APIClient.shared.request(
                "patient/profile", method: "PUT", body: req)
            message = "Profile updated"
            isEditing = false
            await load()
        } catch {
            message = error.localizedDescription
        }
    }
}
