# 🏗️ Trading Bot Dashboard - Architecture v2.0

## 📋 **Overzicht**

De Trading Bot Dashboard is geëvolueerd naar een **moderne, robuuste architectuur** met geavanceerde features voor productie-gebruik. Deze documentatie beschrijft de nieuwe architectuur en verbeteringen.

---

## 🎯 **Belangrijkste Verbeteringen**

### ✅ **Nieuwe Features**
- **Database-gebaseerde Pi synchronisatie** (geen CSV meer)
- **Intelligente fallback mechanismen** 
- **Uitgebreide health monitoring**
- **Geavanceerde caching met compressie**
- **Real-time API endpoints**
- **Verbeterde error handling**

### 🔧 **Technische Verbeteringen**
- **Modulaire architectuur** met gescheiden verantwoordelijkheden
- **Performance optimalisaties** met LRU cache en compressie
- **Robuuste error recovery** met multiple fallback layers
- **Comprehensive monitoring** van alle systemen
- **Enhanced security** met verbeterde validatie

---

## 🏛️ **Architectuur Overzicht**

```
┌─────────────────────────────────────────────────────────────┐
│                    TRADING BOT DASHBOARD v2.0               │
├─────────────────────────────────────────────────────────────┤
│  Frontend (HTML/CSS/JS)                                     │
│  ├── Dashboard UI                                           │
│  ├── Real-time Charts                                       │
│  └── Health Monitoring                                      │
├─────────────────────────────────────────────────────────────┤
│  Web Server (Flask)                                         │
│  ├── API Endpoints                                          │
│  ├── Authentication & Security                              │
│  ├── Rate Limiting                                          │
│  └── Request Routing                                        │
├─────────────────────────────────────────────────────────────┤
│  Core Services                                              │
│  ├── PiAPIClient (Database Sync)                           │
│  ├── FallbackManager (Error Recovery)                      │
│  ├── HealthMonitor (System Monitoring)                     │
│  ├── AdvancedCache (Performance)                           │
│  └── DataProcessor (Data Processing)                       │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                 │
│  ├── Local SQLite Database                                  │
│  ├── CSV Files (Fallback)                                  │
│  ├── Cache Layer                                            │
│  └── Backup System                                          │
├─────────────────────────────────────────────────────────────┤
│  External Systems                                           │
│  ├── Raspberry Pi (Trading Bot)                            │
│  ├── SSH Connection                                         │
│  └── Database Queries                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 **Data Flow Architectuur**

### **1. Primary Data Flow (Pi Online)**
```
Pi Database → PiAPIClient → Local CSV → Database → Cache → Dashboard
```

### **2. Fallback Data Flow (Pi Offline)**
```
Local CSV/Database → FallbackManager → Cache → Dashboard
```

### **3. Health Monitoring Flow**
```
All Systems → HealthMonitor → Health API → Dashboard
```

---

## 📦 **Core Components**

### **1. PiAPIClient** (`pi_api_client.py`)
**Functie**: Database-gebaseerde synchronisatie met Pi
- **SSH connectiviteit** naar Pi
- **SQLite database queries** op Pi
- **Real-time data ophalen** (trades, portfolio, equity)
- **Automatische data validatie**
- **Error handling** en retry logic

**Key Methods**:
- `sync_trading_data()` - Sync alle trading data
- `get_pi_health()` - Pi systeem health check
- `check_pi_connectivity()` - Netwerk connectiviteit

### **2. FallbackManager** (`fallback_manager.py`)
**Functie**: Intelligente fallback wanneer Pi offline is
- **Multi-layer fallback** (CSV → Database → Demo data)
- **Data freshness detection**
- **Automatic fallback activation**
- **Cache management** voor fallback data

**Fallback Priority**:
1. **Local CSV files** (recent data)
2. **Local database** (cached data)
3. **Demo data** (last resort)

### **3. HealthMonitor** (`health_monitor.py`)
**Functie**: Comprehensive system health monitoring
- **System resources** (CPU, Memory, Disk)
- **Database health** en connectivity
- **Pi connectivity** en status
- **Data freshness** monitoring
- **Log file analysis**
- **SSL certificate monitoring**
- **Backup system health**

**Health Levels**:
- 🟢 **Healthy** - All systems operational
- 🟡 **Warning** - Minor issues detected
- 🔴 **Critical** - Major issues requiring attention

### **4. AdvancedCache** (`cache.py`)
**Functie**: High-performance caching met compressie
- **LRU (Least Recently Used)** eviction
- **Automatic compression** voor grote data
- **Performance monitoring** en statistics
- **Memory usage optimization**
- **TTL (Time To Live)** support

**Features**:
- **Compression**: Gzip compressie voor data > 1KB
- **LRU Management**: Automatische eviction van oude data
- **Performance Stats**: Hit rate, memory usage, compression savings

---

## 🔌 **API Endpoints**

### **Core Data Endpoints**
- `GET /api/trading-performance` - Trading performance metrics
- `GET /api/portfolio` - Portfolio overview
- `GET /api/equity-curve` - Equity curve data
- `GET /api/bot-status` - Bot status information

### **Pi Integration Endpoints**
- `POST /api/pi-sync` - Trigger Pi database sync
- `GET /api/pi-health` - Pi system health
- `GET /api/pi-database-info` - Pi database information

### **System Monitoring Endpoints**
- `GET /api/health-check` - Comprehensive health check
- `GET /api/health-history` - Health check history
- `GET /api/fallback-status` - Fallback system status
- `GET /api/stats` - System statistics

### **Legacy Endpoints** (Backward Compatibility)
- `POST /api/sync-now` - Legacy CSV sync
- `GET /api/sync-status` - Legacy sync status

---

## ⚙️ **Configuration**

### **Environment Variables**
```bash
# Pi Configuration
PI_HOST=stephang@192.168.1.104
PI_APP_PATH=/srv/trading-bot-pi/app
PI_DATABASE_PATH=/srv/trading-bot-pi/app/data
PI_API_ENABLED=True

# Cache Configuration
CACHE_ENABLED=True
CACHE_TIMEOUT_SECONDS=60

# Health Monitoring
HEALTH_CHECK_INTERVAL=300  # 5 minutes
HEALTH_ALERT_THRESHOLDS=80,85,90  # CPU, Memory, Disk

# Fallback Configuration
FALLBACK_ENABLED=True
DATA_AGE_THRESHOLD_HOURS=2
```

### **Configuration Classes**
- **Config** - Base configuration
- **DevelopmentConfig** - Development settings
- **ProductionConfig** - Production settings
- **TestConfig** - Testing settings

---

## 🛡️ **Security Features**

### **Authentication & Authorization**
- **HTTP Basic Auth** met PBKDF2-SHA256
- **CSRF Protection** voor alle POST requests
- **Rate Limiting** per endpoint type
- **IP Whitelisting** voor private netwerken

### **Data Security**
- **Input validation** voor alle API endpoints
- **CSV sanitization** met suspicious content detection
- **SQL injection prevention** met parameterized queries
- **SSH host verification** voor Pi connecties

### **Audit & Logging**
- **Comprehensive audit logging** van alle activiteiten
- **Security event logging** voor verdachte activiteiten
- **Rotating log files** met size limits
- **Structured logging** voor easy analysis

---

## 📊 **Performance Optimizations**

### **Caching Strategy**
- **Multi-level caching** (Memory → Database → Files)
- **Intelligent cache invalidation** op data updates
- **Compression** voor memory efficiency
- **LRU eviction** voor optimal memory usage

### **Database Optimizations**
- **Indexed queries** voor snelle data retrieval
- **Connection pooling** voor database efficiency
- **Query optimization** met proper WHERE clauses
- **Batch operations** voor bulk data updates

### **Network Optimizations**
- **Connection reuse** voor SSH connecties
- **Timeout management** voor network operations
- **Retry logic** met exponential backoff
- **Parallel data fetching** waar mogelijk

---

## 🔧 **Deployment & Operations**

### **System Requirements**
- **Python 3.8+** met pip packages
- **SQLite3** voor lokale database
- **SSH access** naar Pi
- **Network connectivity** naar Pi (192.168.1.104)

### **Installation**
```bash
# Clone repository
git clone <repository-url>
cd trading-bot-dashboard

# Install dependencies
pip install -r requirements.txt

# Setup configuration
cp .env.example .env
# Edit .env with your settings

# Initialize system
python setup.py

# Start dashboard
python web_server.py
```

### **Monitoring & Maintenance**
- **Health checks** elke 5 minuten
- **Automatic backups** dagelijks
- **Log rotation** automatisch
- **Cache cleanup** periodiek

---

## 🚀 **Future Enhancements**

### **Planned Features**
- **WebSocket support** voor real-time updates
- **GraphQL API** voor flexible data queries
- **Docker containerization** voor easy deployment
- **Kubernetes support** voor scaling
- **Prometheus metrics** voor advanced monitoring

### **Performance Improvements**
- **Redis caching** voor distributed caching
- **Database clustering** voor high availability
- **CDN integration** voor static assets
- **Load balancing** voor multiple instances

---

## 📚 **Development Guidelines**

### **Code Structure**
- **Modular design** met gescheiden concerns
- **Type hints** voor alle functions
- **Comprehensive error handling** met logging
- **Unit tests** voor alle components
- **Documentation** voor alle public APIs

### **Best Practices**
- **Fail-fast** met early validation
- **Graceful degradation** bij system failures
- **Resource cleanup** in finally blocks
- **Security-first** approach voor alle features
- **Performance monitoring** voor alle operations

---

## 🆘 **Troubleshooting**

### **Common Issues**
1. **Pi Connectivity**: Check SSH keys en network
2. **Database Locked**: Restart dashboard service
3. **Cache Issues**: Clear cache via API
4. **Health Warnings**: Check system resources
5. **Fallback Activation**: Verify Pi status

### **Debug Commands**
```bash
# Check Pi connectivity
ssh stephang@192.168.1.104 "echo 'Pi is online'"

# Check dashboard health
curl -u admin:password http://localhost:5001/api/health-check

# Check fallback status
curl -u admin:password http://localhost:5001/api/fallback-status

# View logs
tail -f logs/server.log
```

---

## 📈 **Metrics & KPIs**

### **Performance Metrics**
- **Response time** < 500ms voor API calls
- **Cache hit rate** > 80%
- **Uptime** > 99.9%
- **Data freshness** < 2 hours

### **Health Metrics**
- **CPU usage** < 80%
- **Memory usage** < 85%
- **Disk usage** < 90%
- **Error rate** < 1%

---

*Deze architectuur documentatie wordt regelmatig bijgewerkt met nieuwe features en verbeteringen.*

