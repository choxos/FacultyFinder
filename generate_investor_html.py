#!/usr/bin/env python3
"""
FacultyFinder.io Investor Package HTML Generator
Creates a comprehensive HTML investor package that can be printed to PDF
"""

import os
import sys
from datetime import datetime
import markdown
from pathlib import Path

# Document order for the investor package
DOCUMENT_ORDER = [
    '01_Executive_Summary.md',
    '02_Business_Plan.md', 
    '03_Financial_Projections.md',
    '04_Pitch_Deck.md',
    '05_Founder_Profile.md',
    '06_Market_Analysis.md',
    '07_Investment_Memorandum.md'
]

def create_html_header():
    """Create professional HTML header with styling"""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FacultyFinder.io - Investor Package</title>
    <style>
        @media print {
            .page-break { page-break-before: always; }
            .no-print { display: none; }
            * { -webkit-print-color-adjust: exact !important; color-adjust: exact !important; }
        }
        
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: white;
        }
        
        .cover-page {
            text-align: center;
            padding: 100px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: -20px -20px 40px -20px;
            page-break-after: always;
        }
        
        .cover-title {
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .cover-subtitle {
            font-size: 1.8rem;
            margin-bottom: 30px;
            opacity: 0.95;
        }
        
        .cover-info {
            font-size: 1.2rem;
            margin: 15px 0;
            background: rgba(255,255,255,0.1);
            padding: 10px 20px;
            border-radius: 5px;
            display: inline-block;
            backdrop-filter: blur(10px);
        }
        
        .confidential {
            margin-top: 60px;
            font-size: 0.9rem;
            opacity: 0.8;
            border-top: 1px solid rgba(255,255,255,0.3);
            padding-top: 20px;
        }
        
        h1 {
            color: #2c5530;
            border-bottom: 3px solid #4a90e2;
            padding-bottom: 10px;
            margin-top: 40px;
            font-size: 2.2rem;
        }
        
        h2 {
            color: #4a90e2;
            border-bottom: 2px solid #e8e8e8;
            padding-bottom: 8px;
            margin-top: 30px;
            font-size: 1.6rem;
        }
        
        h3 {
            color: #2c5530;
            margin-top: 25px;
            font-size: 1.3rem;
        }
        
        h4 {
            color: #34495e;
            margin-top: 20px;
            font-size: 1.1rem;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 12px 15px;
            text-align: left;
        }
        
        th {
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            font-weight: 600;
            color: #2c3e50;
        }
        
        tbody tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        tbody tr:hover {
            background-color: #e3f2fd;
        }
        
        .highlight {
            background: linear-gradient(135deg, #e7f3ff, #bbdefb);
            padding: 20px;
            border-left: 5px solid #4a90e2;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .document-section {
            margin-top: 50px;
            padding-top: 30px;
            border-top: 3px solid #4a90e2;
        }
        
        .toc {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            margin: 30px 0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .toc ol {
            font-size: 1.1rem;
            line-height: 1.8;
        }
        
        .toc li {
            margin: 10px 0;
            padding: 5px 0;
        }
        
        .toc strong {
            color: #2c5530;
        }
        
        blockquote {
            border-left: 4px solid #4a90e2;
            margin: 20px 0;
            padding: 15px 25px;
            background: #f8f9fa;
            font-style: italic;
            border-radius: 0 8px 8px 0;
        }
        
        code {
            background: #f4f4f4;
            padding: 3px 6px;
            border-radius: 4px;
            font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
            font-size: 0.9em;
        }
        
        pre {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            border-left: 4px solid #4a90e2;
        }
        
        ul li, ol li {
            margin: 8px 0;
        }
        
        ul li::marker {
            color: #4a90e2;
        }
        
        .print-button {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4a90e2;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(74,144,226,0.3);
            transition: all 0.3s ease;
        }
        
        .print-button:hover {
            background: #357abd;
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(74,144,226,0.4);
        }
        
        .financial-highlight {
            background: linear-gradient(135deg, #d4edda, #c3e6cb);
            border: 1px solid #28a745;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }
        
        .risk-item {
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 6px;
            padding: 12px 15px;
            margin: 10px 0;
        }
        
        .investment-summary {
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border: 2px solid #4a90e2;
            border-radius: 10px;
            padding: 25px;
            margin: 25px 0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        @media (max-width: 768px) {
            body { padding: 10px; }
            .cover-title { font-size: 2.5rem; }
            .cover-subtitle { font-size: 1.3rem; }
            h1 { font-size: 1.8rem; }
            h2 { font-size: 1.4rem; }
            table { font-size: 0.9rem; }
            th, td { padding: 8px 10px; }
        }
    </style>
    <script>
        function printPDF() {
            window.print();
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            // Add click handlers for better interactivity
            const tables = document.querySelectorAll('table');
            tables.forEach(table => {
                table.addEventListener('click', function() {
                    this.style.transform = 'scale(1.02)';
                    setTimeout(() => this.style.transform = 'scale(1)', 200);
                });
            });
        });
    </script>
</head>
<body>"""

def create_cover_page():
    """Create professional cover page"""
    current_date = datetime.now().strftime("%B %Y")
    return f"""
    <div class="cover-page">
        <div class="cover-title">FacultyFinder.io</div>
        <div class="cover-subtitle">AI-Powered Academic Intelligence Platform</div>
        <div class="cover-subtitle">📊 INVESTOR PACKAGE 📊</div>
        
        <div style="margin: 50px 0;">
            <div class="cover-info">💰 <strong>Seed Round:</strong> $500,000 CAD</div>
            <div class="cover-info">💎 <strong>Valuation:</strong> $2,500,000 CAD Pre-Money</div>
            <div class="cover-info">📈 <strong>Equity Offered:</strong> 16.7%</div>
            <div class="cover-info">🎓 <strong>Industry:</strong> EdTech / Academic Intelligence</div>
            <div class="cover-info">🚀 <strong>Expected ROI:</strong> 12-24x in 5-7 years</div>
        </div>
        
        <div style="margin-top: 80px;">
            <div class="cover-info"><strong>📋 Prepared for Qualified Investors</strong></div>
            <div class="cover-info">📅 {current_date}</div>
            <div class="cover-info">🔒 CONFIDENTIAL</div>
        </div>
        
        <div class="confidential">
            This document contains confidential and proprietary information.<br/>
            Distribution is restricted to potential investors only.<br/>
            <strong>© 2024 FacultyFinder.io - All Rights Reserved</strong>
        </div>
    </div>
    """

def create_table_of_contents():
    """Create comprehensive table of contents"""
    return """
    <div class="toc page-break">
        <h1>📋 Table of Contents</h1>
        <ol>
            <li><strong>Executive Summary</strong> - One-page investment overview and key highlights</li>
            <li><strong>Business Plan</strong> - Comprehensive business strategy, market analysis, and competitive positioning</li>
            <li><strong>Financial Projections</strong> - 5-year financial forecasts, revenue models, and unit economics</li>
            <li><strong>Pitch Deck</strong> - Visual presentation materials and key value propositions</li>
            <li><strong>Founder Profile</strong> - Leadership team background and qualifications</li>
            <li><strong>Market Analysis</strong> - Industry landscape, competitive analysis, and market opportunity</li>
            <li><strong>Investment Memorandum</strong> - Detailed investment terms, risks, and opportunity overview</li>
        </ol>
        
        <div class="highlight">
            <strong>📊 Package Summary:</strong> This comprehensive investor package contains over 100 pages 
            of professional investment materials for FacultyFinder.io's $500,000 CAD seed round. 
            The package includes detailed market analysis, financial projections, and business strategy 
            for the AI-powered academic intelligence platform targeting the $2.8B academic recruitment market.
        </div>
        
        <div class="investment-summary">
            <h3>💡 Quick Investment Overview</h3>
            <p><strong>FacultyFinder.io</strong> is the world's first AI-powered academic intelligence platform 
            combining multiple AI services (Claude, ChatGPT, Gemini, Grok) with automated research data 
            to revolutionize how graduate students, researchers, and institutions discover and connect 
            with faculty worldwide.</p>
            
            <p><strong>🎯 Key Investment Highlights:</strong></p>
            <ul>
                <li>✅ Live production platform with proven AI integration</li>
                <li>✅ $2.8B addressable market growing at 12.3% annually</li>
                <li>✅ PhD founder with academic credibility and technical execution</li>
                <li>✅ Multiple validated revenue streams with strong unit economics</li>
                <li>✅ Clear path to profitability and strategic exit opportunities</li>
            </ul>
        </div>
    </div>
    """

def markdown_to_html(markdown_content):
    """Convert markdown to HTML with extensions"""
    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'toc', 'attr_list'])
    return md.convert(markdown_content)

def process_document(doc_path, doc_number):
    """Process individual markdown document"""
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Convert to HTML
        html_content = markdown_to_html(markdown_content)
        
        # Add document section with page break
        doc_name = os.path.basename(doc_path).replace('.md', '').replace('_', ' ').title()
        doc_html = f'''
        <div class="document-section page-break">
            <h1>{doc_number}. {doc_name}</h1>
            {html_content}
        </div>
        '''
        
        return doc_html
        
    except Exception as e:
        print(f"Error processing {doc_path}: {e}")
        return f'''
        <div class="document-section page-break">
            <h1>Error Processing Document</h1>
            <p>Could not process {doc_path}: {e}</p>
        </div>
        '''

def generate_html():
    """Generate comprehensive investor package HTML"""
    print("🚀 Generating FacultyFinder.io Investor Package HTML...")
    
    # Check if startup_investor_package directory exists
    package_dir = Path('startup_investor_package')
    if not package_dir.exists():
        print("❌ startup_investor_package directory not found!")
        return False
    
    # Start building HTML content
    html_content = create_html_header()
    
    # Add print button
    html_content += '<button class="print-button no-print" onclick="printPDF()">🖨️ Print to PDF</button>'
    
    # Add cover page
    html_content += create_cover_page()
    
    # Add table of contents
    html_content += create_table_of_contents()
    
    # Process each document in order
    for idx, doc_name in enumerate(DOCUMENT_ORDER, 1):
        doc_path = package_dir / doc_name
        if doc_path.exists():
            print(f"📄 Processing {doc_name}...")
            html_content += process_document(doc_path, idx)
        else:
            print(f"⚠️ Warning: {doc_name} not found, skipping...")
    
    # Add footer
    html_content += f"""
    <div class="document-section page-break" style="text-align: center; padding: 50px 0;">
        <h2>Thank You for Your Interest</h2>
        <p><strong>FacultyFinder.io</strong> - Revolutionizing Academic Intelligence with AI</p>
        <p>For questions or to schedule a demo, please contact:</p>
        <div class="highlight">
            📧 <strong>ahmad@facultyfinder.io</strong><br/>
            🌐 <strong>https://facultyfinder.io</strong><br/>
            📱 Available for investor calls and platform demonstrations
        </div>
        <p style="margin-top: 30px; font-size: 0.9rem; color: #666;">
            Generated on {datetime.now().strftime("%B %d, %Y")} | © 2024 FacultyFinder.io
        </p>
    </div>
    """
    
    # Close HTML
    html_content += "</body></html>"
    
    # Write to file
    output_path = "FacultyFinder_Investor_Package.html"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Success! Generated: {output_path}")
        print(f"📊 File size: {os.path.getsize(output_path) / 1024:.1f} KB")
        print(f"🔗 Full path: {os.path.abspath(output_path)}")
        print("\n💡 To convert to PDF:")
        print("   1. Open the HTML file in your browser")
        print("   2. Click 'Print to PDF' button or use Cmd+P (Mac) / Ctrl+P (Windows)")
        print("   3. Select 'Save as PDF' as destination")
        print("   4. Choose appropriate print settings for best results")
        
        return True
        
    except Exception as e:
        print(f"❌ HTML generation failed: {e}")
        return False

def main():
    """Main function"""
    print("🎯 FacultyFinder.io Investor Package HTML Generator")
    print("=" * 60)
    
    # Check dependencies
    try:
        import markdown
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("💡 Install with: pip install markdown")
        return False
    
    # Generate HTML
    success = generate_html()
    
    if success:
        print("\n🎉 Investor Package HTML Generated Successfully!")
        print("📧 Ready to convert to PDF and send to potential investors")
        print("💼 Professional 100+ page investment package")
        print("🖨️ Click the 'Print to PDF' button in the HTML file to generate PDF")
    else:
        print("\n❌ HTML generation failed")
    
    return success

if __name__ == "__main__":
    main()
