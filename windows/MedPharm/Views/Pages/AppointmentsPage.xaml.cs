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

public partial class AppointmentsPage : UserControl
{
    public AppointmentsPage()
    {
        InitializeComponent();
        Loaded += async (_, _) => await Load();
    }

    private async System.Threading.Tasks.Task Load()
    {
        try
        {
            var resp = await App.Api.GetAsync<AppointmentsResponse>("patient/appointments");
            AppointmentsGrid.ItemsSource = resp.Appointments;
        }
        catch (ApiException) { }
    }
}
