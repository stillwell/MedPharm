/*
 * MedPharm ERP - iOS Application
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
        Group {
            if isLoading {
                ProgressView()
            } else if let profile = profile {
                Form {
                    Section("Patient") {
                        LabeledContent("Name", value: profile.patient.full_name)
                        if let dob = profile.patient.dob {
                            LabeledContent("Date of Birth", value: dob)
                        }
                        if let age = profile.patient.age {
                            LabeledContent("Age", value: "\(age)")
                        }
                        if let gender = profile.patient.gender {
                            LabeledContent("Gender", value: gender)
                        }
                        if let blood = profile.patient.blood_type {
                            LabeledContent("Blood Type", value: blood)
                        }
                    }

                    Section("Contact") {
                        if isEditing {
                            TextField("Email", text: $email)
                                .keyboardType(.emailAddress)
                                .autocapitalization(.none)
                            TextField("Phone", text: $phone)
                                .keyboardType(.phonePad)
                            TextField("Address", text: $address)
                            TextField("City", text: $city)
                            TextField("State", text: $state)
                            TextField("Zip", text: $zip)
                                .keyboardType(.numberPad)
                        } else {
                            LabeledContent("Email", value: profile.patient.email ?? "—")
                            LabeledContent("Phone", value: profile.patient.phone ?? "—")
                            LabeledContent("Address", value: profile.patient.address ?? "—")
                            LabeledContent("City", value: profile.patient.city ?? "—")
                            LabeledContent("State", value: profile.patient.state ?? "—")
                            LabeledContent("Zip", value: profile.patient.zip_code ?? "—")
                        }
                    }

                    Section("Insurance (\(profile.insurance.count))") {
                        if profile.insurance.isEmpty {
                            Text("No insurance on file").foregroundColor(.secondary)
                        } else {
                            ForEach(profile.insurance.indices, id: \.self) { idx in
                                let ins = profile.insurance[idx]
                                VStack(alignment: .leading, spacing: 2) {
                                    Text((ins["provider_name"]?.value as? String) ?? "—")
                                        .font(.subheadline).bold()
                                    if let policy = ins["policy_number"]?.value as? String {
                                        Text("Policy: \(policy)").font(.caption)
                                            .foregroundColor(.secondary)
                                    }
                                }
                            }
                        }
                    }

                    Section("Allergies (\(profile.allergies.count))") {
                        if profile.allergies.isEmpty {
                            Text("No known allergies").foregroundColor(.secondary)
                        } else {
                            ForEach(profile.allergies.indices, id: \.self) { idx in
                                let a = profile.allergies[idx]
                                HStack {
                                    Image(systemName: "exclamationmark.triangle.fill")
                                        .foregroundColor(.orange)
                                    VStack(alignment: .leading) {
                                        Text((a["allergen"]?.value as? String) ?? "—")
                                            .font(.subheadline)
                                        if let sev = a["severity"]?.value as? String {
                                            Text(sev).font(.caption2).foregroundColor(.secondary)
                                        }
                                    }
                                }
                            }
                        }
                    }

                    if let msg = message {
                        Text(msg).font(.caption).foregroundColor(.green)
                    }
                }
            }
        }
        .navigationTitle("Profile")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            if profile != nil {
                ToolbarItem(placement: .topBarTrailing) {
                    Button(isEditing ? "Save" : "Edit") {
                        if isEditing {
                            Task { await save() }
                        } else {
                            startEditing()
                        }
                    }
                }
            }
        }
        .task { await load() }
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

struct NotificationsView: View {
    @State private var notifications: [AppNotification] = []
    @State private var isLoading = true

    var body: some View {
        Group {
            if isLoading {
                ProgressView()
            } else if notifications.isEmpty {
                Text("No notifications").foregroundColor(.secondary)
            } else {
                List(notifications) { n in
                    HStack {
                        Image(systemName: iconFor(n.type))
                            .foregroundColor(colorFor(n.type))
                        VStack(alignment: .leading) {
                            if let title = n.title {
                                Text(title).font(.subheadline).bold()
                            }
                            Text(n.message).font(.caption)
                        }
                    }
                }
                .listStyle(.plain)
            }
        }
        .navigationTitle("Notifications")
        .navigationBarTitleDisplayMode(.inline)
        .task { await load() }
    }

    private func load() async {
        isLoading = true
        do {
            let resp: NotificationsResponse = try await APIClient.shared.request(
                "patient/notifications")
            notifications = resp.notifications
        } catch { }
        isLoading = false
    }

    private func iconFor(_ type: String) -> String {
        switch type {
        case "appointment": return "calendar"
        case "prescription": return "pill"
        case "billing": return "dollarsign.circle"
        default: return "bell"
        }
    }

    private func colorFor(_ type: String) -> Color {
        switch type {
        case "appointment": return .blue
        case "prescription": return .teal
        case "billing": return .orange
        default: return .gray
        }
    }
}

struct SymptomsView: View {
    @State private var symptoms: [SymptomRef] = []
    @State private var searchText = ""
    @State private var isLoading = false

    var body: some View {
        List(symptoms) { s in
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(s.name).font(.headline)
                    Spacer()
                    if s.is_emergency == true {
                        Text("EMERGENCY").font(.caption2).bold()
                            .padding(4)
                            .background(Color.red.opacity(0.2))
                            .foregroundColor(.red)
                            .cornerRadius(4)
                    }
                }
                if let system = s.body_system {
                    Text(system).font(.caption2).foregroundColor(.teal)
                }
                if let desc = s.description {
                    Text(desc).font(.caption).foregroundColor(.secondary).lineLimit(2)
                }
            }
            .padding(.vertical, 2)
        }
        .searchable(text: $searchText, prompt: "Search symptoms")
        .onChange(of: searchText) { _ in Task { await load() } }
        .navigationTitle("Symptoms")
        .navigationBarTitleDisplayMode(.inline)
        .task { await load() }
    }

    private func load() async {
        do {
            let endpoint = searchText.isEmpty
                ? "reference/symptoms"
                : "reference/symptoms?q=\(searchText.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "")"
            let resp: SymptomsResponse = try await APIClient.shared.request(endpoint)
            symptoms = resp.symptoms
        } catch { }
    }
}
