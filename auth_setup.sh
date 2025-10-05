#!/bin/bash
# Trading Bot Dashboard - Authentication Setup
# Configureert authenticatie voor dashboard toegang

set -e

echo "🔐 Dashboard Authenticatie Setup"
echo "================================"
echo ""

# Colors voor output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuratie
CONFIG_FILE=".env"
DASHBOARD_DIR="$(pwd)"

echo -e "${BLUE}📁 Dashboard Directory:${NC} $DASHBOARD_DIR"
echo ""

# Controleer of .env bestand bestaat
if [ -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}⚠️  .env bestand bestaat al${NC}"
    echo -e "${BLUE}   Wil je de bestaande configuratie overschrijven? (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}   Setup geannuleerd${NC}"
        exit 0
    fi
fi

# Vraag om gebruikersnaam
echo -e "${YELLOW}👤 Gebruikersnaam voor dashboard toegang:${NC}"
read -r username
if [ -z "$username" ]; then
    echo -e "${RED}❌ Gebruikersnaam mag niet leeg zijn${NC}"
    exit 1
fi

# Vraag om wachtwoord
echo -e "${YELLOW}🔑 Wachtwoord voor dashboard toegang:${NC}"
read -rs password
if [ -z "$password" ]; then
    echo -e "${RED}❌ Wachtwoord mag niet leeg zijn${NC}"
    exit 1
fi

# Bevestig wachtwoord
echo -e "${YELLOW}🔑 Bevestig wachtwoord:${NC}"
read -rs password_confirm
if [ "$password" != "$password_confirm" ]; then
    echo -e "${RED}❌ Wachtwoorden komen niet overeen${NC}"
    exit 1
fi

# Genereer wachtwoord hash met Python werkzeug (PBKDF2)
echo -e "${YELLOW}🔐 Veilige wachtwoord hash genereren (PBKDF2-SHA256)...${NC}"
password_hash=$(python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('$password', method='pbkdf2:sha256'))")

# Genereer secret key voor Flask sessions
secret_key=$(python3 -c "import os; print(os.urandom(32).hex())")

# Schrijf configuratie naar .env bestand
echo -e "${YELLOW}📝 Configuratie opslaan...${NC}"
cat > "$CONFIG_FILE" << EOF
# Trading Bot Dashboard - Environment Configuration
# Generated on $(date)

# Authentication
DASHBOARD_AUTH_ENABLED=True
DASHBOARD_USERNAME=$username
DASHBOARD_PASSWORD_HASH=$password_hash

# Security
DASHBOARD_SECRET_KEY=$secret_key

# Debug Mode (set to True for development, False for production)
DASHBOARD_DEBUG=False

# Environment (development, production, testing)
DASHBOARD_ENV=production

# Server Configuration
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5001

# Pi Configuration
PI_HOST=stephang@192.168.1.104
PI_PATH=/home/stephang/trading-bot-v4/storage/reports

# Sync Configuration
SYNC_INTERVAL_MINUTES=5
SYNC_TIMEOUT_SECONDS=30

# Cache Configuration
CACHE_ENABLED=True
CACHE_TIMEOUT_SECONDS=60

# Backup Configuration
BACKUP_RETENTION_DAYS=30
MAX_BACKUPS=50
AUTO_BACKUP_ENABLED=True
AUTO_BACKUP_INTERVAL_HOURS=24
EOF

# Stel permissies in
chmod 600 "$CONFIG_FILE"
echo -e "${GREEN}✅ Configuratie opgeslagen in $CONFIG_FILE${NC}"

# Test configuratie
echo -e "${YELLOW}🧪 Configuratie testen...${NC}"
if [ -f "$CONFIG_FILE" ] && [ -r "$CONFIG_FILE" ]; then
    echo -e "${GREEN}✅ Configuratie bestand is geldig${NC}"
else
    echo -e "${RED}❌ Configuratie bestand is ongeldig${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Authenticatie Setup Voltooid!${NC}"
echo ""
echo -e "${BLUE}📋 Wat er is geconfigureerd:${NC}"
echo -e "${BLUE}   ✅ Authenticatie ingeschakeld${NC}"
echo -e "${BLUE}   ✅ Gebruikersnaam: $username${NC}"
echo -e "${BLUE}   ✅ Wachtwoord hash gegenereerd${NC}"
echo -e "${BLUE}   ✅ Configuratie opgeslagen in .env${NC}"
echo ""
echo -e "${BLUE}🔒 Beveiligingsverbeteringen:${NC}"
echo -e "${BLUE}   • Dashboard toegang vereist login${NC}"
echo -e "${BLUE}   • API endpoints zijn beveiligd${NC}"
echo -e "${BLUE}   • Wachtwoord gebruikt PBKDF2-SHA256 hashing${NC}"
echo -e "${BLUE}   • Flask secret key gegenereerd voor sessions${NC}"
echo -e "${BLUE}   • CSRF protection ingeschakeld${NC}"
echo -e "${BLUE}   • Alle toegang wordt gelogd${NC}"
echo ""
echo -e "${BLUE}📝 Belangrijke informatie:${NC}"
echo -e "${BLUE}   • Gebruikersnaam: $username${NC}"
echo -e "${BLUE}   • Wachtwoord: [verborgen]${NC}"
echo -e "${BLUE}   • Configuratie: $CONFIG_FILE${NC}"
echo ""
echo -e "${YELLOW}💡 Om authenticatie uit te schakelen:${NC}"
echo -e "${YELLOW}   DASHBOARD_AUTH_ENABLED=False in $CONFIG_FILE${NC}"
echo ""
echo -e "${GREEN}🚀 Je kunt nu het dashboard starten!${NC}"
echo -e "${BLUE}   python3 web_server.py${NC}"
