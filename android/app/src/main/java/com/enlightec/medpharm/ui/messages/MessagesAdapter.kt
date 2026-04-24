/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.messages

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.enlightec.medpharm.R
import com.enlightec.medpharm.data.model.SecureMessage

class MessagesAdapter :
    ListAdapter<SecureMessage, MessagesAdapter.VH>(DIFF) {

    override fun getItemViewType(position: Int): Int {
        return if (getItem(position).senderType == "patient") VIEW_TYPE_PATIENT else VIEW_TYPE_STAFF
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
        val layout = if (viewType == VIEW_TYPE_PATIENT)
            R.layout.item_message_outgoing
        else
            R.layout.item_message_incoming
        val view = LayoutInflater.from(parent.context).inflate(layout, parent, false)
        return VH(view)
    }

    override fun onBindViewHolder(holder: VH, position: Int) {
        val m = getItem(position)
        holder.body.text = m.body
        holder.time.text = m.sentAt ?: ""
    }

    class VH(view: View) : RecyclerView.ViewHolder(view) {
        val body: TextView = view.findViewById(R.id.tvBody)
        val time: TextView = view.findViewById(R.id.tvTime)
    }

    companion object {
        const val VIEW_TYPE_PATIENT = 1
        const val VIEW_TYPE_STAFF = 2

        private val DIFF = object : DiffUtil.ItemCallback<SecureMessage>() {
            override fun areItemsTheSame(a: SecureMessage, b: SecureMessage) = a.id == b.id
            override fun areContentsTheSame(a: SecureMessage, b: SecureMessage) = a == b
        }
    }
}
