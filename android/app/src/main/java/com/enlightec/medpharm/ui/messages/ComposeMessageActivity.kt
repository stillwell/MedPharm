/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.messages

import android.content.Intent
import android.os.Bundle
import android.widget.ArrayAdapter
import android.widget.Toast
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import com.enlightec.medpharm.data.model.ProviderSummary
import com.enlightec.medpharm.databinding.ActivityComposeMessageBinding
import com.enlightec.medpharm.util.Resource

class ComposeMessageActivity : AppCompatActivity() {

    private lateinit var binding: ActivityComposeMessageBinding
    private val viewModel: MessagesViewModel by viewModels()
    private var providers: List<ProviderSummary> = emptyList()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityComposeMessageBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setSupportActionBar(binding.toolbar)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = "New Message"

        binding.btnSend.setOnClickListener { send() }
        binding.btnCancel.setOnClickListener { finish() }

        viewModel.providers.observe(this) { result ->
            if (result is Resource.Success) {
                providers = result.data.providers
                val labels = listOf("Any available clinician") +
                        providers.map {
                            val suffix = it.specialization?.takeIf { s -> s.isNotBlank() }
                                ?.let { s -> " — $s" }
                                ?: ""
                            "${it.displayTitle}$suffix"
                        }
                binding.spinnerProvider.adapter = ArrayAdapter(
                    this,
                    android.R.layout.simple_spinner_dropdown_item,
                    labels,
                )
            }
        }

        viewModel.newThread.observe(this) { result ->
            when (result) {
                is Resource.Success -> {
                    val threadId = result.data.threadId
                    startActivity(
                        Intent(this, MessageThreadActivity::class.java)
                            .putExtra(MessageThreadActivity.EXTRA_THREAD_ID, threadId)
                    )
                    finish()
                }
                is Resource.Error -> {
                    binding.btnSend.isEnabled = true
                    Toast.makeText(this, result.message, Toast.LENGTH_LONG).show()
                }
                else -> {}
            }
        }

        viewModel.loadProviders()
    }

    private fun send() {
        val subject = binding.etSubject.text.toString().trim()
        val body = binding.etBody.text.toString().trim()
        if (subject.isEmpty() || body.isEmpty()) {
            Toast.makeText(this, "Subject and message are required", Toast.LENGTH_SHORT).show()
            return
        }
        val idx = binding.spinnerProvider.selectedItemPosition
        val providerId = if (idx <= 0) null else providers.getOrNull(idx - 1)?.id
        binding.btnSend.isEnabled = false
        viewModel.createThread(subject, body, providerId)
    }

    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }
}
