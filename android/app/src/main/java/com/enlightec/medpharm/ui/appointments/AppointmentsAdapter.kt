/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.appointments

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.enlightec.medpharm.R
import com.enlightec.medpharm.data.model.Appointment

class AppointmentsAdapter : ListAdapter<Appointment, AppointmentsAdapter.ViewHolder>(DiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_appointment, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvDateTime: TextView = itemView.findViewById(R.id.tvDateTime)
        private val tvProvider: TextView = itemView.findViewById(R.id.tvProvider)
        private val tvType: TextView = itemView.findViewById(R.id.tvType)
        private val tvStatus: TextView = itemView.findViewById(R.id.tvStatus)
        private val tvReason: TextView = itemView.findViewById(R.id.tvReason)

        fun bind(appt: Appointment) {
            tvDateTime.text = appt.scheduledDatetime ?: "TBD"
            tvProvider.text = appt.providerName ?: "Unknown Provider"
            tvType.text = appt.appointmentType?.replace("_", " ")?.replaceFirstChar { it.uppercase() } ?: ""
            tvStatus.text = appt.status.replace("_", " ").replaceFirstChar { it.uppercase() }
            tvReason.text = appt.reason ?: ""
            tvReason.visibility = if (appt.reason.isNullOrBlank()) View.GONE else View.VISIBLE
        }
    }

    class DiffCallback : DiffUtil.ItemCallback<Appointment>() {
        override fun areItemsTheSame(old: Appointment, new: Appointment) = old.id == new.id
        override fun areContentsTheSame(old: Appointment, new: Appointment) = old == new
    }
}
