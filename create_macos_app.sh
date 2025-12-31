#!/bin/bash
# Create a proper macOS .app bundle that launches the Python GUI

APP_NAME="YouTube Samenvatting"
APP_DIR="$HOME/Desktop/${APP_NAME}.app"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Creating macOS app: ${APP_DIR}"

# Create app structure
mkdir -p "${APP_DIR}/Contents/MacOS"
mkdir -p "${APP_DIR}/Contents/Resources"

# Create Info.plist
cat > "${APP_DIR}/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>YouTube Samenvatting</string>
    <key>CFBundleDisplayName</key>
    <string>YouTube Samenvatting</string>
    <key>CFBundleIdentifier</key>
    <string>com.local.youtubesamenvatting</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>launch</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>LSUIElement</key>
    <false/>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Create launcher script
cat > "${APP_DIR}/Contents/MacOS/launch" << EOF
#!/bin/bash
cd "${SCRIPT_DIR}"
source venv/bin/activate
exec python gui_app.py
EOF

chmod +x "${APP_DIR}/Contents/MacOS/launch"

echo "Done! App created at: ${APP_DIR}"
echo ""
echo "Je kunt de app nu dubbelklikken op je bureaublad!"
