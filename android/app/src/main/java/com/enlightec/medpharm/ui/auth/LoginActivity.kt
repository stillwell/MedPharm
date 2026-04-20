/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.auth

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import com.enlightec.medpharm.R
import com.enlightec.medpharm.data.api.ApiClient
import com.enlightec.medpharm.data.api.ServerConfig
import com.enlightec.medpharm.databinding.ActivityLoginBinding
import com.enlightec.medpharm.ui.dashboard.MainActivity
import com.enlightec.medpharm.util.Resource
import com.enlightec.medpharm.util.TokenManager

class LoginActivity : AppCompatActivity() {

    private lateinit var binding: ActivityLoginBinding
    private val viewModel: AuthViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Auto-redirect if already logged in
        val tokenManager = TokenManager.getInstance(this)
        if (tokenManager.isLoggedIn) {
            startMainActivity()
            return
        }

        binding = ActivityLoginBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupUI()
        observeViewModel()
    }

    private fun setupUI() {
        val serverConfig = ServerConfig.getInstance(this)
        binding.etServerUrl.setText(serverConfig.apiBaseUrl)

        binding.tvResetServerUrl.setOnClickListener {
            binding.etServerUrl.setText(ServerConfig.DEFAULT_API_BASE_URL)
        }

        binding.btnLogin.setOnClickListener {
            val username = binding.etUsername.text.toString().trim()
            val password = binding.etPassword.text.toString()
            val serverUrl = binding.etServerUrl.text.toString().trim()

            if (username.isEmpty() || password.isEmpty()) {
                Toast.makeText(this, "Please enter both username and password", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            if (serverUrl.isEmpty()) {
                Toast.makeText(this, "Please enter a server URL", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            if (serverUrl != serverConfig.apiBaseUrl) {
                serverConfig.apiBaseUrl = serverUrl
                ApiClient.reconfigure()
            }

            if (binding.rgLoginType.checkedRadioButtonId == R.id.rbStaff) {
                viewModel.staffLogin(username, password)
            } else {
                viewModel.patientLogin(username, password)
            }
        }

        binding.tvRegister.setOnClickListener {
            startActivity(Intent(this, RegisterActivity::class.java))
        }
    }

    private fun observeViewModel() {
        viewModel.loginResult.observe(this) { result ->
            when (result) {
                is Resource.Loading -> {
                    binding.progressBar.visibility = View.VISIBLE
                    binding.btnLogin.isEnabled = false
                }
                is Resource.Success -> {
                    binding.progressBar.visibility = View.GONE
                    val response = result.data
                    val tokenManager = TokenManager.getInstance(this)
                    tokenManager.saveLoginResponse(
                        accessToken = response.accessToken,
                        refreshToken = response.refreshToken,
                        userId = response.user.id,
                        patientId = response.user.patientId ?: -1,
                        username = response.user.username,
                        name = response.user.name,
                        type = response.user.type,
                        role = response.user.role ?: ""
                    )
                    Toast.makeText(this, "Welcome, ${response.user.name}!", Toast.LENGTH_SHORT).show()
                    startMainActivity()
                }
                is Resource.Error -> {
                    binding.progressBar.visibility = View.GONE
                    binding.btnLogin.isEnabled = true
                    Toast.makeText(this, result.message, Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    private fun startMainActivity() {
        startActivity(Intent(this, MainActivity::class.java))
        finish()
    }
}
