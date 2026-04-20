/*
 * MedPharm ERP - Windows Desktop Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

using System.Windows;
using System.Windows.Threading;
using MedPharm.Services;

namespace MedPharm;

public partial class App : Application
{
    public static SettingsStore SettingsStore { get; } = new SettingsStore();
    public static AppSettings Settings { get; private set; } = SettingsStore.Load();
    public static ApiClient Api { get; } = new ApiClient();
    public static TokenStore Tokens { get; } = new TokenStore();

    public static void SaveSettings(AppSettings settings)
    {
        Settings = settings;
        SettingsStore.Save(settings);
        Api.BaseUrl = settings.ApiBaseUrl;
    }

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        Api.BaseUrl = Settings.ApiBaseUrl;
        Api.LoadTokens();
        DispatcherUnhandledException += OnDispatcherUnhandledException;
    }

    private void OnDispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs e)
    {
        MessageBox.Show(
            $"An unexpected error occurred:\n\n{e.Exception.Message}",
            "MedPharm ERP",
            MessageBoxButton.OK,
            MessageBoxImage.Error);
        e.Handled = true;
    }
}
