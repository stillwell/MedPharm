/*
 * MedPharm ERP - Windows Desktop Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

using System.Windows;
using MedPharm.Services;

namespace MedPharm;

public partial class App : Application
{
    public static ApiClient Api { get; } = new ApiClient();
    public static TokenStore Tokens { get; } = new TokenStore();

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        Api.LoadTokens();
    }
}
