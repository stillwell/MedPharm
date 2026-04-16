/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.prescriptions

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.enlightec.medpharm.R
import com.enlightec.medpharm.data.model.Prescription

class PrescriptionsAdapter(
    private val onRefillClick: (Prescription) -> Unit
) : ListAdapter<Prescription, PrescriptionsAdapter.ViewHolder>(DiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_prescription, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    inner class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvRxNumber: TextView = itemView.findViewById(R.id.tvRxNumber)
        private val tvStatus: TextView = itemView.findViewById(R.id.tvStatus)
        private val tvPrescriber: TextView = itemView.findViewById(R.id.tvPrescriber)
        private val tvDate: TextView = itemView.findViewById(R.id.tvDate)
        private val tvMedications: TextView = itemView.findViewById(R.id.tvMedications)
        private val btnRefill: Button = itemView.findViewById(R.id.btnRefill)

        fun bind(rx: Prescription) {
            tvRxNumber.text = rx.rxNumber
            tvStatus.text = rx.status.replaceFirstChar { it.uppercase() }
            tvPrescriber.text = rx.prescriberName ?: "Unknown"
            tvDate.text = rx.prescribedDate ?: ""

            val medsText = rx.items?.joinToString("\n") { item ->
                "${item.medicationName ?: "Medication"} - ${item.dosage}, ${item.frequency}"
            } ?: "No medications listed"
            tvMedications.text = medsText

            val hasRefills = rx.items?.any { (it.refillsRemaining) > 0 } == true
            btnRefill.visibility = if (rx.status == "active" && hasRefills) View.VISIBLE else View.GONE
            btnRefill.setOnClickListener { onRefillClick(rx) }
        }
    }

    class DiffCallback : DiffUtil.ItemCallback<Prescription>() {
        override fun areItemsTheSame(old: Prescription, new: Prescription) = old.id == new.id
        override fun areContentsTheSame(old: Prescription, new: Prescription) = old == new
    }
}
