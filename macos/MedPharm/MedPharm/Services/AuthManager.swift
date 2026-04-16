/*
 * MedPharm ERP - macOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import Foundation
import SwiftUI

@MainActor
class AuthManager: ObservableObject {
    @Published var isAuthenticated: Bool = false
    @Published var currentUser: UserInfo?
    @Published var errorMessage: String?
    @Published var isLoading: Bool = false

    init() {
        if KeychainHelper.get(key: "access_token") != nil {
            isAuthenticated = true
        }
    }

    func patientLogin(username: String, password: String) async {
        await login(endpoint: "auth/login/patient", username: username, password: password)
    }

    func staffLogin(username: String, password: String) async {
        await login(endpoint: "auth/login/staff", username: username, password: password)
    }

    private func login(endpoint: String, username: String, password: String) async {
        isLoading = true
        errorMessage = nil
        do {
            let body = LoginRequest(username: username, password: password)
            let response: LoginResponse = try await APIClient.shared.request(
                endpoint, method: "POST", body: body)
            await APIClient.shared.setTokens(
                access: response.access_token, refresh: response.refresh_token)
            currentUser = response.user
            isAuthenticated = true
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func logout() async {
        await APIClient.shared.clearTokens()
        currentUser = nil
        isAuthenticated = false
    }
}
