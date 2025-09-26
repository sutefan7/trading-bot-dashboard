#!/bin/bash
# Trading Bot Dashboard - SSL Certificate Setup
# Genereert zelf-ondertekende SSL certificaten voor HTTPS

set -e

echo "🔐 SSL Certificate Setup"
echo "========================"
echo ""

# Colors voor output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuratie
SSL_DIR="ssl"
CERT_FILE="$SSL_DIR/dashboard.crt"
KEY_FILE="$SSL_DIR/dashboard.key"
DASHBOARD_DIR="$(pwd)"

echo -e "${BLUE}📁 Dashboard Directory:${NC} $DASHBOARD_DIR"
echo -e "${BLUE}🔐 SSL Directory:${NC} $SSL_DIR"
echo ""

# Controleer of OpenSSL beschikbaar is
if ! command -v openssl &> /dev/null; then
    echo -e "${RED}❌ OpenSSL is niet geïnstalleerd${NC}"
    echo -e "${BLUE}   Installeer OpenSSL:${NC}"
    echo -e "${BLUE}   macOS: brew install openssl${NC}"
    echo -e "${BLUE}   Ubuntu: sudo apt-get install openssl${NC}"
    exit 1
fi

# Controleer of SSL directory bestaat
if [ ! -d "$SSL_DIR" ]; then
    echo -e "${YELLOW}📁 SSL directory maken...${NC}"
    mkdir -p "$SSL_DIR"
fi

# Controleer of certificaten al bestaan
if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo -e "${YELLOW}⚠️  SSL certificaten bestaan al${NC}"
    echo -e "${BLUE}   Wil je de bestaande certificaten overschrijven? (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}   Setup geannuleerd${NC}"
        exit 0
    fi
fi

# Vraag om server informatie
echo -e "${YELLOW}🌐 Server informatie voor SSL certificaat:${NC}"
echo -e "${BLUE}   Dit wordt gebruikt voor het SSL certificaat${NC}"
echo ""

# Vraag om Common Name (CN)
echo -e "${YELLOW}📝 Common Name (CN) - Server naam:${NC}"
echo -e "${BLUE}   Voor lokaal gebruik: localhost${NC}"
echo -e "${BLUE}   Voor netwerk toegang: [MAC-IP] of [hostname]${NC}"
read -r common_name
if [ -z "$common_name" ]; then
    common_name="localhost"
fi

# Vraag om Subject Alternative Names (SAN)
echo -e "${YELLOW}📝 Subject Alternative Names (SAN):${NC}"
echo -e "${BLUE}   Voor lokaal gebruik: localhost,127.0.0.1${NC}"
echo -e "${BLUE}   Voor netwerk toegang: localhost,127.0.0.1,[MAC-IP]${NC}"
read -r san_names
if [ -z "$san_names" ]; then
    san_names="localhost,127.0.0.1"
fi

# Genereer SSL certificaat
echo -e "${YELLOW}🔐 SSL certificaat genereren...${NC}"

# Maak configuratie bestand voor OpenSSL
cat > "$SSL_DIR/ssl.conf" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = NL
ST = Netherlands
L = Amsterdam
O = Trading Bot Dashboard
OU = IT Department
CN = $common_name

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
EOF

# Voeg SAN names toe aan configuratie
IFS=',' read -ra ADDR <<< "$san_names"
counter=1
for i in "${ADDR[@]}"; do
    echo "DNS.$counter = $i" >> "$SSL_DIR/ssl.conf"
    ((counter++))
done

# Genereer private key en certificaat
openssl req -x509 -newkey rsa:4096 -keyout "$KEY_FILE" -out "$CERT_FILE" -days 365 -nodes -config "$SSL_DIR/ssl.conf"

# Stel permissies in
chmod 600 "$KEY_FILE"
chmod 644 "$CERT_FILE"
chmod 600 "$SSL_DIR/ssl.conf"

echo -e "${GREEN}✅ SSL certificaat gegenereerd${NC}"

# Test certificaat
echo -e "${YELLOW}🧪 Certificaat testen...${NC}"
if openssl x509 -in "$CERT_FILE" -text -noout > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Certificaat is geldig${NC}"
else
    echo -e "${RED}❌ Certificaat is ongeldig${NC}"
    exit 1
fi

# Toon certificaat informatie
echo -e "${YELLOW}📋 Certificaat informatie:${NC}"
echo -e "${BLUE}   Common Name: $common_name${NC}"
echo -e "${BLUE}   Subject Alternative Names: $san_names${NC}"
echo -e "${BLUE}   Geldig voor: 365 dagen${NC}"
echo -e "${BLUE}   Key Size: 4096 bits${NC}"

# Opruimen configuratie bestand
rm -f "$SSL_DIR/ssl.conf"

echo ""
echo -e "${GREEN}🎉 SSL Certificate Setup Voltooid!${NC}"
echo ""
echo -e "${BLUE}📋 Wat er is geconfigureerd:${NC}"
echo -e "${BLUE}   ✅ SSL certificaat gegenereerd${NC}"
echo -e "${BLUE}   ✅ Private key gegenereerd${NC}"
echo -e "${BLUE}   ✅ Certificaat geldig voor 365 dagen${NC}"
echo -e "${BLUE}   ✅ Permissies correct ingesteld${NC}"
echo ""
echo -e "${BLUE}🔒 Beveiligingsverbeteringen:${NC}"
echo -e "${BLUE}   • HTTPS encrypted communicatie${NC}"
echo -e "${BLUE}   • SSL/TLS beveiliging${NC}"
echo -e "${BLUE}   • Data encryptie in transit${NC}"
echo -e "${BLUE}   • Veilige API communicatie${NC}"
echo ""
echo -e "${BLUE}📝 Belangrijke informatie:${NC}"
echo -e "${BLUE}   • Certificaat: $CERT_FILE${NC}"
echo -e "${BLUE}   • Private Key: $KEY_FILE${NC}"
echo -e "${BLUE}   • Common Name: $common_name${NC}"
echo -e "${BLUE}   • SAN: $san_names${NC}"
echo ""
echo -e "${YELLOW}💡 Browser waarschuwing:${NC}"
echo -e "${YELLOW}   Zelf-ondertekende certificaten geven een browser waarschuwing${NC}"
echo -e "${YELLOW}   Dit is normaal voor lokaal gebruik - klik 'Advanced' en 'Proceed'${NC}"
echo ""
echo -e "${GREEN}🚀 Je kunt nu het dashboard starten met HTTPS!${NC}"
echo -e "${BLUE}   python3 web_server.py --https${NC}"
