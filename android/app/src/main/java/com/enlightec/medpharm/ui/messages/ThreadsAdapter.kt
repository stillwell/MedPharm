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
import com.enlightec.medpharm.data.model.MessageThread

class ThreadsAdapter(
    private val onClick: (MessageThread) -> Unit,
) : ListAdapter<MessageThread, ThreadsAdapter.VH>(DIFF) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_message_thread, parent, false)
        return VH(view)
    }

    override fun onBindViewHolder(holder: VH, position: Int) {
        val t = getItem(position)
        holder.subject.text = t.subject.ifBlank { "(no subject)" }
        holder.meta.text = buildString {
            append("With ")
            append(t.providerName.ifBlank { "your care team" })
            append(" · ")
            append(t.messageCount)
            append(if (t.messageCount == 1) " message" else " messages")
        }
        holder.timestamp.text = t.lastMessageAt ?: ""
        if (t.unreadCount > 0) {
            holder.unread.visibility = View.VISIBLE
            holder.unread.text = "${t.unreadCount} new"
        } else {
            holder.unread.visibility = View.GONE
        }
        holder.closed.visibility = if (t.isClosed) View.VISIBLE else View.GONE
        holder.itemView.setOnClickListener { onClick(t) }
    }

    class VH(view: View) : RecyclerView.ViewHolder(view) {
        val subject: TextView = view.findViewById(R.id.tvSubject)
        val meta: TextView = view.findViewById(R.id.tvMeta)
        val timestamp: TextView = view.findViewById(R.id.tvTimestamp)
        val unread: TextView = view.findViewById(R.id.tvUnread)
        val closed: TextView = view.findViewById(R.id.tvClosed)
    }

    companion object {
        private val DIFF = object : DiffUtil.ItemCallback<MessageThread>() {
            override fun areItemsTheSame(a: MessageThread, b: MessageThread) = a.id == b.id
            override fun areContentsTheSame(a: MessageThread, b: MessageThread) = a == b
        }
    }
}
