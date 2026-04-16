/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct RegisterView: View {
    @Environment(\.dismiss) var dismiss
    @State private var firstName = ""
    @State private var lastName = ""
    @State private var dob = ""
    @State private var ssnLast4 = ""
    @State private var username = ""
    @State private var email = ""
    @State private var password = ""
    @State private var confirmPassword = ""
    @State private var isLoading = false
    @State private var message: String?
    @State private var isError = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Identity Verification") {
                    TextField("First Name", text: $firstName)
                    TextField("Last Name", text: $lastName)
                    TextField("Date of Birth (YYYY-MM-DD)", text: $dob)
                    TextField("Last 4 of SSN", text: $ssnLast4)
                        .keyboardType(.numberPad)
                }
                Section("Account Credentials") {
                    TextField("Username", text: $username).autocapitalization(.none)
                    TextField("Email", text: $email).keyboardType(.emailAddress).autocapitalization(.none)
                    SecureField("Password", text: $password)
                    SecureField("Confirm Password", text: $confirmPassword)
                }
                if let message = message {
                    Text(message).foregroundColor(isError ? .red : .green)
                }
                Section {
                    Button(action: register) {
                        if isLoading { ProgressView() } else { Text("Create Account").bold() }
                    }.disabled(isLoading)
                }
            }
            .navigationTitle("Register")
            .toolbar { ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } } }
        }
    }

    private func register() {
        guard password == confirmPassword else { message = "Passwords don't match"; isError = true; return }
        guard password.count >= 6 else { message = "Password must be 6+ characters"; isError = true; return }
        isLoading = true
        Task {
            do {
                let _: MessageResponse = try await APIClient.shared.request(
                    "auth/register", method: "POST",
                    body: RegisterRequest(first_name: firstName, last_name: lastName,
                                          dob: dob, ssn_last4: ssnLast4, username: username,
                                          email: email, password: password))
                message = "Account created! You can now log in."; isError = false
                try? await Task.sleep(nanoseconds: 1_500_000_000); dismiss()
            } catch { message = error.localizedDescription; isError = true }
            isLoading = false
        }
    }
}
