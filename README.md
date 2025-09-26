# 🤖 Trading Bot Dashboard

Een lokaal HTML dashboard om je Trading Bot op de Raspberry Pi te monitoren vanaf je Mac.

## 📊 Features

- **Real-time Monitoring**: Live data van je Pi via CSV bestanden
- **Responsive Design**: Werkt op Mac, iPhone, iPad
- **Automatische Sync**: Elke 5 minuten data van Pi ophalen
- **Charts & Visualisaties**: Equity curve, win/loss breakdown, portfolio overview
- **Volledig Lokaal**: Geen internet of cloud services nodig
- **Security First**: Geen credentials, alleen lokale bestanden

## 🚀 Quick Start

### 1. Installatie

```bash
# Clone of download de dashboard files
cd ~/trading-bot-dashboard

# Installeer Python dependencies
pip3 install -r requirements.txt
```

### 2. SSH Beveiliging Setup (Eénmalig)

```bash
# Voer het SSH beveiliging script uit
./ssh_setup.sh

# Dit script configureert:
# • SSH host key verificatie
# • Veilige SSH authenticatie  
# • Pi host key toevoegen
# • Verbindingen testen
```

**Belangrijk**: Dit script zorgt voor veilige SSH verbindingen en voorkomt man-in-the-middle aanvallen.

### 3. Authenticatie Setup (Eénmalig)

```bash
# Voer het authenticatie setup script uit
./auth_setup.sh

# Dit script configureert:
# • Dashboard gebruikersnaam en wachtwoord
# • Veilige wachtwoord opslag (hash)
# • Authenticatie configuratie
# • .env bestand met credentials
```

**Belangrijk**: Dit script beveiligt dashboard toegang met gebruikersnaam/wachtwoord authenticatie.

### 4. SSL/HTTPS Setup (Eénmalig)

```bash
# Voer het SSL setup script uit
./ssl_setup.sh

# Dit script configureert:
# • SSL certificaten genereren
# • HTTPS server configuratie
# • Encrypted communicatie
# • Veilige data overdracht
```

**Belangrijk**: Dit script beveiligt alle communicatie met SSL/TLS encryptie.

### 5. Start Dashboard

```bash
# Start de web server (HTTP)
python3 web_server.py

# Of start met HTTPS (aanbevolen)
python3 web_server.py --https
```

### 6. Open Dashboard

**HTTP**: Open je browser en ga naar: **http://localhost:5001**
**HTTPS**: Open je browser en ga naar: **https://localhost:5001**

**⚠️ Browser Waarschuwing**: Zelf-ondertekende certificaten geven een browser waarschuwing. Dit is normaal voor lokaal gebruik - klik 'Advanced' en 'Proceed'.

## 📁 Project Structuur

```
~/trading-bot-dashboard/
├── data/                    # CSV bestanden van Pi
├── logs/                    # Sync logs
├── static/
│   ├── css/
│   │   └── dashboard.css    # Custom styling
│   └── js/
│       └── dashboard.js     # Dashboard logic
├── templates/
│   └── dashboard.html       # Main dashboard
├── data_sync.py             # SCP sync system
├── web_server.py            # Flask web server
├── requirements.txt         # Python dependencies
└── README.md               # Deze file
```

## 🔄 Data Flow

```
Pi (192.168.1.104)          Mac (localhost)
├── CSV Reports (15min)  ──► ├── SCP Sync (5min)
├── trades_summary.csv       ├── Data Processing
├── portfolio.csv            ├── HTML Dashboard
└── equity.csv               └── Charts & Visualizations
```

## 📊 Dashboard Sections

### **Status Cards**
- **Bot Status**: Online/Offline status van Pi
- **Total P&L**: Totale winst/verlies
- **Win Rate**: Percentage winnende trades
- **Total Trades**: Aantal uitgevoerde trades

### **Charts**
- **Equity Curve**: Portfolio balans over tijd
- **Win/Loss Breakdown**: Pie chart van winnende vs verliezende trades
- **Trading Statistics**: Gemiddelde win/loss, profit factor

### **Portfolio Overview**
- **Total Balance**: Totale portefeuille waarde
- **Available Balance**: Beschikbaar voor nieuwe trades
- **Open Positions**: Aantal openstaande posities
- **Total P&L**: Huidige winst/verlies

### **System Status**
- **Pi Connection**: Status van Pi connectie
- **Last Sync**: Laatste data sync tijd
- **Data Files**: Aantal beschikbare CSV bestanden
- **Auto Refresh**: Status van automatische updates

## ⚙️ Configuratie

### **Pi Instellingen**
```python
# In data_sync.py
PI_HOST = "stephang@192.168.1.104"
PI_PATH = "/home/stephang/trading-bot-v4/storage/reports"
SYNC_INTERVAL_MINUTES = 5
```

### **Web Server Instellingen**
```python
# In web_server.py
app.run(
    host='0.0.0.0',    # Toegankelijk vanaf andere devices
    port=5000,         # Poort voor dashboard
    debug=True,        # Debug mode
    threaded=True      # Multi-threading
)
```

## 🔧 Troubleshooting

### **Pi Offline**
```
❌ SCP failed: Connection refused
```
**Oplossing:**
1. Check of Pi aan staat: `ping 192.168.1.104`
2. Check SSH: `ssh stephang@192.168.1.104`
3. Check Pi IP: `ip addr show` op Pi

### **Geen Data**
```
⚠️ No trades data available
```
**Oplossing:**
1. Check of Pi CSV bestanden genereert
2. Check Pi path: `/home/stephang/trading-bot-v4/storage/reports/`
3. Manual sync: Klik "Sync Now" button

### **Charts Niet Laden**
```
❌ Error loading dashboard data
```
**Oplossing:**
1. Check browser console (F12)
2. Check web server logs
3. Restart web server: `python3 web_server.py`

### **SSH Permission Denied**
```
❌ Permission denied (publickey)
```
**Oplossing:**
```bash
# Setup SSH key
ssh-keygen -t ed25519
ssh-copy-id stephang@192.168.1.104

# Test connectie
ssh stephang@192.168.1.104
```

## 📱 Mobile Access

Het dashboard is responsive en werkt op alle devices:

- **Mac**: http://localhost:5001
- **iPhone/iPad**: http://[MAC-IP]:5001
- **Andere devices**: http://[MAC-IP]:5001

### **Mac IP Adres Vinden**
```bash
# Vind je Mac IP adres
ifconfig | grep "inet " | grep -v 127.0.0.1
```

## 🔄 Automatische Updates

### **Auto Refresh**
- Dashboard refresht automatisch elke 5 minuten
- Data wordt gesynced van Pi naar Mac
- Charts worden real-time bijgewerkt

### **Manual Sync**
- Klik "Sync Now" button voor directe sync
- Handig voor testing of troubleshooting
- Toont sync status en resultaten

## 📊 CSV Data Format

Het dashboard verwacht deze CSV bestanden van de Pi:

### **trades_summary.csv**
```csv
timestamp,symbol,side,quantity,price,pnl,status
2025-01-25 10:00:00,BTC-USD,buy,0.1,45000,150,closed
```

### **portfolio.csv**
```csv
timestamp,total_balance,available_balance,total_pnl,open_positions
2025-01-25 10:00:00,10000,5000,500,3
```

### **equity.csv**
```csv
timestamp,balance
2025-01-25 10:00:00,10000
2025-01-25 11:00:00,10100
```

## 🛡️ Security

- **Authenticatie**: Gebruikersnaam/wachtwoord login vereist voor alle toegang
- **HTTPS/SSL**: Encrypted communicatie met SSL/TLS certificaten
- **SSH Host Key Verificatie**: Voorkomt man-in-the-middle aanvallen
- **Rate Limiting**: Beschermt tegen brute force en DoS aanvallen
- **Input Validatie**: CSV bestanden worden gevalideerd voor beveiliging
- **Beveiligingslogging**: Volledige audit trail van alle activiteiten
- **Debug Mode**: Uitgeschakeld in productie
- **Wachtwoord Hashing**: Wachtwoorden worden veilig opgeslagen als SHA-256 hash
- **SSH Keys**: Veilige SSH authenticatie met de Pi
- **SSL Certificaten**: Zelf-ondertekende certificaten voor lokaal gebruik
- **Lokaal Netwerk**: Alleen toegankelijk binnen je netwerk
- **Geen Internet**: Volledig offline, geen cloud dependencies
- **Data Privacy**: Alle data blijft lokaal op je Mac

## 🚀 Advanced Usage

### **Custom Sync Interval**
```python
# In data_sync.py
SYNC_INTERVAL_MINUTES = 1  # Sync elke minuut
```

### **Custom Pi Path**
```python
# In data_sync.py
PI_PATH = "/custom/path/to/reports"
```

### **Multiple Pi's**
```python
# In data_sync.py
PI_HOSTS = [
    "stephang@192.168.1.104",
    "stephang@192.168.1.105"
]
```

## 📞 Support

### **Logs Bekijken**
```bash
# Sync logs
tail -f logs/sync.log

# Web server logs
python3 web_server.py  # Toont logs in terminal
```

### **Debug Mode**
```bash
# Start met debug info
FLASK_DEBUG=1 python3 web_server.py
```

### **Data Validatie**
```bash
# Test data sync
python3 data_sync.py

# Check CSV bestanden
ls -la data/*.csv
```

## 🎯 Performance

- **Load Time**: < 2 seconden
- **Memory Usage**: < 100MB
- **CPU Usage**: < 5%
- **Network**: Alleen lokale SCP calls
- **Storage**: CSV bestanden + logs

## 🔄 Updates

### **Dashboard Updates**
```bash
# Stop web server (Ctrl+C)
# Update files
# Restart web server
python3 web_server.py
```

### **Dependencies Updates**
```bash
pip3 install -r requirements.txt --upgrade
```

---

**🎉 Je Trading Bot Dashboard is nu klaar voor gebruik!**

Open **http://localhost:5000** in je browser en begin met monitoren! 🚀📊
