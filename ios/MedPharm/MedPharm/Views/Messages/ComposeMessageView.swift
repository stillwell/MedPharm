/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct ComposeMessageView: View {
    @Environment(\.dismiss) private var dismiss

    @State private var providers: [ProviderSummary] = []
    @State private var selectedProviderId: Int? = nil
    @State private var subject: String = ""
    @State private var body: String = ""
    @State private var isSending = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            Form {
                Section("To") {
                    Picker("Provider", selection: $selectedProviderId) {
                        Text("Any available clinician").tag(Int?.none)
                        ForEach(providers) { p in
                            let label = p.display_title ?? p.full_name ?? "Unknown"
                            let suffix = (p.specialization?.isEmpty == false) ? " — \(p.specialization!)" : ""
                            Text("\(label)\(suffix)").tag(Int?(p.id))
                        }
                    }
                }
                Section("Subject") {
                    TextField("Subject", text: $subject)
                }
                Section("Message") {
                    TextEditor(text: $body)
                        .frame(minHeight: 180)
                }
                Section {
                    Text("For medical emergencies, call 911. Secure messages are typically answered within 1–2 business days.")
                        .font(.footnote)
                        .foregroundColor(MPColor.textMuted)
                }
            }
            .scrollContentBackground(.hidden)
            .background(MPColor.bg)
            .navigationTitle("New Message")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button(isSending ? "Sending…" : "Send") {
                        Task { await send() }
                    }
                    .disabled(!canSend || isSending)
                }
            }
            .alert("Error", isPresented: Binding(
                get: { errorMessage != nil },
                set: { if !$0 { errorMessage = nil } }
            )) {
                Button("OK") { errorMessage = nil }
            } message: {
                Text(errorMessage ?? "")
            }
            .task { await loadProviders() }
        }
    }

    private var canSend: Bool {
        !subject.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty &&
        !body.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    private func loadProviders() async {
        do {
            let response: ProvidersResponse = try await APIClient.shared
                .request("patient/messages/providers")
            providers = response.providers
        } catch {
            // Non-fatal — can still send without selecting a provider.
        }
    }

    private func send() async {
        isSending = true
        defer { isSending = false }
        let request = NewThreadRequest(
            subject: subject.trimmingCharacters(in: .whitespacesAndNewlines),
            body: body.trimmingCharacters(in: .whitespacesAndNewlines),
            provider_id: selectedProviderId)
        do {
            let _: NewThreadResponse = try await APIClient.shared.request(
                "patient/messages", method: "POST", body: request)
            dismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
