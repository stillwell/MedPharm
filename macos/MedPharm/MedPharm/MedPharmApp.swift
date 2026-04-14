/*
 * MedPharm ERP - macOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * License: GNU General Public License v3.0
 */

import SwiftUI

@main
struct MedPharmApp: App {
    @StateObject private var authManager = AuthManager()

    var body: some Scene {
        WindowGroup {
            Group {
                if authManager.isAuthenticated {
                    MainView()
                        .environmentObject(authManager)
                        .frame(minWidth: 1100, minHeight: 720)
                } else {
                    LoginView()
                        .environmentObject(authManager)
                        .frame(width: 480, height: 600)
                }
            }
        }
        .windowStyle(.titleBar)
        .commands {
            CommandGroup(replacing: .appInfo) {
                Button("About MedPharm ERP") {
                    NSApplication.shared.orderFrontStandardAboutPanel(options: [
                        .applicationName: "MedPharm ERP",
                        .applicationVersion: "1.1.0",
                        .credits: NSAttributedString(string: "Copyright © 2026 Enlightec Ltd.")
                    ])
                }
            }
        }
    }
}
