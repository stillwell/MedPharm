/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct LoginView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var username = ""
    @State private var password = ""
    @State private var isStaff = false
    @State private var showRegister = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    Spacer().frame(height: 40)

                    Text("MedPharm ERP")
                        .font(.largeTitle).bold()
                        .foregroundColor(.teal)
                    Text("Medical & Pharmaceutical Management")
                        .font(.subheadline)
                        .foregroundColor(.secondary)

                    Picker("Login Type", selection: $isStaff) {
                        Text("Patient").tag(false)
                        Text("Staff").tag(true)
                    }.pickerStyle(.segmented).padding(.horizontal)

                    VStack(spacing: 16) {
                        TextField("Username", text: $username)
                            .textFieldStyle(.roundedBorder)
                            .autocapitalization(.none)
                            .disableAutocorrection(true)

                        SecureField("Password", text: $password)
                            .textFieldStyle(.roundedBorder)
                    }.padding(.horizontal)

                    if let error = authManager.errorMessage {
                        Text(error).foregroundColor(.red).font(.caption)
                    }

                    Button(action: login) {
                        if authManager.isLoading {
                            ProgressView().tint(.white)
                        } else {
                            Text("Sign In").bold()
                        }
                    }
                    .frame(maxWidth: .infinity, minHeight: 50)
                    .background(Color.teal)
                    .foregroundColor(.white)
                    .cornerRadius(12)
                    .padding(.horizontal)
                    .disabled(authManager.isLoading)

                    Button("Don't have an account? Register") {
                        showRegister = true
                    }.foregroundColor(.teal)
                }
            }
            .sheet(isPresented: $showRegister) {
                RegisterView()
            }
        }
    }

    private func login() {
        Task {
            if isStaff {
                await authManager.staffLogin(username: username, password: password)
            } else {
                await authManager.patientLogin(username: username, password: password)
            }
        }
    }
}
