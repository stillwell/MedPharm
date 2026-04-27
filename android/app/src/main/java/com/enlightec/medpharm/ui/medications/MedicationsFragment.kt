/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.medications

import android.content.ActivityNotFoundException
import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.appcompat.widget.SearchView
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.recyclerview.widget.LinearLayoutManager
import com.enlightec.medpharm.databinding.FragmentMedicationsBinding
import com.enlightec.medpharm.util.DrugInfoUrl
import com.enlightec.medpharm.util.Resource

class MedicationsFragment : Fragment() {

    private var _binding: FragmentMedicationsBinding? = null
    private val binding get() = _binding!!
    private val viewModel: MedicationsViewModel by viewModels()
    private lateinit var adapter: MedicationsAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentMedicationsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        adapter = MedicationsAdapter { med ->
            val uri = DrugInfoUrl.forMedication(med) ?: run {
                Toast.makeText(requireContext(),
                    "No medication name to look up", Toast.LENGTH_SHORT).show()
                return@MedicationsAdapter
            }
            try {
                startActivity(Intent(Intent.ACTION_VIEW, uri))
            } catch (_: ActivityNotFoundException) {
                Toast.makeText(requireContext(),
                    "No browser installed to open drug information", Toast.LENGTH_LONG).show()
            }
        }
        binding.recyclerView.layoutManager = LinearLayoutManager(requireContext())
        binding.recyclerView.adapter = adapter

        binding.swipeRefresh.setOnRefreshListener { viewModel.loadMedications() }

        binding.searchView.setOnQueryTextListener(object : SearchView.OnQueryTextListener {
            override fun onQueryTextSubmit(query: String?): Boolean {
                query?.let { viewModel.searchMedications(it) }
                return true
            }
            override fun onQueryTextChange(newText: String?): Boolean {
                if (newText.isNullOrEmpty()) viewModel.loadMedications()
                return true
            }
        })

        viewModel.medications.observe(viewLifecycleOwner) { result ->
            when (result) {
                is Resource.Loading -> binding.swipeRefresh.isRefreshing = true
                is Resource.Success -> {
                    binding.swipeRefresh.isRefreshing = false
                    adapter.submitList(result.data.medications)
                    binding.tvEmpty.visibility =
                        if (result.data.medications.isEmpty()) View.VISIBLE else View.GONE
                }
                is Resource.Error -> {
                    binding.swipeRefresh.isRefreshing = false
                    Toast.makeText(requireContext(), result.message, Toast.LENGTH_LONG).show()
                }
            }
        }

        viewModel.loadMedications()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
