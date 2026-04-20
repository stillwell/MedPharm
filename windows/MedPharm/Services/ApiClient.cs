/*
 * MedPharm ERP - Windows Desktop Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

namespace MedPharm.Services;

public class ApiException : Exception
{
    public int StatusCode { get; }
    public ApiException(string message, int statusCode = 0) : base(message)
    {
        StatusCode = statusCode;
    }
}

public class ApiClient
{
    private readonly HttpClient _http;
    private string _baseUrl = AppSettings.DefaultApiBaseUrl;

    public string BaseUrl
    {
        get => _baseUrl;
        set => _baseUrl = string.IsNullOrWhiteSpace(value)
            ? AppSettings.DefaultApiBaseUrl
            : value.TrimEnd('/');
    }

    public ApiClient()
    {
        _http = new HttpClient
        {
            Timeout = TimeSpan.FromSeconds(30)
        };
    }

    public void LoadTokens()
    {
        var tokens = App.Tokens.Load();
        if (tokens != null && !string.IsNullOrEmpty(tokens.AccessToken))
        {
            _http.DefaultRequestHeaders.Authorization =
                new AuthenticationHeaderValue("Bearer", tokens.AccessToken);
        }
    }

    public void SetToken(string accessToken)
    {
        _http.DefaultRequestHeaders.Authorization =
            new AuthenticationHeaderValue("Bearer", accessToken);
    }

    public void ClearToken()
    {
        _http.DefaultRequestHeaders.Authorization = null;
    }

    public async Task<T> GetAsync<T>(string endpoint)
    {
        var response = await _http.GetAsync($"{BaseUrl}/{endpoint}");
        return await HandleResponse<T>(response);
    }

    public async Task<T> PostAsync<T>(string endpoint, object? body = null)
    {
        var content = body != null
            ? new StringContent(JsonConvert.SerializeObject(body), Encoding.UTF8, "application/json")
            : null;
        var response = await _http.PostAsync($"{BaseUrl}/{endpoint}", content);
        return await HandleResponse<T>(response);
    }

    public async Task<T> PutAsync<T>(string endpoint, object body)
    {
        var content = new StringContent(JsonConvert.SerializeObject(body), Encoding.UTF8, "application/json");
        var response = await _http.PutAsync($"{BaseUrl}/{endpoint}", content);
        return await HandleResponse<T>(response);
    }

    private async Task<T> HandleResponse<T>(HttpResponseMessage response)
    {
        var json = await response.Content.ReadAsStringAsync();

        if (response.IsSuccessStatusCode)
        {
            var result = JsonConvert.DeserializeObject<T>(json);
            return result ?? throw new ApiException("Invalid response");
        }

        if ((int)response.StatusCode == 401)
        {
            throw new ApiException("Session expired. Please log in again.", 401);
        }

        try
        {
            var error = JsonConvert.DeserializeObject<dynamic>(json);
            throw new ApiException((string?)error?.error ?? "Server error", (int)response.StatusCode);
        }
        catch (JsonException)
        {
            throw new ApiException($"Server error ({(int)response.StatusCode})", (int)response.StatusCode);
        }
    }
}
