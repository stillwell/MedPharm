/*
 * MedPharm ERP - Windows Desktop Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

using System.Collections.Generic;
using Newtonsoft.Json;

namespace MedPharm.Models;

public class LoginResponse
{
    [JsonProperty("access_token")] public string AccessToken { get; set; } = "";
    [JsonProperty("refresh_token")] public string RefreshToken { get; set; } = "";
    [JsonProperty("user")] public UserInfo User { get; set; } = new();
}

public class UserInfo
{
    [JsonProperty("id")] public int Id { get; set; }
    [JsonProperty("patient_id")] public int? PatientId { get; set; }
    [JsonProperty("username")] public string Username { get; set; } = "";
    [JsonProperty("name")] public string Name { get; set; } = "";
    [JsonProperty("type")] public string Type { get; set; } = "";
    [JsonProperty("role")] public string? Role { get; set; }
}

public class DashboardData
{
    [JsonProperty("active_prescriptions")] public int ActivePrescriptions { get; set; }
    [JsonProperty("upcoming_appointments")] public int UpcomingAppointments { get; set; }
    [JsonProperty("outstanding_balance")] public double OutstandingBalance { get; set; }
    [JsonProperty("recent_prescriptions")] public List<Prescription> RecentPrescriptions { get; set; } = new();
    [JsonProperty("next_appointments")] public List<Appointment> NextAppointments { get; set; } = new();
    [JsonProperty("recent_invoices")] public List<Invoice> RecentInvoices { get; set; } = new();
}

public class Prescription
{
    [JsonProperty("id")] public int Id { get; set; }
    [JsonProperty("rx_number")] public string RxNumber { get; set; } = "";
    [JsonProperty("status")] public string Status { get; set; } = "";
    [JsonProperty("prescriber_name")] public string? PrescriberName { get; set; }
    [JsonProperty("prescribed_date")] public string? PrescribedDate { get; set; }
    [JsonProperty("expiry_date")] public string? ExpiryDate { get; set; }
    [JsonProperty("notes")] public string? Notes { get; set; }
    [JsonProperty("items")] public List<PrescriptionItem>? Items { get; set; }
}

public class PrescriptionItem
{
    [JsonProperty("id")] public int Id { get; set; }
    [JsonProperty("medication_id")] public int MedicationId { get; set; }
    [JsonProperty("medication_name")] public string? MedicationName { get; set; }
    [JsonProperty("dosage")] public string Dosage { get; set; } = "";
    [JsonProperty("frequency")] public string Frequency { get; set; } = "";
    [JsonProperty("quantity")] public int Quantity { get; set; }
    [JsonProperty("refills_allowed")] public int RefillsAllowed { get; set; }
    [JsonProperty("refills_used")] public int RefillsUsed { get; set; }
    [JsonProperty("refills_remaining")] public int RefillsRemaining { get; set; }
    [JsonProperty("instructions")] public string? Instructions { get; set; }
}

public class PrescriptionListResponse
{
    [JsonProperty("prescriptions")] public List<Prescription> Prescriptions { get; set; } = new();
}

public class BillingData
{
    [JsonProperty("invoices")] public List<Invoice> Invoices { get; set; } = new();
    [JsonProperty("payments")] public List<Payment> Payments { get; set; } = new();
    [JsonProperty("outstanding_balance")] public double OutstandingBalance { get; set; }
}

public class Invoice
{
    [JsonProperty("id")] public int Id { get; set; }
    [JsonProperty("invoice_number")] public string InvoiceNumber { get; set; } = "";
    [JsonProperty("invoice_date")] public string? InvoiceDate { get; set; }
    [JsonProperty("due_date")] public string? DueDate { get; set; }
    [JsonProperty("total_amount")] public double TotalAmount { get; set; }
    [JsonProperty("amount_paid")] public double AmountPaid { get; set; }
    [JsonProperty("balance_due")] public double BalanceDue { get; set; }
    [JsonProperty("status")] public string Status { get; set; } = "";
}

public class Payment
{
    [JsonProperty("id")] public int Id { get; set; }
    [JsonProperty("invoice_id")] public int InvoiceId { get; set; }
    [JsonProperty("amount")] public double Amount { get; set; }
    [JsonProperty("payment_method")] public string PaymentMethod { get; set; } = "";
    [JsonProperty("payment_date")] public string? PaymentDate { get; set; }
    [JsonProperty("status")] public string Status { get; set; } = "";
}

public class Appointment
{
    [JsonProperty("id")] public int Id { get; set; }
    [JsonProperty("provider_name")] public string? ProviderName { get; set; }
    [JsonProperty("appointment_type")] public string? AppointmentType { get; set; }
    [JsonProperty("scheduled_datetime")] public string? ScheduledDatetime { get; set; }
    [JsonProperty("duration_minutes")] public int? DurationMinutes { get; set; }
    [JsonProperty("status")] public string Status { get; set; } = "";
    [JsonProperty("reason")] public string? Reason { get; set; }
}

public class AppointmentsResponse
{
    [JsonProperty("appointments")] public List<Appointment> Appointments { get; set; } = new();
}

public class MessageResponse
{
    [JsonProperty("message")] public string? Message { get; set; }
    [JsonProperty("error")] public string? Error { get; set; }
}

// ── Secure Messaging ───────────────────────────────────────────────────

public class MessageThread
{
    [JsonProperty("id")] public int Id { get; set; }
    [JsonProperty("patient_id")] public int PatientId { get; set; }
    [JsonProperty("patient_name")] public string? PatientName { get; set; }
    [JsonProperty("provider_id")] public int? ProviderId { get; set; }
    [JsonProperty("provider_name")] public string? ProviderName { get; set; }
    [JsonProperty("subject")] public string Subject { get; set; } = "";
    [JsonProperty("is_closed")] public bool IsClosed { get; set; }
    [JsonProperty("created_at")] public string? CreatedAt { get; set; }
    [JsonProperty("last_message_at")] public string? LastMessageAt { get; set; }
    [JsonProperty("message_count")] public int MessageCount { get; set; }
    [JsonProperty("unread_count")] public int UnreadCount { get; set; }

    public string Display =>
        (UnreadCount > 0 ? $"● ({UnreadCount}) " : "")
        + Subject
        + (IsClosed ? "  (closed)" : "");

    public string WithLine => $"With {ProviderName ?? "your care team"}";
}

public class MessageThreadsResponse
{
    [JsonProperty("threads")] public List<MessageThread> Threads { get; set; } = new();
}

public class SecureMessage
{
    [JsonProperty("id")] public int Id { get; set; }
    [JsonProperty("sender_type")] public string SenderType { get; set; } = "";
    [JsonProperty("sender_id")] public int SenderId { get; set; }
    [JsonProperty("body")] public string Body { get; set; } = "";
    [JsonProperty("sent_at")] public string? SentAt { get; set; }
    [JsonProperty("read_at")] public string? ReadAt { get; set; }

    public bool IsFromPatient => SenderType == "patient";
    public string SenderLabel => IsFromPatient ? "You" : "Care Team";
}

public class MessageThreadDetailResponse
{
    [JsonProperty("thread")] public MessageThread Thread { get; set; } = new();
    [JsonProperty("messages")] public List<SecureMessage> Messages { get; set; } = new();
}

public class ProviderSummary
{
    [JsonProperty("id")] public int Id { get; set; }
    [JsonProperty("full_name")] public string? FullName { get; set; }
    [JsonProperty("display_title")] public string? DisplayTitle { get; set; }
    [JsonProperty("role")] public string? Role { get; set; }
    [JsonProperty("specialization")] public string? Specialization { get; set; }

    public string DisplayLabel
    {
        get
        {
            var name = DisplayTitle ?? FullName ?? "Unknown";
            var suffix = !string.IsNullOrWhiteSpace(Specialization) ? $" — {Specialization}" : "";
            return name + suffix;
        }
    }
}

public class ProvidersResponse
{
    [JsonProperty("providers")] public List<ProviderSummary> Providers { get; set; } = new();
}

public class NewThreadResponse
{
    [JsonProperty("thread_id")] public int ThreadId { get; set; }
}
