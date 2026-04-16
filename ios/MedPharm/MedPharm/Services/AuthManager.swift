/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import SwiftUI

@MainActor
class AuthManager: ObservableObject {
    @Published var isAuthenticated = false
    @Published var currentUser: UserInfo?
    @Published var isLoading = false
    @Published var errorMessage: String?

    init() {
        isAuthenticated = KeychainHelper.get(key: "access_token") != nil
    }

    func patientLogin(username: String, password: String) async {
        isLoading = true; errorMessage = nil
        do {
            let response: LoginResponse = try await APIClient.shared.request(
                "auth/login/patient", method: "POST",
                body: LoginRequest(username: username, password: password))
            await APIClient.shared.setTokens(access: response.access_token, refresh: response.refresh_token)
            currentUser = response.user
            UserDefaults.standard.set(response.user.name, forKey: "user_name")
            UserDefaults.standard.set(response.user.type, forKey: "user_type")
            isAuthenticated = true
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func staffLogin(username: String, password: String) async {
        isLoading = true; errorMessage = nil
        do {
            let response: LoginResponse = try await APIClient.shared.request(
                "auth/login/staff", method: "POST",
                body: LoginRequest(username: username, password: password))
            await APIClient.shared.setTokens(access: response.access_token, refresh: response.refresh_token)
            currentUser = response.user
            UserDefaults.standard.set(response.user.name, forKey: "user_name")
            UserDefaults.standard.set(response.user.type, forKey: "user_type")
            isAuthenticated = true
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func logout() async {
        await APIClient.shared.clearTokens()
        UserDefaults.standard.removeObject(forKey: "user_name")
        UserDefaults.standard.removeObject(forKey: "user_type")
        currentUser = nil
        isAuthenticated = false
    }
}
