/*
 * MedPharm ERP - Android Application
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
 * to patients. DailyMed (FDA labels) and Drugs.com are also available.
 */

package com.enlightec.medpharm.util

import android.net.Uri
import com.enlightec.medpharm.data.model.Medication

enum class DrugInfoSource(val displayName: String) {
    MEDLINE_PLUS("MedlinePlus (NIH)"),
    DAILY_MED("DailyMed (FDA labels)"),
    DRUGS_COM("Drugs.com"),
}

object DrugInfoUrl {
    /**
     * Build a search URL for the given medication. The brand name is preferred
     * (it is what patients recognise) and the generic name is the fallback so
     * uncommon brands still resolve to a useful page. Returns null when both
     * names are blank — the caller should not show a "look up" affordance in
     * that case.
     */
    fun forMedication(med: Medication, source: DrugInfoSource = DrugInfoSource.MEDLINE_PLUS): Uri? {
        val term = med.brandName.trim().ifEmpty { med.genericName.trim() }
        if (term.isEmpty()) return null
        val encoded = Uri.encode(term)
        val url = when (source) {
            // MedlinePlus's homepage search form posts to the NLM vsearch
            // backend; the v:project / v:sources params are required to
            // scope results to MedlinePlus content. The cleaner-looking
            // medlineplus.gov/search.html does not exist (404).
            DrugInfoSource.MEDLINE_PLUS ->
                "https://vsearch.nlm.nih.gov/vivisimo/cgi-bin/query-meta" +
                    "?v%3Aproject=medlineplus" +
                    "&v%3Asources=medlineplus-bundle" +
                    "&query=$encoded"
            DrugInfoSource.DAILY_MED    -> "https://dailymed.nlm.nih.gov/dailymed/search.cfm?query=$encoded"
            DrugInfoSource.DRUGS_COM    -> "https://www.drugs.com/search.php?searchterm=$encoded"
        }
        return Uri.parse(url)
    }
}
