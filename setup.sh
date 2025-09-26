#!/bin/bash
# Trading Bot Dashboard - Setup Script
# Automatische installatie en configuratie

set -e

echo "🚀 Trading Bot Dashboard Setup"
echo "=============================="
echo ""

# Colors voor output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuratie
PI_HOST="stephang@192.168.1.104"
PI_PATH="/home/stephang/trading-bot-v4/storage/reports"
DASHBOARD_DIR="$HOME/trading-bot-dashboard"

echo -e "${BLUE}📁 Dashboard Directory:${NC} $DASHBOARD_DIR"
echo -e "${BLUE}📡 Pi Host:${NC} $PI_HOST"
echo -e "${BLUE}📂 Pi Pad:${NC} $PI_PATH"
echo ""

# Controleer of Python 3 is geïnstalleerd
echo -e "${YELLOW}🔍 Python 3 controleren...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 niet gevonden. Installeer Python 3.8+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python 3 gevonden: $PYTHON_VERSION${NC}"

# Controleer of pip is geïnstalleerd
echo -e "${YELLOW}🔍 pip controleren...${NC}"
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 niet gevonden. Installeer pip3${NC}"
    exit 1
fi

echo -e "${GREEN}✅ pip3 gevonden${NC}"

# Haal de script directory op voordat we van directory wisselen
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Maak dashboard directory aan als deze niet bestaat
echo -e "${YELLOW}📁 Dashboard directory aanmaken...${NC}"
mkdir -p "$DASHBOARD_DIR"
cd "$DASHBOARD_DIR"

# Maak subdirectories aan
mkdir -p data logs static/css static/js templates

echo -e "${GREEN}✅ Directory structuur aangemaakt${NC}"

# Kopieer project bestanden naar dashboard directory
echo -e "${YELLOW}📋 Project bestanden kopiëren...${NC}"
cp "$SCRIPT_DIR/requirements.txt" "$DASHBOARD_DIR/"
cp "$SCRIPT_DIR/web_server.py" "$DASHBOARD_DIR/"
cp "$SCRIPT_DIR/data_sync.py" "$DASHBOARD_DIR/"
cp "$SCRIPT_DIR/auto_sync.py" "$DASHBOARD_DIR/"
cp "$SCRIPT_DIR/start_dashboard.sh" "$DASHBOARD_DIR/"
cp -r "$SCRIPT_DIR/static"/* "$DASHBOARD_DIR/static/"
cp -r "$SCRIPT_DIR/templates"/* "$DASHBOARD_DIR/templates/"
cp "$SCRIPT_DIR/README.md" "$DASHBOARD_DIR/"

echo -e "${GREEN}✅ Project bestanden gekopieerd${NC}"

# Installeer Python dependencies
echo -e "${YELLOW}📦 Python dependencies installeren...${NC}"
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies geïnstalleerd${NC}"
else
    echo -e "${RED}❌ requirements.txt niet gevonden${NC}"
    exit 1
fi

# Test SSH verbinding met Pi (veilige versie)
echo -e "${YELLOW}🔍 SSH verbinding met Pi testen...${NC}"
if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=yes "$PI_HOST" "echo 'SSH verbinding succesvol'" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ SSH verbinding met Pi succesvol (veilig)${NC}"
else
    echo -e "${YELLOW}⚠️  SSH verbinding mislukt. SSH beveiliging instellen...${NC}"
    echo -e "${BLUE}   Voer het SSH setup script uit voor veilige configuratie:${NC}"
    echo -e "${BLUE}   ./ssh_setup.sh${NC}"
    echo ""
    echo -e "${YELLOW}💡 Dit script configureert:${NC}"
    echo -e "${YELLOW}   • SSH host key verificatie${NC}"
    echo -e "${YELLOW}   • Veilige SSH authenticatie${NC}"
    echo -e "${YELLOW}   • Pi host key toevoegen${NC}"
    echo ""
    echo -e "${BLUE}   Na SSH setup, voer dit script opnieuw uit${NC}"
    exit 1
fi

# Test SCP verbinding (veilige versie)
echo -e "${YELLOW}🔍 SCP verbinding testen...${NC}"
if scp -o ConnectTimeout=10 -o StrictHostKeyChecking=yes "$PI_HOST:$PI_PATH/*.csv" /tmp/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ SCP verbinding succesvol (veilig)${NC}"
    # Opruimen test bestanden
    rm -f /tmp/*.csv
else
    echo -e "${YELLOW}⚠️  SCP verbinding mislukt (Pi heeft mogelijk nog geen CSV bestanden)${NC}"
    echo -e "${BLUE}   Dit is normaal als de bot nog geen rapporten heeft gegenereerd${NC}"
fi

# Maak voorbeeld data bestanden voor testing
echo -e "${YELLOW}📊 Voorbeeld data bestanden aanmaken...${NC}"

# Sample trades_summary.csv
cat > data/trades_summary.csv << EOF
timestamp,symbol,side,quantity,price,pnl,status
2025-01-25 10:00:00,BTC-USD,buy,0.1,45000,150,closed
2025-01-25 11:00:00,ETH-USD,sell,1.0,3000,-50,closed
2025-01-25 12:00:00,SOL-USD,buy,10.0,100,200,closed
EOF

# Sample portfolio.csv
cat > data/portfolio.csv << EOF
timestamp,total_balance,available_balance,total_pnl,open_positions
2025-01-25 10:00:00,10000,5000,500,3
EOF

# Sample equity.csv
cat > data/equity.csv << EOF
timestamp,balance
2025-01-25 09:00:00,9500
2025-01-25 10:00:00,10000
2025-01-25 11:00:00,9950
2025-01-25 12:00:00,10150
EOF

echo -e "${GREEN}✅ Voorbeeld data bestanden aangemaakt${NC}"

# Stel permissies in
echo -e "${YELLOW}🔐 Permissies instellen...${NC}"
chmod +x data_sync.py web_server.py
chmod 755 data logs static templates

echo -e "${GREEN}✅ Permissies ingesteld${NC}"

# Test data synchronisatie
echo -e "${YELLOW}🧪 Data synchronisatie testen...${NC}"
if python3 data_sync.py > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Data synchronisatie test succesvol${NC}"
else
    echo -e "${YELLOW}⚠️  Data synchronisatie test mislukt (normaal als Pi offline is)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Setup Voltooid!${NC}"
echo ""
echo -e "${BLUE}📋 Volgende Stappen:${NC}"
echo -e "${BLUE}   1. Start het dashboard:${NC}"
echo -e "${BLUE}      cd $DASHBOARD_DIR${NC}"
echo -e "${BLUE}      python3 web_server.py${NC}"
echo ""
echo -e "${BLUE}   2. Open je browser:${NC}"
echo -e "${BLUE}      http://localhost:5000${NC}"
echo ""
echo -e "${BLUE}   3. Voor mobiele toegang:${NC}"
echo -e "${BLUE}      http://$(ifconfig | grep 'inet ' | grep -v 127.0.0.1 | head -1 | awk '{print $2}'):5000${NC}"
echo ""
echo -e "${BLUE}📚 Documentatie:${NC}"
echo -e "${BLUE}      README.md${NC}"
echo ""
echo -e "${GREEN}🚀 Succesvol Trading!${NC}"
