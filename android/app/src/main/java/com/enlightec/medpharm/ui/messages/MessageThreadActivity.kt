/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.messages

import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import com.enlightec.medpharm.databinding.ActivityMessageThreadBinding
import com.enlightec.medpharm.util.Resource

class MessageThreadActivity : AppCompatActivity() {

    companion object {
        const val EXTRA_THREAD_ID = "thread_id"
    }

    private lateinit var binding: ActivityMessageThreadBinding
    private val viewModel: MessagesViewModel by viewModels()
    private lateinit var adapter: MessagesAdapter
    private var threadId: Int = -1
    private var isClosed: Boolean = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMessageThreadBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setSupportActionBar(binding.toolbar)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)

        threadId = intent.getIntExtra(EXTRA_THREAD_ID, -1)
        if (threadId <= 0) {
            finish()
            return
        }

        adapter = MessagesAdapter()
        binding.recyclerView.layoutManager = LinearLayoutManager(this).apply {
            stackFromEnd = true
        }
        binding.recyclerView.adapter = adapter

        binding.btnSend.setOnClickListener {
            val body = binding.etReply.text.toString().trim()
            if (body.isEmpty() || isClosed) return@setOnClickListener
            viewModel.reply(threadId, body)
        }

        viewModel.thread.observe(this) { result ->
            when (result) {
                is Resource.Loading -> {}
                is Resource.Success -> {
                    val thread = result.data.thread
                    supportActionBar?.title = thread.subject
                    supportActionBar?.subtitle =
                        thread.providerName.ifBlank { "Care team" }
                    isClosed = thread.isClosed
                    binding.replyBar.visibility = if (isClosed) View.GONE else View.VISIBLE
                    binding.tvClosed.visibility = if (isClosed) View.VISIBLE else View.GONE
                    adapter.submitList(result.data.messages)
                    if (result.data.messages.isNotEmpty()) {
                        binding.recyclerView.scrollToPosition(result.data.messages.size - 1)
                    }
                }
                is Resource.Error -> {
                    Toast.makeText(this, result.message, Toast.LENGTH_LONG).show()
                }
            }
        }

        viewModel.replyResult.observe(this) { result ->
            when (result) {
                is Resource.Success -> {
                    binding.etReply.setText("")
                    viewModel.loadThread(threadId)
                }
                is Resource.Error -> {
                    Toast.makeText(this, result.message, Toast.LENGTH_LONG).show()
                }
                else -> {}
            }
        }
    }

    override fun onResume() {
        super.onResume()
        viewModel.loadThread(threadId)
    }

    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }
}
