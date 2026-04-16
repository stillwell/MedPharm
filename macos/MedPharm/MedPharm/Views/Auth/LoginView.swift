/*
 * MedPharm ERP - macOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct LoginView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var username = ""
    @State private var password = ""
    @State private var loginType = "Patient"

    var body: some View {
        VStack(spacing: 24) {
            VStack(spacing: 8) {
                Image(systemName: "cross.case.fill")
                    .font(.system(size: 60))
                    .foregroundColor(.teal)
                Text("MedPharm ERP")
                    .font(.largeTitle).bold()
                    .foregroundColor(.teal)
                Text("Medical & Pharmaceutical Management")
                    .font(.caption).foregroundColor(.secondary)
            }
            .padding(.top, 20)

            VStack(alignment: .leading, spacing: 16) {
                Picker("Login As", selection: $loginType) {
                    Text("Patient").tag("Patient")
                    Text("Staff").tag("Staff")
                }.pickerStyle(.segmented)

                VStack(alignment: .leading, spacing: 4) {
                    Text("Username").font(.caption).foregroundColor(.secondary)
                    TextField("", text: $username)
                        .textFieldStyle(.roundedBorder)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text("Password").font(.caption).foregroundColor(.secondary)
                    SecureField("", text: $password)
                        .textFieldStyle(.roundedBorder)
                }

                if let error = authManager.errorMessage {
                    Text(error).foregroundColor(.red).font(.caption)
                }

                Button(action: login) {
                    if authManager.isLoading {
                        ProgressView().scaleEffect(0.7)
                    } else {
                        Text("Log In").frame(maxWidth: .infinity)
                    }
                }
                .buttonStyle(.borderedProminent)
                .tint(.teal)
                .controlSize(.large)
                .disabled(authManager.isLoading || username.isEmpty || password.isEmpty)
            }
            .padding(.horizontal, 32)

            Spacer()

            Text("Copyright © 2026 Enlightec Ltd.")
                .font(.caption2).foregroundColor(.secondary)
        }
        .padding()
    }

    private func login() {
        Task {
            if loginType == "Patient" {
                await authManager.patientLogin(username: username, password: password)
            } else {
                await authManager.staffLogin(username: username, password: password)
            }
        }
    }
}
