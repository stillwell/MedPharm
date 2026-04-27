/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 *
 * Public drug-information URLs. Centralised so the source of truth can be
 * swapped without touching every view that links to it.
 *
 * Default provider is MedlinePlus (NIH/NLM) — public-domain, patient-friendly,
 * no ads or trackers — which is the right default for a clinical app shown
 * to patients. DailyMed (the FDA's official labels database) is offered as
 * an alternative for clinicians who want the prescribing information.
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
    /// Build a search URL for the given medication. The brand name is preferred
    /// (it is what patients recognise) and the generic name is the fallback so
    /// uncommon brands still resolve to a useful page.
    static func url(for med: Medication, source: DrugInfoSource = .medlinePlus) -> URL? {
        let term = (med.brand_name.isEmpty ? med.generic_name : med.brand_name)
            .trimmingCharacters(in: .whitespacesAndNewlines)
        guard !term.isEmpty else { return nil }
        let encoded = term.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? term
        switch source {
        case .medlinePlus:
            // MedlinePlus's homepage search form posts to the NLM vsearch
            // backend; the v:project / v:sources params are required to scope
            // results to MedlinePlus content. The cleaner-looking
            // medlineplus.gov/search.html does not exist (404).
            return URL(string:
                "https://vsearch.nlm.nih.gov/vivisimo/cgi-bin/query-meta"
                + "?v%3Aproject=medlineplus"
                + "&v%3Asources=medlineplus-bundle"
                + "&query=\(encoded)")
        case .dailyMed:
            return URL(string: "https://dailymed.nlm.nih.gov/dailymed/search.cfm?query=\(encoded)")
        case .drugsCom:
            return URL(string: "https://www.drugs.com/search.php?searchterm=\(encoded)")
        }
    }
}
