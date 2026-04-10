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

public partial class PaymentDialog : Window
{
    private readonly Invoice _invoice;

    public PaymentDialog(Invoice invoice)
    {
        InitializeComponent();
        _invoice = invoice;
        InvoiceText.Text = invoice.InvoiceNumber;
        BalanceText.Text = $"${invoice.BalanceDue:F2}";
        AmountBox.Text = invoice.BalanceDue.ToString("F2");
    }

    private async void Submit_Click(object sender, RoutedEventArgs e)
    {
        if (!double.TryParse(AmountBox.Text, out var amount) || amount <= 0)
        {
            StatusText.Text = "Invalid amount";
            return;
        }

        var method = ((ComboBoxItem)MethodCombo.SelectedItem).Content.ToString();
        SubmitBtn.IsEnabled = false;

        try
        {
            await App.Api.PostAsync<MessageResponse>(
                $"patient/billing/invoices/{_invoice.Id}/pay",
                new { amount, payment_method = method });
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
