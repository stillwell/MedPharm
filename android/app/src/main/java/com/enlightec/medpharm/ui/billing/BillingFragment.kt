/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.billing

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.Spinner
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.recyclerview.widget.LinearLayoutManager
import com.enlightec.medpharm.R
import com.enlightec.medpharm.data.model.InsuranceRecord
import com.enlightec.medpharm.data.model.Invoice
import com.enlightec.medpharm.databinding.FragmentBillingBinding
import com.enlightec.medpharm.util.Resource
import com.google.android.material.textfield.TextInputEditText

class BillingFragment : Fragment() {

    private var _binding: FragmentBillingBinding? = null
    private val binding get() = _binding!!
    private val viewModel: BillingViewModel by viewModels()
    private lateinit var adapter: InvoicesAdapter
    private var cachedInsurance: List<InsuranceRecord> = emptyList()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentBillingBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        adapter = InvoicesAdapter(
            onPayClick = { invoice -> showPayDialog(invoice) },
            onClaimClick = { invoice -> showClaimDialog(invoice) }
        )
        binding.recyclerView.layoutManager = LinearLayoutManager(requireContext())
        binding.recyclerView.adapter = adapter

        binding.swipeRefresh.setOnRefreshListener {
            viewModel.loadBilling()
            viewModel.loadProfile()
        }

        viewModel.billingData.observe(viewLifecycleOwner) { result ->
            when (result) {
                is Resource.Loading -> binding.swipeRefresh.isRefreshing = true
                is Resource.Success -> {
                    binding.swipeRefresh.isRefreshing = false
                    val data = result.data
                    binding.tvOutstandingBalance.text = String.format("$%.2f", data.outstandingBalance)
                    adapter.submitList(data.invoices)
                    binding.tvEmpty.visibility =
                        if (data.invoices.isEmpty()) View.VISIBLE else View.GONE
                }
                is Resource.Error -> {
                    binding.swipeRefresh.isRefreshing = false
                    Toast.makeText(requireContext(), result.message, Toast.LENGTH_LONG).show()
                }
            }
        }

        viewModel.profile.observe(viewLifecycleOwner) { result ->
            if (result is Resource.Success) {
                cachedInsurance = result.data.insurance.filter { it.isActive }
            }
        }

        viewModel.paymentResult.observe(viewLifecycleOwner) { result ->
            when (result) {
                is Resource.Success -> {
                    Toast.makeText(requireContext(),
                        result.data.message ?: "Payment processed",
                        Toast.LENGTH_SHORT).show()
                    viewModel.loadBilling()
                }
                is Resource.Error -> Toast.makeText(requireContext(), result.message, Toast.LENGTH_LONG).show()
                is Resource.Loading -> { /* handled */ }
            }
        }

        viewModel.claimResult.observe(viewLifecycleOwner) { result ->
            when (result) {
                is Resource.Success -> {
                    Toast.makeText(requireContext(),
                        result.data.message ?: getString(R.string.claim_submitted),
                        Toast.LENGTH_SHORT).show()
                    viewModel.loadBilling()
                }
                is Resource.Error -> Toast.makeText(requireContext(), result.message, Toast.LENGTH_LONG).show()
                is Resource.Loading -> { /* handled */ }
            }
        }

        viewModel.loadBilling()
        viewModel.loadProfile()
    }

    private fun showPayDialog(invoice: Invoice) {
        if (invoice.balanceDue <= 0) return
        val dialogView = LayoutInflater.from(requireContext()).inflate(R.layout.dialog_pay, null)
        val etAmount = dialogView.findViewById<TextInputEditText>(R.id.etAmount)
        val spinnerMethod = dialogView.findViewById<Spinner>(R.id.spinnerPaymentMethod)
        etAmount.setText(String.format("%.2f", invoice.balanceDue))

        AlertDialog.Builder(requireContext())
            .setTitle("Pay Invoice ${invoice.invoiceNumber}")
            .setView(dialogView)
            .setPositiveButton("Pay") { _, _ ->
                val amount = etAmount.text.toString().toDoubleOrNull()
                val methodLabel = spinnerMethod.selectedItem?.toString() ?: "Credit Card"
                val methodKey = methodLabel.lowercase()
                    .replace(" ", "_")
                    .replace("/", "_")
                if (amount != null && amount > 0 && amount <= invoice.balanceDue) {
                    viewModel.payInvoice(invoice.id, amount, methodKey)
                } else {
                    Toast.makeText(requireContext(), "Invalid amount", Toast.LENGTH_SHORT).show()
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun showClaimDialog(invoice: Invoice) {
        val dialogView = LayoutInflater.from(requireContext())
            .inflate(R.layout.dialog_insurance_claim, null)
        val spinner = dialogView.findViewById<Spinner>(R.id.spinnerInsurance)
        val etNotes = dialogView.findViewById<TextInputEditText>(R.id.etNotes)
        val tvNone = dialogView.findViewById<View>(R.id.tvNoInsurance)

        if (cachedInsurance.isEmpty()) {
            spinner.visibility = View.GONE
            tvNone.visibility = View.VISIBLE
        } else {
            val labels = cachedInsurance.map {
                "${it.providerName} (${it.policyNumber})"
            }
            spinner.adapter = ArrayAdapter(
                requireContext(),
                android.R.layout.simple_spinner_dropdown_item,
                labels
            )
        }

        AlertDialog.Builder(requireContext())
            .setTitle("${getString(R.string.file_insurance_claim)} — ${invoice.invoiceNumber}")
            .setView(dialogView)
            .setPositiveButton("Submit") { _, _ ->
                if (cachedInsurance.isEmpty()) return@setPositiveButton
                val selected = cachedInsurance.getOrNull(spinner.selectedItemPosition)
                    ?: return@setPositiveButton
                val notes = etNotes.text?.toString()?.takeIf { it.isNotBlank() }
                viewModel.submitInsuranceClaim(invoice.id, selected.id, notes)
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
