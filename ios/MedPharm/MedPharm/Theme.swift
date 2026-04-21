/*
 * MedPharm ERP - iOS Application
 * Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
 * Author: Robert Andrew Stillwell
 * Email: Andrew.Stillwell@enlightec.com
 * License: GNU General Public License v3.0
 *
 * Shared design system — colors, gradients, modifiers.
 */

import SwiftUI

// MARK: - Palette

enum MPColor {
    static let bg             = Color(red: 0.027, green: 0.043, blue: 0.078)   // #070B14
    static let bgElevated     = Color(red: 0.043, green: 0.071, blue: 0.125)   // #0B1220
    static let surface        = Color(red: 0.071, green: 0.102, blue: 0.169)   // #121A2B
    static let surface2       = Color(red: 0.094, green: 0.129, blue: 0.212)   // #182136
    static let border         = Color(red: 0.165, green: 0.227, blue: 0.353)   // #2A3A5A

    static let primary        = Color(red: 0.000, green: 0.898, blue: 0.816)   // #00E5D0
    static let primaryAlt     = Color(red: 0.094, green: 0.718, blue: 1.000)   // #18B7FF
    static let accent         = Color(red: 1.000, green: 0.239, blue: 0.545)   // #FF3D8B
    static let violet         = Color(red: 0.694, green: 0.294, blue: 1.000)   // #B14BFF
    static let gold           = Color(red: 1.000, green: 0.722, blue: 0.000)   // #FFB800

    static let success        = Color(red: 0.000, green: 0.851, blue: 0.494)   // #00D97E
    static let warning        = Color(red: 1.000, green: 0.624, blue: 0.263)   // #FF9F43
    static let danger         = Color(red: 1.000, green: 0.278, blue: 0.341)   // #FF4757
    static let info           = Color(red: 0.188, green: 0.757, blue: 1.000)   // #30C1FF

    static let text           = Color(red: 0.914, green: 0.933, blue: 0.969)   // #E9EEF7
    static let textMuted      = Color(red: 0.525, green: 0.584, blue: 0.690)   // #8695B0
    static let textDim        = Color(red: 0.353, green: 0.404, blue: 0.510)   // #5A6782
}

// MARK: - Gradients

enum MPGradient {
    static let primary = LinearGradient(
        colors: [MPColor.primary, MPColor.primaryAlt, MPColor.violet],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let accent = LinearGradient(
        colors: [MPColor.accent, MPColor.violet],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let success = LinearGradient(
        colors: [MPColor.success, MPColor.primary],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let sunrise = LinearGradient(
        colors: [MPColor.gold, MPColor.accent],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let danger = LinearGradient(
        colors: [MPColor.danger, MPColor.accent],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let surface = LinearGradient(
        colors: [MPColor.surface2.opacity(0.85), MPColor.bgElevated.opacity(0.92)],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    static let hero = LinearGradient(
        stops: [
            .init(color: Color(red: 0.039, green: 0.063, blue: 0.157), location: 0.0),  // #0A1028
            .init(color: Color(red: 0.118, green: 0.051, blue: 0.212), location: 0.5),  // #1E0D36
            .init(color: Color(red: 0.071, green: 0.039, blue: 0.157), location: 1.0)   // #120A28
        ],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )
}

// MARK: - Background with animated orbs

struct MPBackground: View {
    var body: some View {
        ZStack {
            MPColor.bg.ignoresSafeArea()
            RadialGradient(
                colors: [MPColor.primaryAlt.opacity(0.12), .clear],
                center: .topLeading,
                startRadius: 10, endRadius: 650
            )
            .ignoresSafeArea()
            .blendMode(.plusLighter)

            RadialGradient(
                colors: [MPColor.accent.opacity(0.10), .clear],
                center: .topTrailing,
                startRadius: 10, endRadius: 600
            )
            .ignoresSafeArea()
            .blendMode(.plusLighter)

            RadialGradient(
                colors: [MPColor.violet.opacity(0.16), .clear],
                center: UnitPoint(x: 0.2, y: 0.9),
                startRadius: 10, endRadius: 600
            )
            .ignoresSafeArea()
            .blendMode(.plusLighter)
        }
    }
}

// MARK: - Card modifier

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

extension View {
    func mpCard(padding: CGFloat = 20) -> some View {
        modifier(MPCardStyle(padding: padding))
    }
}

// MARK: - Primary button style

struct MPPrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 16, weight: .bold, design: .default))
            .foregroundColor(Color(red: 0.024, green: 0.067, blue: 0.110))
            .frame(maxWidth: .infinity, minHeight: 54)
            .background(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(MPGradient.primary)
                    .overlay(
                        RoundedRectangle(cornerRadius: 14, style: .continuous)
                            .strokeBorder(Color.white.opacity(0.15), lineWidth: 1)
                    )
                    .shadow(color: MPColor.primary.opacity(0.45), radius: 20, x: 0, y: 10)
            )
            .scaleEffect(configuration.isPressed ? 0.98 : 1.0)
            .opacity(configuration.isPressed ? 0.9 : 1.0)
            .animation(.easeOut(duration: 0.15), value: configuration.isPressed)
    }
}

struct MPGhostButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 15, weight: .semibold))
            .foregroundColor(MPColor.primary)
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(
                Capsule().fill(MPColor.primary.opacity(0.1))
                    .overlay(Capsule().strokeBorder(MPColor.primary.opacity(0.45), lineWidth: 1))
            )
            .opacity(configuration.isPressed ? 0.7 : 1.0)
    }
}

// MARK: - Page title

struct MPPageTitle: View {
    let title: String
    let subtitle: String?
    let systemImage: String

    init(_ title: String, subtitle: String? = nil, systemImage: String) {
        self.title = title
        self.subtitle = subtitle
        self.systemImage = systemImage
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 12) {
                Image(systemName: systemImage)
                    .font(.system(size: 26, weight: .semibold))
                    .foregroundStyle(MPGradient.primary)
                Text(title)
                    .font(.system(size: 28, weight: .bold, design: .default))
                    .foregroundColor(MPColor.text)
            }
            if let subtitle {
                Text(subtitle)
                    .font(.system(size: 14))
                    .foregroundColor(MPColor.textMuted)
            }
        }
    }
}

// MARK: - KPI card

struct MPKpiCard: View {
    let label: String
    let value: String
    let systemImage: String
    let tint: LinearGradient

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Image(systemName: systemImage)
                .font(.system(size: 20, weight: .semibold))
                .foregroundStyle(tint)
                .frame(width: 44, height: 44)
                .background(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .fill(MPColor.primary.opacity(0.12))
                )
            Text(value)
                .font(.system(size: 30, weight: .bold, design: .rounded))
                .foregroundColor(.white)
            Text(label.uppercased())
                .font(.system(size: 11, weight: .semibold))
                .kerning(1.0)
                .foregroundColor(MPColor.textMuted)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .mpCard(padding: 20)
        .overlay(
            HStack {
                RoundedRectangle(cornerRadius: 2)
                    .fill(tint)
                    .frame(width: 4)
                    .padding(.vertical, 18)
                Spacer()
            }
        )
    }
}

// MARK: - Hero banner

struct MPHeroBanner: View {
    let title: String
    let subtitle: String
    let systemImage: String

    var body: some View {
        HStack(alignment: .center, spacing: 16) {
            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 10) {
                    Image(systemName: systemImage)
                        .font(.system(size: 26, weight: .semibold))
                        .foregroundStyle(MPGradient.primary)
                    Text(title)
                        .font(.system(size: 24, weight: .bold))
                        .foregroundColor(.white)
                }
                Text(subtitle)
                    .font(.system(size: 13, weight: .medium))
                    .kerning(0.6)
                    .foregroundColor(MPColor.textMuted)
            }
            Spacer()
        }
        .padding(24)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .fill(MPGradient.hero)
                .overlay(
                    RoundedRectangle(cornerRadius: 22, style: .continuous)
                        .strokeBorder(MPColor.violet.opacity(0.35), lineWidth: 1)
                )
        )
        .shadow(color: .black.opacity(0.5), radius: 24, x: 0, y: 14)
    }
}
