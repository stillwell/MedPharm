/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct BillingView: View {
    @State private var billing: BillingData?
    @State private var isLoading = true
    @State private var selectedInvoice: Invoice?
    @State private var showPaySheet = false
    @State private var showClaimSheet = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            Group {
                if isLoading {
                    ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if let billing = billing {
                    List {
                        Section {
                            HStack {
                                Text("Outstanding Balance").font(.headline)
                                Spacer()
                                Text(String(format: "$%.2f", billing.outstanding_balance))
                                    .font(.title3).bold()
                                    .foregroundColor(billing.outstanding_balance > 0 ? .orange : .green)
                            }
                        }

                        Section("Invoices") {
                            if billing.invoices.isEmpty {
                                Text("No invoices").foregroundColor(.secondary)
                            } else {
                                ForEach(billing.invoices) { invoice in
                                    InvoiceRow(invoice: invoice) {
                                        selectedInvoice = invoice
                                        showPaySheet = true
                                    } onClaim: {
                                        selectedInvoice = invoice
                                        showClaimSheet = true
                                    }
                                }
                            }
                        }

                        Section("Payment History") {
                            if billing.payments.isEmpty {
                                Text("No payments").foregroundColor(.secondary)
                            } else {
                                ForEach(billing.payments) { payment in
                                    HStack {
                                        VStack(alignment: .leading) {
                                            Text(payment.payment_method).font(.subheadline)
                                            Text(payment.payment_date ?? "").font(.caption2)
                                                .foregroundColor(.secondary)
                                        }
                                        Spacer()
                                        Text(String(format: "$%.2f", payment.amount))
                                            .foregroundColor(.green)
                                    }
                                }
                            }
                        }
                    }
                } else {
                    Text("Unable to load billing").foregroundColor(.secondary)
                }
            }
            .navigationTitle("Billing")
            .refreshable { await load() }
            .task { await load() }
            .sheet(isPresented: $showPaySheet) {
                if let invoice = selectedInvoice {
                    PaymentSheet(invoice: invoice) {
                        showPaySheet = false
                        Task { await load() }
                    }
                }
            }
            .sheet(isPresented: $showClaimSheet) {
                if let invoice = selectedInvoice {
                    InsuranceClaimSheet(invoice: invoice) {
                        showClaimSheet = false
                        Task { await load() }
                    }
                }
            }
            .alert("Error", isPresented: .constant(errorMessage != nil), actions: {
                Button("OK") { errorMessage = nil }
            }, message: { Text(errorMessage ?? "") })
        }
    }

    private func load() async {
        isLoading = true
        do {
            billing = try await APIClient.shared.request("patient/billing")
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}

struct InvoiceRow: View {
    let invoice: Invoice
    let onPay: () -> Void
    let onClaim: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(invoice.invoice_number).font(.headline).foregroundColor(.teal)
                Spacer()
                StatusBadge(status: invoice.status)
            }
            Text(invoice.invoice_date ?? "").font(.caption).foregroundColor(.secondary)
            HStack {
                Text("Total: $\(String(format: "%.2f", invoice.total_amount))")
                    .font(.caption)
                Spacer()
                Text("Due: $\(String(format: "%.2f", invoice.balance_due))")
                    .font(.caption)
                    .foregroundColor(invoice.balance_due > 0 ? .orange : .green)
            }
            if invoice.balance_due > 0 {
                HStack(spacing: 8) {
                    Button("Pay", action: onPay)
                        .buttonStyle(.borderedProminent)
                        .controlSize(.small)
                        .tint(.teal)
                    Button("File Claim", action: onClaim)
                        .buttonStyle(.bordered)
                        .controlSize(.small)
                        .tint(.blue)
                }
            }
        }
        .padding(.vertical, 4)
    }
}

struct PaymentSheet: View {
    let invoice: Invoice
    let onDismiss: () -> Void

    @State private var amount: String = ""
    @State private var method: String = "Credit Card"
    @State private var isProcessing = false
    @State private var errorMessage: String?

    private let methods = ["Credit Card", "Debit Card", "Cash", "Check",
                          "Bank Transfer", "Insurance", "HSA/FSA"]

    var body: some View {
        NavigationStack {
            Form {
                Section("Invoice") {
                    LabeledContent("Number", value: invoice.invoice_number)
                    LabeledContent("Balance Due",
                                   value: String(format: "$%.2f", invoice.balance_due))
                }
                Section("Payment Details") {
                    TextField("Amount", text: $amount)
                        .keyboardType(.decimalPad)
                    Picker("Method", selection: $method) {
                        ForEach(methods, id: \.self) { Text($0) }
                    }
                }
                if let msg = errorMessage {
                    Text(msg).foregroundColor(.red).font(.caption)
                }
            }
            .navigationTitle("Record Payment")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel", action: onDismiss)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Submit") { Task { await submit() } }
                        .disabled(isProcessing || amount.isEmpty)
                }
            }
            .onAppear { amount = String(format: "%.2f", invoice.balance_due) }
        }
    }

    private func submit() async {
        guard let amt = Double(amount) else {
            errorMessage = "Invalid amount"
            return
        }
        isProcessing = true
        do {
            let req = PaymentRequest(amount: amt, payment_method: method)
            let _: MessageResponse = try await APIClient.shared.request(
                "patient/billing/invoices/\(invoice.id)/pay",
                method: "POST", body: req)
            onDismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
        isProcessing = false
    }
}

struct InsuranceClaimSheet: View {
    let invoice: Invoice
    let onDismiss: () -> Void

    @State private var insurances: [[String: AnyCodable]] = []
    @State private var selectedInsuranceId: Int?
    @State private var notes: String = ""
    @State private var isProcessing = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            Form {
                Section("Invoice") {
                    LabeledContent("Number", value: invoice.invoice_number)
                    LabeledContent("Balance",
                                   value: String(format: "$%.2f", invoice.balance_due))
                }
                Section("Insurance") {
                    if insurances.isEmpty {
                        Text("No insurance records on file").foregroundColor(.secondary)
                    } else {
                        Picker("Provider", selection: $selectedInsuranceId) {
                            Text("Select...").tag(nil as Int?)
                            ForEach(insurances.indices, id: \.self) { idx in
                                let ins = insurances[idx]
                                let name = (ins["provider_name"]?.value as? String) ?? "Provider"
                                let id = (ins["id"]?.value as? Int) ?? 0
                                Text(name).tag(id as Int?)
                            }
                        }
                    }
                }
                Section("Notes") {
                    TextField("Optional notes", text: $notes, axis: .vertical)
                        .lineLimit(3...6)
                }
                if let msg = errorMessage {
                    Text(msg).foregroundColor(.red).font(.caption)
                }
            }
            .navigationTitle("File Insurance Claim")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel", action: onDismiss)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Submit") { Task { await submit() } }
                        .disabled(isProcessing || selectedInsuranceId == nil)
                }
            }
            .task { await loadInsurance() }
        }
    }

    private func loadInsurance() async {
        do {
            let profile: PatientProfile = try await APIClient.shared.request("patient/profile")
            insurances = profile.insurance
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func submit() async {
        guard let insId = selectedInsuranceId else { return }
        isProcessing = true
        do {
            let req = InsuranceClaimRequest(
                invoice_id: invoice.id, insurance_id: insId,
                notes: notes.isEmpty ? nil : notes)
            let _: MessageResponse = try await APIClient.shared.request(
                "patient/insurance/claims", method: "POST", body: req)
            onDismiss()
        } catch {
            errorMessage = error.localizedDescription
        }
        isProcessing = false
    }
}
