/*
 * MedPharm ERP - Windows Desktop Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

using System.Collections.Generic;
using System.Windows;
using Newtonsoft.Json.Linq;
using MedPharm.Models;
using MedPharm.Services;

namespace MedPharm.Views.Pages;

public class InsuranceEntry
{
    public int Id { get; set; }
    public string ProviderName { get; set; } = "";
}

public partial class InsuranceClaimDialog : Window
{
    private readonly Invoice _invoice;

    public InsuranceClaimDialog(Invoice invoice)
    {
        InitializeComponent();
        _invoice = invoice;
        InvoiceText.Text = invoice.InvoiceNumber;
        BalanceText.Text = $"${invoice.BalanceDue:F2}";
        Loaded += async (_, _) => await LoadInsurance();
    }

    private async System.Threading.Tasks.Task LoadInsurance()
    {
        try
        {
            var profile = await App.Api.GetAsync<JObject>("patient/profile");
            var insurances = new List<InsuranceEntry>();
            var insArray = profile["insurance"] as JArray;
            if (insArray != null)
            {
                foreach (var ins in insArray)
                {
                    insurances.Add(new InsuranceEntry
                    {
                        Id = ins["id"]?.Value<int>() ?? 0,
                        ProviderName = ins["provider_name"]?.Value<string>() ?? "Unknown"
                    });
                }
            }
            InsuranceCombo.ItemsSource = insurances;
            if (insurances.Count > 0) InsuranceCombo.SelectedIndex = 0;
            else StatusText.Text = "No insurance records on file";
        }
        catch (ApiException ex)
        {
            StatusText.Text = ex.Message;
        }
    }

    private async void Submit_Click(object sender, RoutedEventArgs e)
    {
        if (InsuranceCombo.SelectedItem is not InsuranceEntry entry)
        {
            StatusText.Text = "Please select an insurance provider";
            return;
        }

        SubmitBtn.IsEnabled = false;
        try
        {
            await App.Api.PostAsync<MessageResponse>("patient/insurance/claims", new
            {
                invoice_id = _invoice.Id,
                insurance_id = entry.Id,
                notes = NotesBox.Text
            });
            DialogResult = true;
            Close();
        }
        catch (ApiException ex)
        {
            StatusText.Text = ex.Message;
            SubmitBtn.IsEnabled = true;
        }
    }

    private void Cancel_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}
