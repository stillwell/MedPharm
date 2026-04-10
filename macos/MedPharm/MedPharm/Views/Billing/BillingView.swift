/*
 * MedPharm ERP - macOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

import SwiftUI

struct BillingView: View {
    @State private var billing: BillingData?
    @State private var isLoading = true
    @State private var selectedInvoice: Invoice?
    @State private var showPay = false
    @State private var showClaim = false

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Billing & Payments").font(.largeTitle).bold()
                Spacer()
                if let billing = billing {
                    VStack(alignment: .trailing) {
                        Text("Outstanding Balance").font(.caption).foregroundColor(.secondary)
                        Text(String(format: "$%.2f", billing.outstanding_balance))
                            .font(.title2).bold()
                            .foregroundColor(billing.outstanding_balance > 0 ? .orange : .green)
                    }
                }
            }

            if isLoading {
                ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let billing = billing {
                SectionBox(title: "Invoices") {
                    Table(billing.invoices) {
                        TableColumn("Invoice #", value: \.invoice_number)
                        TableColumn("Date") { Text($0.invoice_date ?? "") }
                        TableColumn("Total") { Text(String(format: "$%.2f", $0.total_amount)) }
                        TableColumn("Balance") {
                            Text(String(format: "$%.2f", $0.balance_due))
                                .foregroundColor($0.balance_due > 0 ? .orange : .green)
                        }
                        TableColumn("Status", value: \.status)
                        TableColumn("Actions") { invoice in
                            HStack(spacing: 6) {
                                if invoice.balance_due > 0 {
                                    Button("Pay") {
                                        selectedInvoice = invoice
                                        showPay = true
                                    }.controlSize(.small)
                                    Button("Claim") {
                                        selectedInvoice = invoice
                                        showClaim = true
                                    }.controlSize(.small)
                                }
                            }
                        }
                    }
                    .frame(minHeight: 200)
                }

                SectionBox(title: "Payment History") {
                    Table(billing.payments) {
                        TableColumn("Date") { Text($0.payment_date ?? "") }
                        TableColumn("Method", value: \.payment_method)
                        TableColumn("Amount") { Text(String(format: "$%.2f", $0.amount)) }
                        TableColumn("Status", value: \.status)
                    }
                    .frame(minHeight: 150)
                }
            }
        }
        .padding(24)
        .task { await load() }
        .sheet(isPresented: $showPay) {
            if let invoice = selectedInvoice {
                PaymentSheet(invoice: invoice) {
                    showPay = false
                    Task { await load() }
                }
            }
        }
        .sheet(isPresented: $showClaim) {
            if let invoice = selectedInvoice {
                InsuranceClaimSheet(invoice: invoice) {
                    showClaim = false
                    Task { await load() }
                }
            }
        }
    }

    private func load() async {
        isLoading = true
        do {
            billing = try await APIClient.shared.request("patient/billing")
        } catch { }
        isLoading = false
    }
}

struct PaymentSheet: View {
    let invoice: Invoice
    let onDismiss: () -> Void

    @State private var amount: String = ""
    @State private var method: String = "Credit Card"
    @State private var errorMsg: String?
    @State private var isProcessing = false

    private let methods = ["Credit Card", "Debit Card", "Cash", "Check",
                          "Bank Transfer", "Insurance", "HSA/FSA"]

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Record Payment").font(.title2).bold()

            Grid(alignment: .leading, horizontalSpacing: 12, verticalSpacing: 10) {
                GridRow {
                    Text("Invoice:").foregroundColor(.secondary)
                    Text(invoice.invoice_number).bold()
                }
                GridRow {
                    Text("Balance:").foregroundColor(.secondary)
                    Text(String(format: "$%.2f", invoice.balance_due)).bold()
                }
                GridRow {
                    Text("Amount:").foregroundColor(.secondary)
                    TextField("0.00", text: $amount)
                        .textFieldStyle(.roundedBorder)
                }
                GridRow {
                    Text("Method:").foregroundColor(.secondary)
                    Picker("", selection: $method) {
                        ForEach(methods, id: \.self) { Text($0) }
                    }
                }
            }

            if let msg = errorMsg {
                Text(msg).foregroundColor(.red).font(.caption)
            }

            HStack {
                Spacer()
                Button("Cancel", action: onDismiss)
                Button("Submit") { Task { await submit() } }
                    .buttonStyle(.borderedProminent)
                    .tint(.teal)
                    .disabled(isProcessing)
            }
        }
        .padding(24)
        .frame(width: 400)
        .onAppear { amount = String(format: "%.2f", invoice.balance_due) }
    }

    private func submit() async {
        guard let amt = Double(amount) else {
            errorMsg = "Invalid amount"
            return
        }
        isProcessing = true
        do {
            let req = PaymentRequest(amount: amt, payment_method: method)
            let _: MessageResponse = try await APIClient.shared.request(
                "patient/billing/invoices/\(invoice.id)/pay", method: "POST", body: req)
            onDismiss()
        } catch {
            errorMsg = error.localizedDescription
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
    @State private var errorMsg: String?
    @State private var isProcessing = false

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("File Insurance Claim").font(.title2).bold()

            Grid(alignment: .leading, horizontalSpacing: 12, verticalSpacing: 10) {
                GridRow {
                    Text("Invoice:").foregroundColor(.secondary)
                    Text(invoice.invoice_number).bold()
                }
                GridRow {
                    Text("Amount:").foregroundColor(.secondary)
                    Text(String(format: "$%.2f", invoice.balance_due)).bold()
                }
                GridRow {
                    Text("Provider:").foregroundColor(.secondary)
                    Picker("", selection: $selectedInsuranceId) {
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

            VStack(alignment: .leading, spacing: 4) {
                Text("Notes:").foregroundColor(.secondary)
                TextEditor(text: $notes).frame(height: 80).border(Color.gray.opacity(0.3))
            }

            if let msg = errorMsg {
                Text(msg).foregroundColor(.red).font(.caption)
            }

            HStack {
                Spacer()
                Button("Cancel", action: onDismiss)
                Button("Submit") { Task { await submit() } }
                    .buttonStyle(.borderedProminent)
                    .tint(.teal)
                    .disabled(isProcessing || selectedInsuranceId == nil)
            }
        }
        .padding(24)
        .frame(width: 440)
        .task { await loadInsurance() }
    }

    private func loadInsurance() async {
        do {
            let profile: PatientProfile = try await APIClient.shared.request("patient/profile")
            insurances = profile.insurance
        } catch { errorMsg = error.localizedDescription }
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
        } catch { errorMsg = error.localizedDescription }
        isProcessing = false
    }
}

struct InsuranceClaimsView: View {
    @State private var claims: [InsuranceClaim] = []
    @State private var isLoading = true

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Insurance Claims").font(.largeTitle).bold()

            if isLoading {
                ProgressView()
            } else if claims.isEmpty {
                Text("No claims on file").foregroundColor(.secondary)
            } else {
                Table(claims) {
                    TableColumn("Claim #", value: \.claim_number)
                    TableColumn("Provider") { Text($0.insurance_provider ?? "") }
                    TableColumn("Claimed") { Text(String(format: "$%.2f", $0.claimed_amount)) }
                    TableColumn("Approved") {
                        Text($0.approved_amount.map { String(format: "$%.2f", $0) } ?? "—")
                    }
                    TableColumn("Status", value: \.status)
                    TableColumn("Submitted") { Text($0.submitted_date ?? "") }
                }
            }
        }
        .padding(24)
        .task { await load() }
    }

    private func load() async {
        isLoading = true
        do {
            let resp: InsuranceClaimsResponse = try await APIClient.shared.request(
                "patient/insurance/claims")
            claims = resp.claims
        } catch { }
        isLoading = false
    }
}
