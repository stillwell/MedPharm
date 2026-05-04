#!/usr/bin/env python3
# MedPharm ERP - Medical & Pharmaceutical Management System
# Copyright (C) 2026 Enlightec Ltd. (www.enlightec.com)
# Author: Robert Andrew Stillwell
# License: GNU General Public License v3.0
#
# ─────────────────────────────────────────────────────────────────────────────
# Generate every per-platform branding asset from the two source PNGs in
# images/.  Idempotent — re-running overwrites existing outputs deterministically.
#
#   Sources:
#     images/enlightec-ltd.png         500 × 500 RGBA — the company logo
#     images/medpharm-erp-banner.png   1024 × 559     — the product banner
#
#   Outputs (relative to repo root):
#     qt_app/resources/                       PNG copies for the Qt desktop
#     web/static/img/                         PNG copies for the Flask portal
#     ios/MedPharm/MedPharm/Assets.xcassets/  AppIcon.appiconset + imagesets
#     macos/MedPharm/MedPharm/Assets.xcassets/  AppIcon.appiconset + imagesets
#     android/app/src/main/res/mipmap-*/      ic_launcher{,_round}.png at 5
#                                             densities + adaptive foreground
#     android/app/src/main/res/drawable/      enlightec_logo.png + medpharm_banner.png
#     windows/MedPharm/Assets/                medpharm-icon.ico (multi-res)
#                                             + enlightec-logo.png + medpharm-banner.png
#
# Run:  python3 tools/generate_branding_assets.py
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow is required. Install with:  pip install Pillow")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
SRC_LOGO   = ROOT / "images" / "enlightec-ltd.png"
SRC_BANNER = ROOT / "images" / "medpharm-erp-banner.png"

# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_logo(square: int = 1024, *, with_alpha: bool = True) -> Image.Image:
    """Load the source 500×500 logo and upscale to a square canvas of `square`
    px on a side (transparent background by default).  We upscale once to a
    high-res canvas then downscale per-target so each resized PNG comes from a
    single Lanczos resample, not a chain of degraded ones."""
    img = Image.open(SRC_LOGO).convert("RGBA")
    w, h = img.size
    side = max(w, h)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - w) // 2, (side - h) // 2), img)
    return canvas.resize((square, square), Image.Resampling.LANCZOS)


def _square_with_bg(logo: Image.Image, size: int, bg=(255, 255, 255, 255)
                     ) -> Image.Image:
    """Return a `size × size` image with the logo centred on a solid background.
    iOS / Android launcher icons reject transparency at the App Store / Play
    Store level; macOS allows it but a clean white background looks crisper.
    Pad the logo to ~80% of the canvas so it doesn't crowd the corners."""
    bg_im = Image.new("RGBA", (size, size), bg)
    target = int(size * 0.80)
    inner = logo.resize((target, target), Image.Resampling.LANCZOS)
    bg_im.paste(inner, ((size - target) // 2, (size - target) // 2), inner)
    return bg_im


def _write_png(img: Image.Image, dst: Path, *, optimise: bool = True) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, "PNG", optimize=optimise)
    print(f"  wrote {dst.relative_to(ROOT)}  ({img.size[0]}×{img.size[1]})")


def _write_json(obj: dict, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(obj, indent=2))
    print(f"  wrote {dst.relative_to(ROOT)}")


def _copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    print(f"  copied {src.relative_to(ROOT)} → {dst.relative_to(ROOT)}")


# ── Qt desktop ─────────────────────────────────────────────────────────────────

def gen_qt() -> None:
    print("\n── Qt desktop (qt_app/resources/) ──")
    target_dir = ROOT / "qt_app" / "resources"
    _copy(SRC_LOGO,   target_dir / "enlightec-ltd.png")
    _copy(SRC_BANNER, target_dir / "medpharm-erp-banner.png")


# ── Web portal ─────────────────────────────────────────────────────────────────

def gen_web() -> None:
    print("\n── Web portal (web/static/img/) ──")
    target_dir = ROOT / "web" / "static" / "img"
    _copy(SRC_LOGO,   target_dir / "enlightec-ltd.png")
    _copy(SRC_BANNER, target_dir / "medpharm-erp-banner.png")


# ── iOS ────────────────────────────────────────────────────────────────────────
# Apple's Human Interface Guidelines define every iconset entry by point-size
# and scale.  Modern Xcode (≥14) accepts a single 1024×1024 icon in
# Universal mode and slices automatically; we provide that single-size form.
# In-app branding goes through "imageset" wrappers that Xcode recognises so
# SwiftUI's `Image("EnlightecLogo")` resolves directly.

def _imageset_contents(filename: str) -> dict:
    return {
        "images": [
            {"idiom": "universal", "filename": filename, "scale": "1x"},
            {"idiom": "universal", "scale": "2x"},
            {"idiom": "universal", "scale": "3x"},
        ],
        "info": {"version": 1, "author": "xcode"},
    }


def _appicon_universal_contents(filename: str) -> dict:
    return {
        "images": [{
            "filename": filename,
            "idiom": "universal",
            "platform": "ios",
            "size": "1024x1024",
        }],
        "info": {"version": 1, "author": "xcode"},
    }


def gen_apple(platform: str, base: Path) -> None:
    print(f"\n── {platform} (Assets.xcassets/) ──")
    xcassets = base / "Assets.xcassets"
    # Top-level catalog metadata
    _write_json(
        {"info": {"version": 1, "author": "xcode"}},
        xcassets / "Contents.json",
    )

    # AppIcon — universal 1024×1024 (Xcode 14+ slices automatically). For
    # macOS we also write the legacy multi-size set so older toolchains work.
    appiconset = xcassets / "AppIcon.appiconset"
    logo = _load_logo(1024)
    if platform == "iOS":
        icon_1024 = _square_with_bg(logo, 1024)
        _write_png(icon_1024, appiconset / "icon-1024.png", optimise=False)
        _write_json(_appicon_universal_contents("icon-1024.png"),
                    appiconset / "Contents.json")
    else:
        # macOS expects square 16/32/128/256/512 with @1x and @2x variants
        sizes = [(16, "1x"), (32, "2x"),
                 (32, "1x"), (64, "2x"),
                 (128, "1x"), (256, "2x"),
                 (256, "1x"), (512, "2x"),
                 (512, "1x"), (1024, "2x")]
        images = []
        for px, scale in sizes:
            pt = px if scale == "1x" else px // 2
            fname = f"icon_{pt}x{pt}@{scale}.png"
            _write_png(_square_with_bg(logo, px),
                       appiconset / fname, optimise=False)
            images.append({"size": f"{pt}x{pt}", "idiom": "mac",
                           "filename": fname, "scale": scale})
        _write_json({"images": images, "info": {"version": 1, "author": "xcode"}},
                    appiconset / "Contents.json")

    # In-app branding imagesets — SwiftUI Image("EnlightecLogo") /
    # Image("MedPharmBanner") will resolve here.
    logo_set = xcassets / "EnlightecLogo.imageset"
    _copy(SRC_LOGO, logo_set / "enlightec-ltd.png")
    _write_json(_imageset_contents("enlightec-ltd.png"),
                logo_set / "Contents.json")

    banner_set = xcassets / "MedPharmBanner.imageset"
    _copy(SRC_BANNER, banner_set / "medpharm-erp-banner.png")
    _write_json(_imageset_contents("medpharm-erp-banner.png"),
                banner_set / "Contents.json")


# ── Android ────────────────────────────────────────────────────────────────────
# Android uses density-bucketed PNGs at fixed sizes:
#   mdpi    48 × 48      hdpi    72 × 72       xhdpi   96 × 96
#   xxhdpi  144 × 144    xxxhdpi 192 × 192
# Adaptive icons (API 26+) want a 432 × 432 foreground with a 264 × 264 safe
# zone (i.e. the brand should fit inside the inner 66 dp out of 108 dp).

ANDROID_DENSITIES = {
    "mdpi":    48,
    "hdpi":    72,
    "xhdpi":   96,
    "xxhdpi":  144,
    "xxxhdpi": 192,
}


def gen_android() -> None:
    print("\n── Android (res/mipmap-*, res/drawable/) ──")
    res = ROOT / "android" / "app" / "src" / "main" / "res"
    logo = _load_logo(1024)

    for density, size in ANDROID_DENSITIES.items():
        # Standard square launcher icon (white-background to satisfy Play Store
        # transparency rules and to look correct on legacy launchers).
        sq = _square_with_bg(logo, size)
        _write_png(sq, res / f"mipmap-{density}" / "ic_launcher.png",
                   optimise=False)

        # Round mask — Android takes care of the round mask itself, but
        # `ic_launcher_round.png` is still expected for older launchers; ship
        # the same square art and let the launcher round-corner it.
        _write_png(sq, res / f"mipmap-{density}" / "ic_launcher_round.png",
                   optimise=False)

    # Adaptive icon foreground — 432 × 432 with the logo centred at ~62% of
    # canvas so it stays inside the 264 × 264 safe zone. Goes in drawable/
    # (not mipmap-anydpi-v26/, which is for XML qualifiers); the existing
    # mipmap-anydpi-v26/ic_launcher.xml already references
    # @drawable/ic_launcher_foreground, which resolves to this PNG.
    foreground = Image.new("RGBA", (432, 432), (0, 0, 0, 0))
    inner = logo.resize((268, 268), Image.Resampling.LANCZOS)
    foreground.paste(inner, ((432 - 268) // 2, (432 - 268) // 2), inner)
    _write_png(foreground,
               res / "drawable" / "ic_launcher_foreground.png",
               optimise=False)

    # Drawables for in-app branding (login screen, About dialog).
    _copy(SRC_LOGO,   res / "drawable" / "enlightec_logo.png")
    _copy(SRC_BANNER, res / "drawable" / "medpharm_banner.png")


# ── Windows ────────────────────────────────────────────────────────────────────
# WPF wants a multi-resolution .ico for ApplicationIcon. PIL can write .ico
# with sizes embedded; Windows picks the best for each context (taskbar, alt-
# tab, file-explorer thumbnail).

WIN_ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def gen_windows() -> None:
    print("\n── Windows (windows/MedPharm/Assets/) ──")
    target_dir = ROOT / "windows" / "MedPharm" / "Assets"
    target_dir.mkdir(parents=True, exist_ok=True)

    logo = _load_logo(256)
    # Pillow's ICO writer accepts a `sizes` argument for multi-res output.
    icons = [(s, s) for s in WIN_ICO_SIZES]
    ico_path = target_dir / "medpharm-icon.ico"
    _square_with_bg(logo, 256).save(
        ico_path, format="ICO", sizes=icons, optimize=True)
    print(f"  wrote {ico_path.relative_to(ROOT)}  (multi-res: "
          + ", ".join(f"{s}px" for s in WIN_ICO_SIZES) + ")")

    # In-app branding PNGs.
    _copy(SRC_LOGO,   target_dir / "enlightec-logo.png")
    _copy(SRC_BANNER, target_dir / "medpharm-banner.png")


# ── Driver ─────────────────────────────────────────────────────────────────────

def main() -> int:
    if not SRC_LOGO.exists() or not SRC_BANNER.exists():
        print(f"ERROR: missing source images.\n"
              f"  expected: {SRC_LOGO}\n"
              f"            {SRC_BANNER}")
        return 2

    print(f"Source logo   : {SRC_LOGO}  ({Image.open(SRC_LOGO).size})")
    print(f"Source banner : {SRC_BANNER}  ({Image.open(SRC_BANNER).size})")

    gen_qt()
    gen_web()
    gen_apple("iOS",   ROOT / "ios"   / "MedPharm" / "MedPharm")
    gen_apple("macOS", ROOT / "macos" / "MedPharm" / "MedPharm")
    gen_android()
    gen_windows()

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
