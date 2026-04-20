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

public partial class DashboardPage : UserControl
{
    public DashboardPage()
    {
        InitializeComponent();
        Loaded += async (_, _) => await LoadData();
    }

    private async System.Threading.Tasks.Task LoadData()
    {
        try
        {
            var data = await App.Api.GetAsync<DashboardData>("patient/dashboard");
            ActiveRxText.Text = data.ActivePrescriptions.ToString();
            AppointmentsText.Text = data.UpcomingAppointments.ToString();
            BalanceText.Text = $"${data.OutstandingBalance:F2}";
            RecentRxList.ItemsSource = data.RecentPrescriptions;
            UpcomingList.ItemsSource = data.NextAppointments;
        }
        catch (System.Exception)
        {
            // Dashboard fetch failures are non-fatal; surface nothing.
        }
    }
}
