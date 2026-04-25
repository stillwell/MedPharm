/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 *
 * QRConfigParser — Normalises a scanned/pasted string to an API base URL.
 * The server-side `start_ngrok.sh` and `start_docker_hub.sh ngrok` helpers
 * generate a QR code containing one of:
 *
 *   1. The plain API base URL  e.g.  https://abc123.ngrok-free.app/api/v1
 *   2. The full client config  e.g.  {"api_base_url":"https://abc123.ngrok-free.app/api/v1", ...}
 *   3. A bare public ngrok URL e.g.  https://abc123.ngrok-free.app
 *
 * The parser accepts any of those and returns a clean URL string usable as
 * the API base. Whitespace is trimmed; an `/api/v1` suffix is added when a
 * bare host is provided. Empty input returns "".
 */

package com.enlightec.medpharm.util

import org.json.JSONObject

object QRConfigParser {

    fun normalize(raw: String): String {
        val trimmed = raw.trim()
        if (trimmed.isEmpty()) return ""

        // Try JSON first: {"api_base_url": "..."} or {"public_url": "..."}
        if (trimmed.startsWith("{")) {
            try {
                val obj = JSONObject(trimmed)
                obj.optString("api_base_url").takeIf { it.isNotEmpty() }?.let { return it }
                obj.optString("public_url").takeIf { it.isNotEmpty() }
                    ?.let { return appendApiSuffixIfMissing(it) }
            } catch (_: Exception) {
                // fall through to URL handling
            }
        }

        // Plain URL — append /api/v1 if it looks like a bare host.
        val lower = trimmed.lowercase()
        if (lower.startsWith("http://") || lower.startsWith("https://")) {
            return appendApiSuffixIfMissing(trimmed)
        }

        // Fall back to the raw string; the user can edit before logging in.
        return trimmed
    }

    private fun appendApiSuffixIfMissing(url: String): String {
        val stripped = if (url.endsWith("/")) url.dropLast(1) else url
        return if (stripped.contains("/api/")) stripped else "$stripped/api/v1"
    }
}
