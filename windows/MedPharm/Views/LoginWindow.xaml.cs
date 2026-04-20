/*
 * MedPharm ERP - Windows Desktop Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

using System;
using System.Net.Http;
using System.Threading.Tasks;
using System.Windows;
using MedPharm.Models;
using MedPharm.Services;

namespace MedPharm.Views;

public partial class LoginWindow : Window
{
    public LoginWindow()
    {
        InitializeComponent();
        ServerUrlBox.Text = App.Settings.ApiBaseUrl;
    }

    private void ResetServerButton_Click(object sender, RoutedEventArgs e)
    {
        ServerUrlBox.Text = AppSettings.DefaultApiBaseUrl;
    }

    private async void LoginButton_Click(object sender, RoutedEventArgs e)
    {
        var username = UsernameBox.Text.Trim();
        var password = PasswordBox.Password;
        var serverUrl = ServerUrlBox.Text.Trim();

        if (string.IsNullOrEmpty(username) || string.IsNullOrEmpty(password))
        {
            StatusText.Text = "Please enter username and password";
            return;
        }

        if (string.IsNullOrEmpty(serverUrl))
        {
            StatusText.Text = "Please enter a server URL";
            return;
        }

        App.SaveSettings(new AppSettings { ApiBaseUrl = serverUrl });

        LoginButton.IsEnabled = false;
        StatusText.Text = "Logging in...";
        StatusText.Foreground = System.Windows.Media.Brushes.Gray;

        try
        {
            var isStaff = LoginTypeCombo.SelectedIndex == 1;
            var endpoint = isStaff ? "auth/login/staff" : "auth/login/patient";

            var response = await App.Api.PostAsync<LoginResponse>(endpoint, new
            {
                username,
                password
            });

            App.Tokens.Save(new TokenData
            {
                AccessToken = response.AccessToken,
                RefreshToken = response.RefreshToken,
                UserId = response.User.Id,
                Username = response.User.Username,
                UserType = response.User.Type,
                Role = response.User.Role,
                PatientId = response.User.PatientId,
                FullName = response.User.Name
            });

            App.Api.SetToken(response.AccessToken);

            var main = new MainWindow();
            main.Show();
            Close();
        }
        catch (ApiException ex)
        {
            ShowError(ex.Message);
        }
        catch (HttpRequestException ex)
        {
            ShowError($"Cannot reach server at {serverUrl}.\n{ex.Message}");
        }
        catch (TaskCanceledException)
        {
            ShowError("Request timed out. Check the Server URL and try again.");
        }
        catch (UriFormatException)
        {
            ShowError("Server URL is not a valid URI.");
        }
        catch (Exception ex)
        {
            ShowError($"Unexpected error: {ex.Message}");
        }
        finally
        {
            LoginButton.IsEnabled = true;
        }
    }

    private void ShowError(string message)
    {
        StatusText.Foreground = (System.Windows.Media.Brush)Application.Current.Resources["ErrorBrush"];
        StatusText.Text = message;
    }

    private void RegisterButton_Click(object sender, RoutedEventArgs e)
    {
        var register = new RegisterWindow();
        register.ShowDialog();
    }
}
