/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.billing

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.enlightec.medpharm.R
import com.enlightec.medpharm.data.model.Invoice

class InvoicesAdapter(
    private val onPayClick: (Invoice) -> Unit,
    private val onClaimClick: (Invoice) -> Unit
) : ListAdapter<Invoice, InvoicesAdapter.ViewHolder>(DiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_invoice, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    inner class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvInvoiceNumber: TextView = itemView.findViewById(R.id.tvInvoiceNumber)
        private val tvDate: TextView = itemView.findViewById(R.id.tvDate)
        private val tvTotal: TextView = itemView.findViewById(R.id.tvTotal)
        private val tvBalance: TextView = itemView.findViewById(R.id.tvBalance)
        private val tvStatus: TextView = itemView.findViewById(R.id.tvStatus)
        private val btnPay: Button = itemView.findViewById(R.id.btnPay)
        private val btnClaim: Button = itemView.findViewById(R.id.btnClaim)

        fun bind(invoice: Invoice) {
            tvInvoiceNumber.text = invoice.invoiceNumber
            tvDate.text = invoice.invoiceDate ?: ""
            tvTotal.text = String.format("$%.2f", invoice.totalAmount)
            tvBalance.text = String.format("$%.2f", invoice.balanceDue)
            tvStatus.text = invoice.status.replaceFirstChar { it.uppercase() }

            val canPay = invoice.balanceDue > 0 && invoice.status in listOf("sent", "partial", "overdue")
            btnPay.visibility = if (canPay) View.VISIBLE else View.GONE
            btnClaim.visibility = if (canPay) View.VISIBLE else View.GONE
            btnPay.setOnClickListener { onPayClick(invoice) }
            btnClaim.setOnClickListener { onClaimClick(invoice) }
        }
    }

    class DiffCallback : DiffUtil.ItemCallback<Invoice>() {
        override fun areItemsTheSame(old: Invoice, new: Invoice) = old.id == new.id
        override fun areContentsTheSame(old: Invoice, new: Invoice) = old == new
    }
}
