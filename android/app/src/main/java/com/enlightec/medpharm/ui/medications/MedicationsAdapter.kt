/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.medications

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.enlightec.medpharm.R
import com.enlightec.medpharm.data.model.Medication

class MedicationsAdapter : ListAdapter<Medication, MedicationsAdapter.ViewHolder>(DiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_medication, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvBrandName: TextView = itemView.findViewById(R.id.tvBrandName)
        private val tvGenericName: TextView = itemView.findViewById(R.id.tvGenericName)
        private val tvDrugClass: TextView = itemView.findViewById(R.id.tvDrugClass)
        private val tvDosage: TextView = itemView.findViewById(R.id.tvDosage)
        private val tvPrescriber: TextView = itemView.findViewById(R.id.tvPrescriber)
        private val tvIndications: TextView = itemView.findViewById(R.id.tvIndications)

        fun bind(med: Medication) {
            tvBrandName.text = med.brandName
            tvGenericName.text = "(${med.genericName})"
            tvDrugClass.text = med.drugClass ?: ""

            if (med.dosage != null && med.frequency != null) {
                tvDosage.text = "${med.dosage} - ${med.frequency}"
                tvDosage.visibility = View.VISIBLE
            } else {
                tvDosage.visibility = View.GONE
            }

            if (med.prescriberName != null) {
                tvPrescriber.text = "Prescribed by: ${med.prescriberName}"
                tvPrescriber.visibility = View.VISIBLE
            } else {
                tvPrescriber.visibility = View.GONE
            }

            if (!med.indications.isNullOrBlank()) {
                tvIndications.text = med.indications
                tvIndications.visibility = View.VISIBLE
            } else {
                tvIndications.visibility = View.GONE
            }
        }
    }

    class DiffCallback : DiffUtil.ItemCallback<Medication>() {
        override fun areItemsTheSame(old: Medication, new: Medication) = old.id == new.id
        override fun areContentsTheSame(old: Medication, new: Medication) = old == new
    }
}
