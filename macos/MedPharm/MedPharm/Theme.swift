/*
 * MedPharm ERP - macOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 *
 * Shared design system — colors, gradients, modifiers.
 */

import SwiftUI

enum MPColor {
    static let bg             = Color(red: 0.027, green: 0.043, blue: 0.078)
    static let bgElevated     = Color(red: 0.043, green: 0.071, blue: 0.125)
    static let surface        = Color(red: 0.071, green: 0.102, blue: 0.169)
    static let surface2       = Color(red: 0.094, green: 0.129, blue: 0.212)
    static let border         = Color(red: 0.165, green: 0.227, blue: 0.353)

    static let primary        = Color(red: 0.000, green: 0.898, blue: 0.816)
    static let primaryAlt     = Color(red: 0.094, green: 0.718, blue: 1.000)
    static let accent         = Color(red: 1.000, green: 0.239, blue: 0.545)
    static let violet         = Color(red: 0.694, green: 0.294, blue: 1.000)
    static let gold           = Color(red: 1.000, green: 0.722, blue: 0.000)

    static let success        = Color(red: 0.000, green: 0.851, blue: 0.494)
    static let warning        = Color(red: 1.000, green: 0.624, blue: 0.263)
    static let danger         = Color(red: 1.000, green: 0.278, blue: 0.341)
    static let info           = Color(red: 0.188, green: 0.757, blue: 1.000)

    static let text           = Color(red: 0.914, green: 0.933, blue: 0.969)
    static let textMuted      = Color(red: 0.525, green: 0.584, blue: 0.690)
    static let textDim        = Color(red: 0.353, green: 0.404, blue: 0.510)
}

enum MPGradient {
    static let primary = LinearGradient(
        colors: [MPColor.primary, MPColor.primaryAlt, MPColor.violet],
        startPoint: .topLeading, endPoint: .bottomTrailing
    )
    static let accent = LinearGradient(
        colors: [MPColor.accent, MPColor.violet],
        startPoint: .topLeading, endPoint: .bottomTrailing
    )
    static let success = LinearGradient(
        colors: [MPColor.success, MPColor.primary],
        startPoint: .topLeading, endPoint: .bottomTrailing
    )
    static let danger = LinearGradient(
        colors: [MPColor.danger, MPColor.accent],
        startPoint: .topLeading, endPoint: .bottomTrailing
    )
    static let surface = LinearGradient(
        colors: [MPColor.surface2.opacity(0.85), MPColor.bgElevated.opacity(0.92)],
        startPoint: .topLeading, endPoint: .bottomTrailing
    )
    static let hero = LinearGradient(
        stops: [
            .init(color: Color(red: 0.039, green: 0.063, blue: 0.157), location: 0.0),
            .init(color: Color(red: 0.118, green: 0.051, blue: 0.212), location: 0.5),
            .init(color: Color(red: 0.071, green: 0.039, blue: 0.157), location: 1.0)
        ],
        startPoint: .topLeading, endPoint: .bottomTrailing
    )
}

struct MPBackground: View {
    var body: some View {
        ZStack {
            MPColor.bg.ignoresSafeArea()
            RadialGradient(colors: [MPColor.primaryAlt.opacity(0.14), .clear],
                           center: .topLeading, startRadius: 10, endRadius: 700)
                .ignoresSafeArea().blendMode(.plusLighter)
            RadialGradient(colors: [MPColor.accent.opacity(0.10), .clear],
                           center: .topTrailing, startRadius: 10, endRadius: 700)
                .ignoresSafeArea().blendMode(.plusLighter)
            RadialGradient(colors: [MPColor.violet.opacity(0.18), .clear],
                           center: UnitPoint(x: 0.2, y: 0.9), startRadius: 10, endRadius: 700)
                .ignoresSafeArea().blendMode(.plusLighter)
        }
    }
}

struct MPCardStyle: ViewModifier {
    var padding: CGFloat = 20
    func body(content: Content) -> some View {
        content
            .padding(padding)
            .background(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .fill(MPGradient.surface)
                    .overlay(
                        RoundedRectangle(cornerRadius: 18, style: .continuous)
                            .stroke(MPColor.border.opacity(0.9), lineWidth: 1)
                    )
                    .shadow(color: .black.opacity(0.5), radius: 20, x: 0, y: 12)
            )
    }
}
extension View { func mpCard(padding: CGFloat = 20) -> some View { modifier(MPCardStyle(padding: padding)) } }

struct MPPrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 15, weight: .bold))
            .foregroundColor(Color(red: 0.024, green: 0.067, blue: 0.110))
            .padding(.horizontal, 22).padding(.vertical, 12)
            .frame(maxWidth: .infinity, minHeight: 42)
            .background(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(MPGradient.primary)
                    .overlay(
                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                            .strokeBorder(Color.white.opacity(0.15), lineWidth: 1)
                    )
                    .shadow(color: MPColor.primary.opacity(0.4), radius: 18, x: 0, y: 8)
            )
            .scaleEffect(configuration.isPressed ? 0.99 : 1.0)
            .opacity(configuration.isPressed ? 0.9 : 1.0)
            .animation(.easeOut(duration: 0.12), value: configuration.isPressed)
    }
}
