/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import Foundation

enum APIError: Error, LocalizedError {
    case invalidURL
    case invalidResponse
    case unauthorized
    case serverError(String)
    case networkError(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL: return "Invalid URL"
        case .invalidResponse: return "Invalid server response"
        case .unauthorized: return "Session expired. Please log in again."
        case .serverError(let msg): return msg
        case .networkError(let err): return err.localizedDescription
        }
    }
}

actor APIClient {
    static let shared = APIClient()

    static let defaultBaseURL = "https://medpharm-erp.enlightec.com:8080/api/v1"
    private static let baseURLKey = "medpharm.apiBaseURL"

    static var storedBaseURL: String {
        UserDefaults.standard.string(forKey: baseURLKey) ?? defaultBaseURL
    }

    static func saveBaseURL(_ url: String) {
        let trimmed = url.trimmingCharacters(in: .whitespacesAndNewlines)
        let value = trimmed.isEmpty ? defaultBaseURL : trimmed
        UserDefaults.standard.set(value, forKey: baseURLKey)
        Task { await APIClient.shared.setBaseURL(value) }
    }

    private var baseURL: String = APIClient.storedBaseURL

    private var accessToken: String? {
        get { KeychainHelper.get(key: "access_token") }
        set { KeychainHelper.set(key: "access_token", value: newValue) }
    }

    private var refreshToken: String? {
        get { KeychainHelper.get(key: "refresh_token") }
        set { KeychainHelper.set(key: "refresh_token", value: newValue) }
    }

    func setTokens(access: String, refresh: String) {
        accessToken = access
        refreshToken = refresh
    }

    func clearTokens() {
        accessToken = nil
        refreshToken = nil
    }

    func setBaseURL(_ url: String) {
        baseURL = url
    }

    // MARK: - Generic Request

    func request<T: Decodable>(_ endpoint: String, method: String = "GET",
                                body: Encodable? = nil) async throws -> T {
        guard let url = URL(string: "\(baseURL)/\(endpoint)") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("true", forHTTPHeaderField: "ngrok-skip-browser-warning")

        if let token = accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        if let body = body {
            request.httpBody = try JSONEncoder().encode(body)
        }

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        if httpResponse.statusCode == 401 {
            // Try token refresh
            if let newToken = try? await refreshAccessToken() {
                accessToken = newToken
                request.setValue("Bearer \(newToken)", forHTTPHeaderField: "Authorization")
                let (retryData, retryResponse) = try await URLSession.shared.data(for: request)
                guard let retryHttp = retryResponse as? HTTPURLResponse,
                      (200...299).contains(retryHttp.statusCode) else {
                    throw APIError.unauthorized
                }
                return try JSONDecoder().decode(T.self, from: retryData)
            }
            throw APIError.unauthorized
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            if let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                throw APIError.serverError(errorResponse.error)
            }
            throw APIError.serverError("Server error (\(httpResponse.statusCode))")
        }

        return try JSONDecoder().decode(T.self, from: data)
    }

    private func refreshAccessToken() async throws -> String? {
        guard let refresh = refreshToken else { return nil }

        struct RefreshBody: Encodable { let refresh_token: String }
        struct RefreshResponse: Decodable { let access_token: String }

        guard let url = URL(string: "\(baseURL)/auth/refresh") else { return nil }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("true", forHTTPHeaderField: "ngrok-skip-browser-warning")
        request.httpBody = try JSONEncoder().encode(RefreshBody(refresh_token: refresh))

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else { return nil }
        let decoded = try JSONDecoder().decode(RefreshResponse.self, from: data)
        return decoded.access_token
    }
}

// MARK: - Keychain Helper

enum KeychainHelper {
    static func set(key: String, value: String?) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key
        ]
        SecItemDelete(query as CFDictionary)
        guard let value = value, let data = value.data(using: .utf8) else { return }
        let attributes: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: data
        ]
        SecItemAdd(attributes as CFDictionary, nil)
    }

    static func get(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        var result: AnyObject?
        guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess,
              let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }
}
