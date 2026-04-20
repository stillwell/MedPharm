/*
 * MedPharm ERP - Windows Desktop Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

using System.Windows;
using System.Windows.Controls;
using MedPharm.Models;
using MedPharm.Services;

namespace MedPharm.Views.Pages;

public partial class BillingPage : UserControl
{
    public BillingPage()
    {
        InitializeComponent();
        Loaded += async (_, _) => await Load();
    }

    private async System.Threading.Tasks.Task Load()
    {
        try
        {
            var data = await App.Api.GetAsync<BillingData>("patient/billing");
            BalanceText.Text = $"${data.OutstandingBalance:F2}";
            InvoicesGrid.ItemsSource = data.Invoices;
            PaymentsGrid.ItemsSource = data.Payments;
        }
        catch (System.Exception) { }
    }

    private async void PayButton_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button btn && btn.Tag is Invoice invoice)
        {
            var dialog = new PaymentDialog(invoice) { Owner = Window.GetWindow(this) };
            if (dialog.ShowDialog() == true)
            {
                await Load();
            }
        }
    }

    private async void ClaimButton_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button btn && btn.Tag is Invoice invoice)
        {
            var dialog = new InsuranceClaimDialog(invoice) { Owner = Window.GetWindow(this) };
            if (dialog.ShowDialog() == true)
            {
                await Load();
            }
        }
    }
}
