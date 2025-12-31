#!/usr/bin/env python3
"""
Build script voor YouTube Samenvatting Mac App
Maakt een standalone .app bundle met PyInstaller
"""

import subprocess
import sys
import os
from pathlib import Path

# App configuratie
APP_NAME = "YouTube Samenvatting"
SCRIPT = "gui_app.py"
ICON = None  # Optioneel: pad naar .icns bestand

def main():
    print("=" * 50)
    print(f"Building {APP_NAME}")
    print("=" * 50)

    # Controleer of PyInstaller geinstalleerd is
    try:
        import PyInstaller
        print(f"PyInstaller versie: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller niet gevonden. Installeren...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--windowed",  # Geen terminal venster
        "--onedir",  # Directory bundle (sneller te starten dan onefile)
        "--clean",  # Clean build
        "--noconfirm",  # Overschrijf zonder vragen
        # Hidden imports die PyInstaller mogelijk mist
        "--hidden-import", "youtube_transcript_api",
        "--hidden-import", "openai",
        "--hidden-import", "anthropic",
        "--hidden-import", "requests",
        "--hidden-import", "certifi",
        "--hidden-import", "charset_normalizer",
        # Voeg het hoofdmodule toe als data
        "--add-data", "youtube_samenvatting.py:.",
        # macOS specifiek
        "--osx-bundle-identifier", "com.local.youtubesamenvatting",
    ]

    # Voeg icoon toe indien beschikbaar
    if ICON and Path(ICON).exists():
        cmd.extend(["--icon", ICON])

    # Het script om te bundelen
    cmd.append(SCRIPT)

    print("\nRunning PyInstaller...")
    print(f"Command: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd)

    if result.returncode == 0:
        app_path = Path("dist") / f"{APP_NAME}.app"
        print("\n" + "=" * 50)
        print("BUILD SUCCESVOL!")
        print("=" * 50)
        print(f"\nApp locatie: {app_path.absolute()}")
        print(f"\nJe kunt de app nu naar je Applications map of bureaublad slepen:")
        print(f"  cp -r 'dist/{APP_NAME}.app' /Applications/")
        print(f"  of")
        print(f"  cp -r 'dist/{APP_NAME}.app' ~/Desktop/")
        print("\nOf open de dist map:")
        print(f"  open dist/")
    else:
        print("\nBuild gefaald!")
        sys.exit(1)


if __name__ == "__main__":
    main()
