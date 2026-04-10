/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.records

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.recyclerview.widget.LinearLayoutManager
import com.enlightec.medpharm.databinding.FragmentRecordsBinding
import com.enlightec.medpharm.util.Resource

class RecordsFragment : Fragment() {

    private var _binding: FragmentRecordsBinding? = null
    private val binding get() = _binding!!
    private val viewModel: RecordsViewModel by viewModels()
    private lateinit var adapter: RecordsAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentRecordsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        adapter = RecordsAdapter()
        binding.recyclerView.layoutManager = LinearLayoutManager(requireContext())
        binding.recyclerView.adapter = adapter

        binding.swipeRefresh.setOnRefreshListener { viewModel.loadRecords() }

        binding.chipAll.setOnClickListener { viewModel.loadRecords() }
        binding.chipVisitNotes.setOnClickListener { viewModel.loadRecords("visit_note") }
        binding.chipLabResults.setOnClickListener { viewModel.loadRecords("lab_result") }
        binding.chipImaging.setOnClickListener { viewModel.loadRecords("imaging") }

        viewModel.records.observe(viewLifecycleOwner) { result ->
            when (result) {
                is Resource.Loading -> binding.swipeRefresh.isRefreshing = true
                is Resource.Success -> {
                    binding.swipeRefresh.isRefreshing = false
                    adapter.submitList(result.data.records)
                    binding.tvEmpty.visibility =
                        if (result.data.records.isEmpty()) View.VISIBLE else View.GONE
                }
                is Resource.Error -> {
                    binding.swipeRefresh.isRefreshing = false
                    Toast.makeText(requireContext(), result.message, Toast.LENGTH_LONG).show()
                }
            }
        }

        viewModel.loadRecords()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
