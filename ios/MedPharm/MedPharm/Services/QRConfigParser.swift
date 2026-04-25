/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 *
 * QRConfigParser — Normalises a scanned/pasted string to an API base URL.
 * The server-side `start_ngrok.sh` and `start_docker_hub.sh ngrok` helpers
 * generate a QR code containing either:
 *
 *   1. The plain API base URL  e.g.  https://abc123.ngrok-free.app/api/v1
 *   2. The full client config  e.g.  {"api_base_url":"https://abc123.ngrok-free.app/api/v1", ...}
 *   3. A bare public ngrok URL e.g.  https://abc123.ngrok-free.app
 *
 * The parser accepts any of those and returns a clean URL string usable as
 * the API base. Whitespace is trimmed; an `/api/v1` suffix is added when a
 * bare host is provided. Empty input returns "".
 */

import Foundation

enum QRConfigParser {
    static func normalize(_ raw: String) -> String {
        let trimmed = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return "" }

        // Try JSON first: {"api_base_url": "..."} or {"public_url": "..."}
        if trimmed.hasPrefix("{"), let data = trimmed.data(using: .utf8) {
            if let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                if let v = obj["api_base_url"] as? String, !v.isEmpty {
                    return v
                }
                if let v = obj["public_url"] as? String, !v.isEmpty {
                    return appendingApiSuffixIfMissing(v)
                }
            }
        }

        // Plain URL — append /api/v1 if it looks like a bare host.
        if trimmed.lowercased().hasPrefix("http://") || trimmed.lowercased().hasPrefix("https://") {
            return appendingApiSuffixIfMissing(trimmed)
        }

        // Fall back to the raw string; the user can edit before logging in.
        return trimmed
    }

    private static func appendingApiSuffixIfMissing(_ url: String) -> String {
        let stripped = url.hasSuffix("/") ? String(url.dropLast()) : url
        if stripped.contains("/api/") {
            return stripped
        }
        return stripped + "/api/v1"
    }
}
