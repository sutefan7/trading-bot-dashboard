#!/bin/bash
# Trading Bot Dashboard - Start Script
# Start de dashboard web server

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🤖 Trading Bot Dashboard${NC}"
echo -e "${BLUE}========================${NC}"
echo ""

# Get dashboard directory
DASHBOARD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DASHBOARD_DIR"

echo -e "${YELLOW}📁 Dashboard Directory:${NC} $DASHBOARD_DIR"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Check if required files exist
if [ ! -f "web_server.py" ]; then
    echo -e "${RED}❌ web_server.py not found${NC}"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

# Check if dependencies are installed
echo -e "${YELLOW}🔍 Checking dependencies...${NC}"
if ! python3 -c "import flask, pandas, numpy, schedule" 2>/dev/null; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    pip3 install -r requirements.txt
fi

echo -e "${GREEN}✅ Dependencies ready${NC}"

# Create necessary directories
mkdir -p data logs

echo -e "${YELLOW}🚀 Starting Trading Bot Dashboard...${NC}"
echo ""
echo -e "${GREEN}📊 Dashboard will be available at:${NC}"
echo -e "${GREEN}   http://localhost:5001${NC}"
echo ""
echo -e "${GREEN}📱 Mobile access:${NC}"
echo -e "${GREEN}   http://$(ifconfig | grep 'inet ' | grep -v 127.0.0.1 | head -1 | awk '{print $2}'):5001${NC}"
echo ""
echo -e "${YELLOW}💡 Press Ctrl+C to stop the dashboard${NC}"
echo ""

# Start the web server
python3 web_server.py --host 0.0.0.0 --port 5001
