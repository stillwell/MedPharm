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
    @State private var serverURL: String = APIClient.storedBaseURL
    @State private var pulse = false

    var body: some View {
        ZStack {
            MPBackground()

            VStack(spacing: 0) {
                Spacer().frame(height: 40)

                // Brand
                ZStack {
                    Circle()
                        .fill(MPGradient.primary)
                        .frame(width: 140, height: 140)
                        .blur(radius: 48)
                        .opacity(0.5)
                        .scaleEffect(pulse ? 1.12 : 0.94)
                        .animation(.easeInOut(duration: 2.4).repeatForever(autoreverses: true), value: pulse)

                    Image(systemName: "cross.case.fill")
                        .font(.system(size: 72, weight: .semibold))
                        .foregroundStyle(MPGradient.primary)
                        .shadow(color: MPColor.primary.opacity(0.55), radius: 18)
                }
                .frame(height: 120)

                Text("MedPharm ERP")
                    .font(.system(size: 36, weight: .bold))
                    .foregroundStyle(MPGradient.primary)
                    .padding(.top, 14)

                Text("MEDICAL · PHARMACEUTICAL · SECURE")
                    .font(.system(size: 11, weight: .semibold))
                    .kerning(2.0)
                    .foregroundColor(MPColor.textMuted)
                    .padding(.top, 4)

                // Form
                VStack(alignment: .leading, spacing: 16) {
                    Picker("Login As", selection: $loginType) {
                        Text("Patient").tag("Patient")
                        Text("Staff").tag("Staff")
                    }.pickerStyle(.segmented)

                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text("SERVER URL").font(.caption).kerning(1.2).foregroundColor(MPColor.textMuted)
                            Spacer()
                            Button("Reset") {
                                serverURL = APIClient.defaultBaseURL
                            }
                            .font(.caption)
                            .buttonStyle(.link)
                            .foregroundColor(MPColor.primary)
                        }
                        TextField("https://medpharm-erp.enlightec.com:8080/api/v1",
                                  text: $serverURL)
                            .textFieldStyle(MPTextFieldStyle())
                            .disableAutocorrection(true)
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        Text("USERNAME").font(.caption).kerning(1.2).foregroundColor(MPColor.textMuted)
                        TextField("", text: $username).textFieldStyle(MPTextFieldStyle())
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        Text("PASSWORD").font(.caption).kerning(1.2).foregroundColor(MPColor.textMuted)
                        SecureField("", text: $password).textFieldStyle(MPTextFieldStyle())
                    }

                    if let error = authManager.errorMessage {
                        Text(error)
                            .foregroundColor(MPColor.danger)
                            .font(.caption)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(10)
                            .background(
                                RoundedRectangle(cornerRadius: 10).fill(MPColor.danger.opacity(0.12))
                            )
                    }

                    Button(action: login) {
                        if authManager.isLoading {
                            ProgressView().scaleEffect(0.7)
                        } else {
                            Label("Log In", systemImage: "arrow.right.circle.fill")
                        }
                    }
                    .buttonStyle(MPPrimaryButtonStyle())
                    .disabled(authManager.isLoading || username.isEmpty || password.isEmpty)
                }
                .mpCard(padding: 24)
                .frame(maxWidth: 420)
                .padding(.top, 28)

                Spacer()

                Text("© 2026 Enlightec Ltd. · HIPAA · TLS")
                    .font(.caption2)
                    .foregroundColor(MPColor.textDim)
                    .padding(.bottom, 20)
            }
            .padding(.horizontal, 40)
        }
        .frame(minWidth: 500, minHeight: 640)
        .onAppear { pulse = true }
        .preferredColorScheme(.dark)
    }

    private func login() {
        APIClient.saveBaseURL(serverURL)
        Task {
            if loginType == "Patient" {
                await authManager.patientLogin(username: username, password: password)
            } else {
                await authManager.staffLogin(username: username, password: password)
            }
        }
    }
}

struct MPTextFieldStyle: TextFieldStyle {
    func _body(configuration: TextField<Self._Label>) -> some View {
        configuration
            .textFieldStyle(.plain)
            .padding(.horizontal, 12)
            .padding(.vertical, 9)
            .background(
                RoundedRectangle(cornerRadius: 10, style: .continuous)
                    .fill(MPColor.bg.opacity(0.75))
                    .overlay(
                        RoundedRectangle(cornerRadius: 10, style: .continuous)
                            .strokeBorder(MPColor.border, lineWidth: 1)
                    )
            )
            .foregroundColor(MPColor.text)
    }
}
