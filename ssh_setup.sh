#!/bin/bash
# Trading Bot Dashboard - SSH Security Setup
# Veilige SSH configuratie voor Pi verbinding

set -e

echo "🔐 SSH Beveiliging Setup"
echo "========================"
echo ""

# Colors voor output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuratie
PI_HOST="stephang@192.168.1.104"
PI_IP="192.168.1.104"
SSH_DIR="$HOME/.ssh"
KNOWN_HOSTS="$SSH_DIR/known_hosts"

echo -e "${BLUE}📡 Pi Host:${NC} $PI_HOST"
echo -e "${BLUE}🌐 Pi IP:${NC} $PI_IP"
echo ""

# Controleer of SSH directory bestaat
if [ ! -d "$SSH_DIR" ]; then
    echo -e "${YELLOW}📁 SSH directory aanmaken...${NC}"
    mkdir -p "$SSH_DIR"
    chmod 700 "$SSH_DIR"
    echo -e "${GREEN}✅ SSH directory aangemaakt${NC}"
fi

# Controleer of known_hosts bestaat
if [ ! -f "$KNOWN_HOSTS" ]; then
    echo -e "${YELLOW}📝 Known hosts bestand aanmaken...${NC}"
    touch "$KNOWN_HOSTS"
    chmod 644 "$KNOWN_HOSTS"
    echo -e "${GREEN}✅ Known hosts bestand aangemaakt${NC}"
fi

# SSH key genereren als deze niet bestaat
if [ ! -f "$SSH_DIR/id_ed25519" ]; then
    echo -e "${YELLOW}🔑 SSH key genereren...${NC}"
    ssh-keygen -t ed25519 -f "$SSH_DIR/id_ed25519" -N "" -C "trading-bot-dashboard"
    echo -e "${GREEN}✅ SSH key gegenereerd${NC}"
fi

# Pi host key ophalen en toevoegen aan known_hosts
echo -e "${YELLOW}🔍 Pi host key ophalen...${NC}"
if ssh-keyscan -H "$PI_IP" >> "$KNOWN_HOSTS" 2>/dev/null; then
    echo -e "${GREEN}✅ Pi host key toegevoegd aan known_hosts${NC}"
else
    echo -e "${RED}❌ Kon Pi host key niet ophalen${NC}"
    echo -e "${YELLOW}💡 Controleer of Pi online is en SSH draait${NC}"
    exit 1
fi

# SSH key naar Pi kopiëren
echo -e "${YELLOW}📤 SSH key naar Pi kopiëren...${NC}"
if ssh-copy-id -i "$SSH_DIR/id_ed25519.pub" "$PI_HOST" 2>/dev/null; then
    echo -e "${GREEN}✅ SSH key naar Pi gekopieerd${NC}"
else
    echo -e "${RED}❌ SSH key kopiëren mislukt${NC}"
    echo -e "${YELLOW}💡 Voer handmatig uit: ssh-copy-id -i $SSH_DIR/id_ed25519.pub $PI_HOST${NC}"
    exit 1
fi

# SSH verbinding testen
echo -e "${YELLOW}🧪 SSH verbinding testen...${NC}"
if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=yes "$PI_HOST" "echo 'SSH verbinding succesvol'" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ SSH verbinding succesvol${NC}"
else
    echo -e "${RED}❌ SSH verbinding mislukt${NC}"
    echo -e "${YELLOW}💡 Controleer Pi SSH configuratie${NC}"
    exit 1
fi

# SCP verbinding testen
echo -e "${YELLOW}🧪 SCP verbinding testen...${NC}"
if scp -o ConnectTimeout=10 -o StrictHostKeyChecking=yes "$PI_HOST:/home/stephang/trading-bot-v4/storage/reports/*.csv" /tmp/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ SCP verbinding succesvol${NC}"
    # Opruimen test bestanden
    rm -f /tmp/*.csv
else
    echo -e "${YELLOW}⚠️  SCP verbinding mislukt (Pi heeft mogelijk nog geen CSV bestanden)${NC}"
    echo -e "${BLUE}   Dit is normaal als de bot nog geen rapporten heeft gegenereerd${NC}"
fi

echo ""
echo -e "${GREEN}🎉 SSH Beveiliging Setup Voltooid!${NC}"
echo ""
echo -e "${BLUE}📋 Wat er is geconfigureerd:${NC}"
echo -e "${BLUE}   ✅ SSH host key verificatie ingeschakeld${NC}"
echo -e "${BLUE}   ✅ Pi host key toegevoegd aan known_hosts${NC}"
echo -e "${BLUE}   ✅ SSH key authenticatie geconfigureerd${NC}"
echo -e "${BLUE}   ✅ Verbindingen getest${NC}"
echo ""
echo -e "${BLUE}🔒 Beveiligingsverbeteringen:${NC}"
echo -e "${BLUE}   • Man-in-the-middle aanvallen voorkomen${NC}"
echo -e "${BLUE}   • Host key verificatie actief${NC}"
echo -e "${BLUE}   • Veilige SSH authenticatie${NC}"
echo ""
echo -e "${GREEN}🚀 Je kunt nu het dashboard starten!${NC}"
