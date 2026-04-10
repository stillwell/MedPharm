/*
 * MedPharm ERP - Windows Desktop Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

using System.Windows;
using MedPharm.Models;
using MedPharm.Services;

namespace MedPharm.Views;

public partial class RegisterWindow : Window
{
    public RegisterWindow()
    {
        InitializeComponent();
    }

    private async void Register_Click(object sender, RoutedEventArgs e)
    {
        RegisterBtn.IsEnabled = false;
        StatusText.Text = "Creating account...";
        StatusText.Foreground = System.Windows.Media.Brushes.Gray;

        try
        {
            var response = await App.Api.PostAsync<LoginResponse>("auth/patient/register", new
            {
                first_name = FirstNameBox.Text.Trim(),
                last_name = LastNameBox.Text.Trim(),
                dob = DobBox.Text.Trim(),
                ssn_last4 = SsnBox.Text.Trim(),
                username = UsernameBox.Text.Trim(),
                email = EmailBox.Text.Trim(),
                password = PasswordBox.Password
            });

            MessageBox.Show("Registration successful! You can now log in.",
                "Success", MessageBoxButton.OK, MessageBoxImage.Information);
            Close();
        }
        catch (ApiException ex)
        {
            StatusText.Foreground = (System.Windows.Media.Brush)Application.Current.Resources["ErrorBrush"];
            StatusText.Text = ex.Message;
        }
        finally
        {
            RegisterBtn.IsEnabled = true;
        }
    }

    private void Cancel_Click(object sender, RoutedEventArgs e)
    {
        Close();
    }
}
