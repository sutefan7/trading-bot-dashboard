#!/usr/bin/env python3
"""
Quick Export Tool - Summary voor snelle review
"""

import os
from pathlib import Path
from datetime import datetime

def get_file_summary(file_path):
    """Get file summary"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return {
                'lines': len(lines),
                'size': os.path.getsize(file_path),
                'first_line': lines[0].strip() if lines else '',
                'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%d-%m-%Y %H:%M')
            }
    except:
        return {'lines': 0, 'size': 0, 'first_line': 'Error reading file', 'last_modified': 'Unknown'}

def main():
    """Generate quick summary"""
    print("🚀 Trading Bot Dashboard - Quick Summary")
    print("=" * 50)
    
    # Key files to review
    key_files = [
        'web_server.py',
        'templates/dashboard.html', 
        'static/js/dashboard.js',
        'static/css/dashboard.css',
        'data_sync.py',
        'setup.sh',
        'requirements.txt',
        'README.md'
    ]
    
    print("\n📋 Belangrijkste Bestanden:")
    print("-" * 30)
    
    for file_path in key_files:
        if os.path.exists(file_path):
            summary = get_file_summary(file_path)
            size_kb = summary['size'] / 1024
            print(f"📄 {file_path}")
            print(f"   📊 {summary['lines']} regels, {size_kb:.1f} KB")
            print(f"   🕒 Laatst gewijzigd: {summary['last_modified']}")
            if summary['first_line']:
                print(f"   📝 Eerste regel: {summary['first_line'][:60]}...")
            print()
    
    print("\n🎯 Dashboard Features:")
    print("-" * 20)
    print("✅ Gekleurde metric cards (Portfolio, P&L, Risico)")
    print("✅ Inklapbare secties met chevron icoontjes")
    print("✅ Info tooltips bij hover over (i) icoontjes")
    print("✅ Bot activiteit timeline met status kleuren")
    print("✅ ML model prestaties en signaal kwaliteit")
    print("✅ Markt overzicht en risico management")
    print("✅ Real-time alerts en trading kansen")
    print("✅ Portfolio verdeling en trading statistieken")
    print("✅ HTTPS/SSL beveiliging")
    print("✅ Authenticatie (admin/test123)")
    print("✅ Rate limiting en input validatie")
    
    print("\n🔧 Technische Details:")
    print("-" * 20)
    print("🌐 Framework: Flask (Python)")
    print("🎨 Frontend: Bootstrap 5 + Chart.js")
    print("🔒 Beveiliging: HTTPS, Auth, Rate Limiting")
    print("📊 Data: CSV files van Pi bot")
    print("🔄 Sync: SCP naar Pi via SSH")
    print("📱 Responsive: Mobile-friendly design")
    
    print(f"\n📅 Export gegenereerd: {datetime.now().strftime('%d-%m-%Y om %H:%M:%S')}")
    print("🌐 Volledige export: trading_bot_dashboard_export.html")

if __name__ == "__main__":
    main()
