/*
 * MedPharm ERP - Windows Desktop Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

using System.Windows;
using System.Windows.Controls;
using MedPharm.Views.Pages;

namespace MedPharm.Views;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        var tokens = App.Tokens.Load();
        if (tokens != null)
        {
            UserNameText.Text = $"Welcome,\n{tokens.FullName}";
        }
        ContentArea.Content = new DashboardPage();
    }

    private void Nav_Click(object sender, RoutedEventArgs e)
    {
        if (sender is not Button btn) return;
        ContentArea.Content = btn.Tag switch
        {
            "dashboard" => new DashboardPage(),
            "prescriptions" => new PrescriptionsPage(),
            "billing" => new BillingPage(),
            "appointments" => new AppointmentsPage(),
            "insurance" => new InsuranceClaimsPage(),
            "messages" => new MessagesPage(),
            _ => ContentArea.Content
        };
    }

    private void LogoutBtn_Click(object sender, RoutedEventArgs e)
    {
        App.Tokens.Clear();
        App.Api.ClearToken();
        var login = new LoginWindow();
        login.Show();
        Close();
    }
}
