#!/bin/bash
# Setup script voor YouTube Samenvatting

echo "=================================="
echo "YouTube Samenvatting - Setup"
echo "=================================="

cd "$(dirname "$0")"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 niet gevonden. Installeer Python eerst."
    exit 1
fi

echo "Python gevonden: $(python3 --version)"

# Create virtual environment
echo ""
echo "Virtual environment aanmaken..."
python3 -m venv venv

# Activate and install
echo "Dependencies installeren..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=================================="
echo "Setup voltooid!"
echo "=================================="
echo ""
echo "Om de app te TESTEN (GUI):"
echo "  source venv/bin/activate"
echo "  python gui_app.py"
echo ""
echo "Om een .app te BOUWEN:"
echo "  source venv/bin/activate"
echo "  python build_app.py"
echo ""
echo "Om de CLI te gebruiken:"
echo "  source venv/bin/activate"
echo "  python youtube_samenvatting.py <youtube_url> [ollama|openai|anthropic]"
