# MedPharm — Windows Desktop Client

WPF patient portal on **.NET 8**, targeting Windows 10 1809+ and Windows 11.

Build instructions: [`docs/COMPILATION.md § Windows`](../docs/COMPILATION.md#windows-net-8--wpf).
Feature inventory: [`docs/CLIENTS.md § Windows Desktop`](../docs/CLIENTS.md#windows-desktop).

---

## Tech stack

| Layer | Technology |
|-------|------------|
| UI | WPF + XAML data templates |
| Architecture | MVVM via `CommunityToolkit.Mvvm` |
| Networking | `HttpClient` + `Newtonsoft.Json` |
| Secure storage | DPAPI (`System.Security.Cryptography.ProtectedData`) |
| Runtime | .NET 8 Desktop |

---

## Project layout

```
windows/MedPharm/
├── App.xaml / App.xaml.cs
├── MedPharm.csproj
├── Models/           # API data contracts
├── Services/
│   ├── ApiClient.cs      # HttpClient wrapper
│   └── TokenStore.cs     # DPAPI token encryption
└── Views/            # XAML pages + dialogs
```

---

## Build & run

```powershell
dotnet restore
dotnet run
```

### Release (self-contained single file)

```powershell
dotnet publish MedPharm.csproj `
  -c Release -r win-x64 --self-contained true `
  -p:PublishSingleFile=true `
  -p:IncludeNativeLibrariesForSelfExtract=true `
  -o publish\win-x64
```

### ARM64

```powershell
dotnet publish -c Release -r win-arm64 --self-contained true -o publish\win-arm64
```

---

## Configure API host

Two options:

1. **Environment variable** (preferred):

   ```powershell
   setx MEDPHARM_API "https://api.example.com/api/v1"
   ```

   `ApiClient.cs` reads `MEDPHARM_API` on startup and falls back to the compiled default.

2. **In-app settings dialog** — stored encrypted via DPAPI alongside the auth tokens.

---

## Token security

`TokenStore.cs` uses `ProtectedData.Protect(..., DataProtectionScope.CurrentUser)`. Tokens are readable only by the Windows user account that saved them.

---

## Packaging (MSI / MSIX)

The project ships a self-contained `.exe` by default. For an MSI installer, integrate with **WiX Toolset v4**; for an MSIX package, use the **MSIX Packaging Tool** or Visual Studio Windows Application Packaging Project.
