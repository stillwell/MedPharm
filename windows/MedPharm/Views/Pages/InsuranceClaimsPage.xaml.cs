/*
 * MedPharm ERP - Windows Desktop Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

using System.Collections.Generic;
using System.Windows.Controls;
using Newtonsoft.Json.Linq;
using MedPharm.Services;

namespace MedPharm.Views.Pages;

public class InsuranceClaimRow
{
    public int Id { get; set; }
    public string ClaimNumber { get; set; } = "";
    public int InvoiceId { get; set; }
    public string? InsuranceProvider { get; set; }
    public string Status { get; set; } = "";
    public string? SubmittedDate { get; set; }
    public double ClaimedAmount { get; set; }
    public double? ApprovedAmount { get; set; }
}

public partial class InsuranceClaimsPage : UserControl
{
    public InsuranceClaimsPage()
    {
        InitializeComponent();
        Loaded += async (_, _) => await Load();
    }

    private async System.Threading.Tasks.Task Load()
    {
        try
        {
            var resp = await App.Api.GetAsync<JObject>("patient/insurance/claims");
            var list = new List<InsuranceClaimRow>();
            if (resp["claims"] is JArray claims)
            {
                foreach (var c in claims)
                {
                    list.Add(new InsuranceClaimRow
                    {
                        Id = c["id"]?.Value<int>() ?? 0,
                        ClaimNumber = c["claim_number"]?.Value<string>() ?? "",
                        InvoiceId = c["invoice_id"]?.Value<int>() ?? 0,
                        InsuranceProvider = c["insurance_provider"]?.Value<string>(),
                        Status = c["status"]?.Value<string>() ?? "",
                        SubmittedDate = c["submitted_date"]?.Value<string>(),
                        ClaimedAmount = c["claimed_amount"]?.Value<double>() ?? 0,
                        ApprovedAmount = c["approved_amount"]?.Value<double?>()
                    });
                }
            }
            ClaimsGrid.ItemsSource = list;
        }
        catch { }
    }
}
