/*
 * MedPharm ERP - Windows Desktop Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using Newtonsoft.Json;

namespace MedPharm.Services;

public class TokenData
{
    public string AccessToken { get; set; } = "";
    public string RefreshToken { get; set; } = "";
    public int UserId { get; set; }
    public string Username { get; set; } = "";
    public string UserType { get; set; } = "";
    public string? Role { get; set; }
    public int? PatientId { get; set; }
    public string FullName { get; set; } = "";
}

public class TokenStore
{
    private readonly string _path;

    public TokenStore()
    {
        var folder = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "MedPharm");
        Directory.CreateDirectory(folder);
        _path = Path.Combine(folder, "session.dat");
    }

    public void Save(TokenData data)
    {
        var json = JsonConvert.SerializeObject(data);
        var bytes = Encoding.UTF8.GetBytes(json);
        var encrypted = ProtectedData.Protect(bytes, null, DataProtectionScope.CurrentUser);
        File.WriteAllBytes(_path, encrypted);
    }

    public TokenData? Load()
    {
        if (!File.Exists(_path)) return null;
        try
        {
            var encrypted = File.ReadAllBytes(_path);
            var bytes = ProtectedData.Unprotect(encrypted, null, DataProtectionScope.CurrentUser);
            var json = Encoding.UTF8.GetString(bytes);
            return JsonConvert.DeserializeObject<TokenData>(json);
        }
        catch
        {
            return null;
        }
    }

    public void Clear()
    {
        if (File.Exists(_path))
            File.Delete(_path);
    }
}
