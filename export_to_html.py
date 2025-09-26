#!/usr/bin/env python3
"""
Trading Bot Dashboard - HTML Export Tool
Export complete repository to HTML for review
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import mimetypes

def get_file_content(file_path):
    """Get file content with proper encoding handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except:
            return f"<em>Binary file - cannot display</em>"

def get_file_icon(file_path):
    """Get appropriate icon for file type"""
    ext = Path(file_path).suffix.lower()
    icons = {
        '.py': '🐍',
        '.js': '📜',
        '.html': '🌐',
        '.css': '🎨',
        '.md': '📝',
        '.txt': '📄',
        '.sh': '⚙️',
        '.json': '📋',
        '.csv': '📊',
        '.yml': '⚙️',
        '.yaml': '⚙️',
        '.gitignore': '🚫',
        '.env': '🔐',
        '.log': '📋'
    }
    return icons.get(ext, '📁')

def get_file_size(file_path):
    """Get human readable file size"""
    try:
        size = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    except:
        return "Unknown"

def should_include_file(file_path, include_binary=False):
    """Check if file should be included in export"""
    # Skip certain files
    skip_patterns = [
        '__pycache__',
        '.git',
        '.DS_Store',
        'node_modules',
        '.env',
        '*.pyc',
        '*.log'
    ]
    
    file_path_str = str(file_path)
    for pattern in skip_patterns:
        if pattern in file_path_str:
            return False
    
    # Check if binary file
    if not include_binary:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)  # Try to read first 1KB
        except:
            return False
    
    return True

def generate_html_export():
    """Generate complete HTML export of repository"""
    
    # Get repository info
    repo_path = Path.cwd()
    repo_name = repo_path.name
    
    # Get all files
    all_files = []
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            file_path = Path(root) / file
            if should_include_file(file_path):
                all_files.append(file_path)
    
    # Sort files by type and name
    all_files.sort(key=lambda x: (x.suffix, x.name))
    
    # Generate HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Bot Dashboard - Repository Export</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.8;
        }}
        .toc {{
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #dee2e6;
        }}
        .toc h2 {{
            margin: 0 0 15px 0;
            color: #495057;
        }}
        .toc-list {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 10px;
        }}
        .toc-item {{
            padding: 8px 12px;
            background: white;
            border-radius: 4px;
            border-left: 3px solid #007bff;
            text-decoration: none;
            color: #495057;
            transition: all 0.2s;
        }}
        .toc-item:hover {{
            background: #e9ecef;
            transform: translateX(2px);
        }}
        .file-section {{
            margin: 40px 0;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
        }}
        .file-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .file-icon {{
            font-size: 1.5em;
        }}
        .file-info {{
            flex: 1;
        }}
        .file-name {{
            font-weight: bold;
            color: #495057;
            margin: 0;
        }}
        .file-meta {{
            font-size: 0.9em;
            color: #6c757d;
            margin: 5px 0 0 0;
        }}
        .file-content {{
            background: #f8f9fa;
            padding: 20px;
            overflow-x: auto;
        }}
        .code-block {{
            background: #2d3748;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 6px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 14px;
            line-height: 1.5;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .text-content {{
            background: white;
            padding: 20px;
            border-radius: 6px;
            border: 1px solid #e2e8f0;
        }}
        .footer {{
            background: #495057;
            color: white;
            padding: 20px;
            text-align: center;
            margin-top: 40px;
        }}
        .highlight {{
            background: #fff3cd;
            padding: 2px 4px;
            border-radius: 3px;
        }}
        @media (max-width: 768px) {{
            .stats {{
                flex-direction: column;
                gap: 15px;
            }}
            .toc-list {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Trading Bot Dashboard</h1>
            <p>Complete Repository Export</p>
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">{len(all_files)}</div>
                    <div class="stat-label">Bestanden</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{sum(1 for f in all_files if f.suffix == '.py')}</div>
                    <div class="stat-label">Python</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{sum(1 for f in all_files if f.suffix in ['.js', '.html', '.css'])}</div>
                    <div class="stat-label">Web</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{datetime.now().strftime('%d-%m-%Y')}</div>
                    <div class="stat-label">Export Datum</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{datetime.now().strftime('%H:%M:%S')}</div>
                    <div class="stat-label">Export Tijd</div>
                </div>
            </div>
        </div>
        
        <div class="toc">
            <h2>📋 Inhoudsopgave</h2>
            <div class="toc-list">
"""
    
    # Add table of contents
    for file_path in all_files:
        relative_path = file_path.relative_to(repo_path)
        file_id = str(relative_path).replace('/', '_').replace('.', '_')
        html_content += f"""
                <a href="#{file_id}" class="toc-item">
                    {get_file_icon(file_path)} {relative_path}
                </a>
"""
    
    html_content += """
            </div>
        </div>
        
        <div class="file-sections">
"""
    
    # Add file contents
    for file_path in all_files:
        relative_path = file_path.relative_to(repo_path)
        file_id = str(relative_path).replace('/', '_').replace('.', '_')
        
        try:
            content = get_file_content(file_path)
            file_size = get_file_size(file_path)
            
            # Determine if it's code
            is_code = file_path.suffix in ['.py', '.js', '.html', '.css', '.sh', '.json', '.yml', '.yaml']
            
            html_content += f"""
            <div class="file-section" id="{file_id}">
                <div class="file-header">
                    <span class="file-icon">{get_file_icon(file_path)}</span>
                    <div class="file-info">
                        <h3 class="file-name">{relative_path}</h3>
                        <p class="file-meta">Grootte: {file_size} | Type: {file_path.suffix or 'Geen extensie'}</p>
                    </div>
                </div>
                <div class="file-content">
"""
            
            if is_code:
                html_content += f'<div class="code-block">{content}</div>'
            else:
                html_content += f'<div class="text-content">{content}</div>'
            
            html_content += """
                </div>
            </div>
"""
            
        except Exception as e:
            html_content += f"""
            <div class="file-section" id="{file_id}">
                <div class="file-header">
                    <span class="file-icon">{get_file_icon(file_path)}</span>
                    <div class="file-info">
                        <h3 class="file-name">{relative_path}</h3>
                        <p class="file-meta">Fout bij lezen: {str(e)}</p>
                    </div>
                </div>
            </div>
"""
    
    html_content += f"""
        </div>
        
        <div class="footer">
            <p>🤖 Trading Bot Dashboard - Repository Export</p>
            <p>Gegenereerd op {datetime.now().strftime('%d-%m-%Y om %H:%M:%S')}</p>
            <p>Voor review en feedback</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html_content

def main():
    """Main function"""
    print("🚀 Trading Bot Dashboard - HTML Export Tool")
    print("=" * 50)
    
    try:
        # Generate HTML
        print("📝 Genereren van HTML export...")
        html_content = generate_html_export()
        
        # Write to file
        output_file = "trading_bot_dashboard_export.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML export succesvol gegenereerd: {output_file}")
        print(f"📊 Bestand grootte: {get_file_size(output_file)}")
        print(f"🌐 Open het bestand in je browser om te bekijken")
        
        # Get file count by type
        py_files = sum(1 for f in Path.cwd().rglob('*.py') if should_include_file(f))
        js_files = sum(1 for f in Path.cwd().rglob('*.js') if should_include_file(f))
        html_files = sum(1 for f in Path.cwd().rglob('*.html') if should_include_file(f))
        css_files = sum(1 for f in Path.cwd().rglob('*.css') if should_include_file(f))
        
        print("\n📈 Statistieken:")
        print(f"   🐍 Python bestanden: {py_files}")
        print(f"   📜 JavaScript bestanden: {js_files}")
        print(f"   🌐 HTML bestanden: {html_files}")
        print(f"   🎨 CSS bestanden: {css_files}")
        
    except Exception as e:
        print(f"❌ Fout bij genereren van HTML export: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
