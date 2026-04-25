/*
 * MedPharm ERP - iOS Application
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
    @State private var isStaff = false
    @State private var showRegister = false
    @State private var showScanner = false
    @State private var serverURL: String = APIClient.storedBaseURL
    @State private var pulse = false

    var body: some View {
        NavigationStack {
            ZStack {
                MPBackground()

                ScrollView {
                    VStack(spacing: 24) {
                        Spacer().frame(height: 32)

                        // Brand logo with pulsing halo
                        ZStack {
                            Circle()
                                .fill(MPGradient.primary)
                                .frame(width: 120, height: 120)
                                .blur(radius: 40)
                                .opacity(0.55)
                                .scaleEffect(pulse ? 1.15 : 0.95)
                                .animation(.easeInOut(duration: 2.4).repeatForever(autoreverses: true), value: pulse)

                            Image(systemName: "heart.text.square.fill")
                                .font(.system(size: 68, weight: .semibold))
                                .foregroundStyle(MPGradient.primary)
                                .shadow(color: MPColor.primary.opacity(0.6), radius: 20)
                        }
                        .frame(height: 110)

                        VStack(spacing: 6) {
                            Text("MedPharm ERP")
                                .font(.system(size: 34, weight: .bold, design: .default))
                                .foregroundStyle(MPGradient.primary)
                            Text("MEDICAL · PHARMACEUTICAL · SECURE")
                                .font(.system(size: 11, weight: .semibold))
                                .kerning(1.8)
                                .foregroundColor(MPColor.textMuted)
                        }

                        // Glass form card
                        VStack(spacing: 18) {
                            Picker("Login Type", selection: $isStaff) {
                                Text("Patient").tag(false)
                                Text("Staff").tag(true)
                            }
                            .pickerStyle(.segmented)

                            VStack(alignment: .leading, spacing: 6) {
                                Text("SERVER URL").font(.caption).kerning(1.4).foregroundColor(MPColor.textMuted)
                                TextField("", text: $serverURL)
                                    .textFieldStyle(MPTextFieldStyle())
                                    .autocapitalization(.none)
                                    .disableAutocorrection(true)
                                    .keyboardType(.URL)
                                HStack(spacing: 16) {
                                    Button(action: { showScanner = true }) {
                                        Label("Scan QR", systemImage: "qrcode.viewfinder")
                                            .font(.caption)
                                    }
                                    .foregroundColor(MPColor.primary)
                                    Button("Reset to Default") {
                                        serverURL = APIClient.defaultBaseURL
                                    }
                                    .font(.caption)
                                    .foregroundColor(MPColor.primary)
                                    Spacer()
                                }
                            }

                            VStack(spacing: 12) {
                                TextField("Username", text: $username)
                                    .textFieldStyle(MPTextFieldStyle())
                                    .autocapitalization(.none)
                                    .disableAutocorrection(true)

                                SecureField("Password", text: $password)
                                    .textFieldStyle(MPTextFieldStyle())
                            }

                            if let error = authManager.errorMessage {
                                Text(error)
                                    .foregroundColor(MPColor.danger)
                                    .font(.caption)
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 8)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .background(RoundedRectangle(cornerRadius: 10).fill(MPColor.danger.opacity(0.12)))
                            }

                            Button(action: login) {
                                if authManager.isLoading {
                                    ProgressView().tint(Color(red: 0.024, green: 0.067, blue: 0.110))
                                } else {
                                    HStack(spacing: 8) {
                                        Image(systemName: "arrow.right.circle.fill")
                                        Text("Sign In")
                                    }
                                }
                            }
                            .buttonStyle(MPPrimaryButtonStyle())
                            .disabled(authManager.isLoading)

                            Button("Don't have an account? Register") {
                                showRegister = true
                            }
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(MPColor.primary)
                        }
                        .mpCard(padding: 24)
                        .padding(.horizontal, 20)

                        Spacer().frame(height: 12)

                        Text("© 2026 Enlightec Ltd. · HIPAA · TLS")
                            .font(.caption2)
                            .kerning(0.4)
                            .foregroundColor(MPColor.textDim)

                        Spacer().frame(height: 24)
                    }
                    .padding(.horizontal, 4)
                }
            }
            .sheet(isPresented: $showRegister) {
                RegisterView()
            }
            .sheet(isPresented: $showScanner) {
                QRScannerView { scanned in
                    let value = QRConfigParser.normalize(scanned)
                    if !value.isEmpty {
                        serverURL = value
                    }
                    showScanner = false
                }
            }
            .onAppear { pulse = true }
            .preferredColorScheme(.dark)
        }
    }

    private func login() {
        APIClient.saveBaseURL(serverURL)
        Task {
            if isStaff {
                await authManager.staffLogin(username: username, password: password)
            } else {
                await authManager.patientLogin(username: username, password: password)
            }
        }
    }
}

struct MPTextFieldStyle: TextFieldStyle {
    func _body(configuration: TextField<Self._Label>) -> some View {
        configuration
            .padding(.horizontal, 14)
            .padding(.vertical, 12)
            .background(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(MPColor.bg.opacity(0.75))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                            .strokeBorder(MPColor.border, lineWidth: 1)
                    )
            )
            .foregroundColor(MPColor.text)
            .tint(MPColor.primary)
    }
}
