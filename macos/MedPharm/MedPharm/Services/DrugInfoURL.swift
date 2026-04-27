/*
 * MedPharm ERP - macOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 *
 * Public drug-information URLs. Centralised so the source of truth can be
 * swapped without touching every view that links to it. Mirrors the iOS
 * helper of the same name in the iOS target.
 *
 * Default provider is MedlinePlus (NIH/NLM) — public-domain, patient-friendly,
 * no ads or trackers. DailyMed (FDA labels) and Drugs.com are also offered.
 */

import Foundation

enum DrugInfoSource: String, CaseIterable {
    case medlinePlus
    case dailyMed
    case drugsCom

    var displayName: String {
        switch self {
        case .medlinePlus: return "MedlinePlus (NIH)"
        case .dailyMed:    return "DailyMed (FDA labels)"
        case .drugsCom:    return "Drugs.com"
        }
    }
}

enum DrugInfoURL {
    static func url(for med: Medication, source: DrugInfoSource = .medlinePlus) -> URL? {
        let term = (med.brand_name.isEmpty ? med.generic_name : med.brand_name)
            .trimmingCharacters(in: .whitespacesAndNewlines)
        guard !term.isEmpty else { return nil }
        let encoded = term.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? term
        switch source {
        case .medlinePlus:
            return URL(string: "https://medlineplus.gov/search.html?query=\(encoded)")
        case .dailyMed:
            return URL(string: "https://dailymed.nlm.nih.gov/dailymed/search.cfm?query=\(encoded)")
        case .drugsCom:
            return URL(string: "https://www.drugs.com/search.php?searchterm=\(encoded)")
        }
    }
}
