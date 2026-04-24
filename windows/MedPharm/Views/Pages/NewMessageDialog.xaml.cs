/*
 * MedPharm ERP - Windows Desktop Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

using System;
using System.Windows;
using MedPharm.Models;

namespace MedPharm.Views.Pages;

public partial class NewMessageDialog : Window
{
    public int? NewThreadId { get; private set; }

    public NewMessageDialog()
    {
        InitializeComponent();
        Loaded += async (_, _) => await LoadProviders();
    }

    private async System.Threading.Tasks.Task LoadProviders()
    {
        try
        {
            var resp = await App.Api.GetAsync<ProvidersResponse>(
                "patient/messages/providers");
            var any = new ProviderSummary { Id = 0, DisplayTitle = "Any available clinician" };
            var items = new System.Collections.Generic.List<ProviderSummary> { any };
            items.AddRange(resp.Providers);
            ProviderCombo.ItemsSource = items;
            ProviderCombo.SelectedIndex = 0;
        }
        catch
        {
            // Non-fatal — server-side will accept a null provider.
        }
    }

    private async void SendBtn_Click(object sender, RoutedEventArgs e)
    {
        var subject = SubjectInput.Text?.Trim() ?? "";
        var body = BodyInput.Text?.Trim() ?? "";
        if (string.IsNullOrEmpty(subject) || string.IsNullOrEmpty(body))
        {
            MessageBox.Show("Subject and message are required.", "New Message",
                MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }
        var selected = ProviderCombo.SelectedItem as ProviderSummary;
        int? providerId = (selected == null || selected.Id == 0) ? null : selected.Id;

        SendBtn.IsEnabled = false;
        try
        {
            var resp = await App.Api.PostAsync<NewThreadResponse>("patient/messages",
                new { subject, body, provider_id = providerId });
            NewThreadId = resp.ThreadId;
            DialogResult = true;
            Close();
        }
        catch (Exception ex)
        {
            MessageBox.Show(ex.Message, "Send failed",
                MessageBoxButton.OK, MessageBoxImage.Warning);
            SendBtn.IsEnabled = true;
        }
    }

    private void CancelBtn_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}
