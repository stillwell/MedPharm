/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.prescriptions

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.recyclerview.widget.LinearLayoutManager
import com.enlightec.medpharm.databinding.FragmentPrescriptionsBinding
import com.enlightec.medpharm.util.Resource

class PrescriptionsFragment : Fragment() {

    private var _binding: FragmentPrescriptionsBinding? = null
    private val binding get() = _binding!!
    private val viewModel: PrescriptionsViewModel by viewModels()
    private lateinit var adapter: PrescriptionsAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentPrescriptionsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        adapter = PrescriptionsAdapter { prescription ->
            viewModel.requestRefill(prescription.id)
        }
        binding.recyclerView.layoutManager = LinearLayoutManager(requireContext())
        binding.recyclerView.adapter = adapter

        binding.swipeRefresh.setOnRefreshListener { viewModel.loadPrescriptions() }

        binding.chipAll.setOnClickListener { viewModel.loadPrescriptions() }
        binding.chipActive.setOnClickListener { viewModel.loadPrescriptions("active") }
        binding.chipExpired.setOnClickListener { viewModel.loadPrescriptions("expired") }

        viewModel.prescriptions.observe(viewLifecycleOwner) { result ->
            when (result) {
                is Resource.Loading -> binding.swipeRefresh.isRefreshing = true
                is Resource.Success -> {
                    binding.swipeRefresh.isRefreshing = false
                    adapter.submitList(result.data.prescriptions)
                    binding.tvEmpty.visibility =
                        if (result.data.prescriptions.isEmpty()) View.VISIBLE else View.GONE
                }
                is Resource.Error -> {
                    binding.swipeRefresh.isRefreshing = false
                    Toast.makeText(requireContext(), result.message, Toast.LENGTH_LONG).show()
                }
            }
        }

        viewModel.refillResult.observe(viewLifecycleOwner) { result ->
            when (result) {
                is Resource.Success -> {
                    Toast.makeText(requireContext(), result.data.message ?: "Refill requested", Toast.LENGTH_SHORT).show()
                    viewModel.loadPrescriptions()
                }
                is Resource.Error -> Toast.makeText(requireContext(), result.message, Toast.LENGTH_LONG).show()
                is Resource.Loading -> { /* handled by swipe refresh */ }
            }
        }

        viewModel.loadPrescriptions()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
