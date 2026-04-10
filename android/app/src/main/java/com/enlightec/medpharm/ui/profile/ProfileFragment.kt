/*
 * MedPharm ERP - Android Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

package com.enlightec.medpharm.ui.profile

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import com.enlightec.medpharm.data.model.ProfileUpdateRequest
import com.enlightec.medpharm.databinding.FragmentProfileBinding
import com.enlightec.medpharm.util.Resource

class ProfileFragment : Fragment() {

    private var _binding: FragmentProfileBinding? = null
    private val binding get() = _binding!!
    private val viewModel: ProfileViewModel by viewModels()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentProfileBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        viewModel.profile.observe(viewLifecycleOwner) { result ->
            when (result) {
                is Resource.Loading -> binding.progressBar.visibility = View.VISIBLE
                is Resource.Success -> {
                    binding.progressBar.visibility = View.GONE
                    binding.contentLayout.visibility = View.VISIBLE
                    val patient = result.data.patient
                    binding.tvName.text = patient.fullName
                    binding.tvDob.text = "DOB: ${patient.dob ?: "N/A"}"
                    binding.tvGender.text = "Gender: ${patient.gender?.replaceFirstChar { it.uppercase() } ?: "N/A"}"
                    binding.tvBloodType.text = "Blood Type: ${patient.bloodType ?: "N/A"}"
                    binding.etEmail.setText(patient.email ?: "")
                    binding.etPhone.setText(patient.phone ?: "")
                    binding.etAddress.setText(patient.address ?: "")
                    binding.etCity.setText(patient.city ?: "")
                    binding.etState.setText(patient.state ?: "")
                    binding.etZipCode.setText(patient.zipCode ?: "")

                    // Insurance
                    val insurance = result.data.insurance
                    if (insurance.isNotEmpty()) {
                        val ins = insurance.first()
                        binding.tvInsurance.text = "${ins["provider_name"]} - ${ins["policy_number"]}"
                    } else {
                        binding.tvInsurance.text = "No insurance on file"
                    }

                    // Allergies
                    val allergies = result.data.allergies
                    if (allergies.isNotEmpty()) {
                        binding.tvAllergies.text = allergies.joinToString("\n") { a ->
                            val allergy = a as? Map<*, *>
                            "${allergy?.get("allergen")} (${allergy?.get("severity")})"
                        }
                    } else {
                        binding.tvAllergies.text = "No known allergies"
                    }
                }
                is Resource.Error -> {
                    binding.progressBar.visibility = View.GONE
                    Toast.makeText(requireContext(), result.message, Toast.LENGTH_LONG).show()
                }
            }
        }

        viewModel.updateResult.observe(viewLifecycleOwner) { result ->
            when (result) {
                is Resource.Success -> {
                    Toast.makeText(requireContext(), "Profile updated", Toast.LENGTH_SHORT).show()
                }
                is Resource.Error -> Toast.makeText(requireContext(), result.message, Toast.LENGTH_LONG).show()
                is Resource.Loading -> { /* handled */ }
            }
        }

        binding.btnSave.setOnClickListener {
            viewModel.updateProfile(ProfileUpdateRequest(
                email = binding.etEmail.text.toString().trim(),
                phone = binding.etPhone.text.toString().trim(),
                address = binding.etAddress.text.toString().trim(),
                city = binding.etCity.text.toString().trim(),
                state = binding.etState.text.toString().trim(),
                zipCode = binding.etZipCode.text.toString().trim()
            ))
        }

        viewModel.loadProfile()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
