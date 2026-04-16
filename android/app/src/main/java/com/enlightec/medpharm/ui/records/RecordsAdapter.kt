/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.records

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.enlightec.medpharm.R
import com.enlightec.medpharm.data.model.MedicalRecord

class RecordsAdapter : ListAdapter<MedicalRecord, RecordsAdapter.ViewHolder>(DiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_record, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvTitle: TextView = itemView.findViewById(R.id.tvTitle)
        private val tvType: TextView = itemView.findViewById(R.id.tvType)
        private val tvDate: TextView = itemView.findViewById(R.id.tvDate)
        private val tvProvider: TextView = itemView.findViewById(R.id.tvProvider)
        private val tvContent: TextView = itemView.findViewById(R.id.tvContent)

        fun bind(record: MedicalRecord) {
            tvTitle.text = record.title
            tvType.text = record.recordType.replace("_", " ").replaceFirstChar { it.uppercase() }
            tvDate.text = record.recordDate ?: ""
            tvProvider.text = record.providerName ?: ""
            tvContent.text = record.content ?: ""
            tvContent.visibility = if (record.content.isNullOrBlank()) View.GONE else View.VISIBLE
        }
    }

    class DiffCallback : DiffUtil.ItemCallback<MedicalRecord>() {
        override fun areItemsTheSame(old: MedicalRecord, new: MedicalRecord) = old.id == new.id
        override fun areContentsTheSame(old: MedicalRecord, new: MedicalRecord) = old == new
    }
}
