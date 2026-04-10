/*
 * MedPharm ERP - Windows Desktop Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

using System.Windows.Controls;
using MedPharm.Models;
using MedPharm.Services;

namespace MedPharm.Views.Pages;

public partial class PrescriptionsPage : UserControl
{
    public PrescriptionsPage()
    {
        InitializeComponent();
        Loaded += async (_, _) => await Load();
    }

    private async System.Threading.Tasks.Task Load()
    {
        try
        {
            var filterItem = FilterCombo.SelectedItem as ComboBoxItem;
            var tag = filterItem?.Tag as string ?? "";
            var endpoint = string.IsNullOrEmpty(tag)
                ? "patient/prescriptions"
                : $"patient/prescriptions?status={tag}";
            var resp = await App.Api.GetAsync<PrescriptionListResponse>(endpoint);
            RxGrid.ItemsSource = resp.Prescriptions;
        }
        catch (ApiException) { }
    }

    private async void FilterCombo_Changed(object sender, SelectionChangedEventArgs e)
    {
        if (IsLoaded) await Load();
    }
}
