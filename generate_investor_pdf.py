#!/usr/bin/env python3
"""
FacultyFinder.io Investor Package PDF Generator
Converts all investor package markdown documents into a comprehensive PDF
"""

import os
import sys
from datetime import datetime
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
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
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>FacultyFinder.io - Investor Package</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: white;
            }
            h1 {
                color: #2c5530;
                border-bottom: 3px solid #4a90e2;
                padding-bottom: 10px;
                margin-top: 40px;
            }
            h2 {
                color: #4a90e2;
                border-bottom: 2px solid #e8e8e8;
                padding-bottom: 5px;
            }
            h3 {
                color: #2c5530;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }
            th {
                background-color: #f8f9fa;
                font-weight: bold;
            }
            .highlight {
                background-color: #e7f3ff;
                padding: 15px;
                border-left: 4px solid #4a90e2;
                margin: 15px 0;
            }
            .document-separator {
                page-break-before: always;
                border-top: 5px solid #4a90e2;
                margin-top: 40px;
                padding-top: 20px;
            }
            .cover-page {
                text-align: center;
                padding: 100px 0;
                page-break-after: always;
            }
            .cover-title {
                font-size: 48px;
                color: #2c5530;
                margin-bottom: 20px;
                font-weight: bold;
            }
            .cover-subtitle {
                font-size: 24px;
                color: #4a90e2;
                margin-bottom: 40px;
            }
            .cover-info {
                font-size: 18px;
                color: #666;
                margin: 10px 0;
            }
            blockquote {
                border-left: 4px solid #4a90e2;
                margin: 0;
                padding: 10px 20px;
                background-color: #f8f9fa;
                font-style: italic;
            }
            code {
                background-color: #f4f4f4;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }
            ul li {
                margin: 5px 0;
            }
            .financial-table {
                background-color: #f8f9fa;
            }
            .risk-section {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 15px;
                margin: 15px 0;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
    """

def create_cover_page():
    """Create professional cover page"""
    current_date = datetime.now().strftime("%B %Y")
    return f"""
    <div class="cover-page">
        <div class="cover-title">FacultyFinder.io</div>
        <div class="cover-subtitle">AI-Powered Academic Intelligence Platform</div>
        <div class="cover-subtitle">INVESTOR PACKAGE</div>
        <div style="margin: 60px 0;">
            <div class="cover-info"><strong>Seed Round:</strong> $500,000 CAD</div>
            <div class="cover-info"><strong>Valuation:</strong> $2,500,000 CAD Pre-Money</div>
            <div class="cover-info"><strong>Equity Offered:</strong> 16.7%</div>
            <div class="cover-info"><strong>Industry:</strong> EdTech / Academic Intelligence</div>
        </div>
        <div style="margin-top: 80px;">
            <div class="cover-info"><strong>Prepared for Qualified Investors</strong></div>
            <div class="cover-info">{current_date}</div>
            <div class="cover-info">CONFIDENTIAL</div>
        </div>
        <div style="margin-top: 60px; font-size: 14px; color: #888;">
            This document contains confidential and proprietary information.<br/>
            Distribution is restricted to potential investors only.
        </div>
    </div>
    """

def markdown_to_html(markdown_content):
    """Convert markdown to HTML with extensions"""
    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'toc'])
    return md.convert(markdown_content)

def process_document(doc_path):
    """Process individual markdown document"""
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Convert to HTML
        html_content = markdown_to_html(markdown_content)
        
        # Add document separator
        doc_name = os.path.basename(doc_path).replace('.md', '').replace('_', ' ').title()
        doc_html = f'<div class="document-separator"><h1>{doc_name}</h1>{html_content}</div>'
        
        return doc_html
        
    except Exception as e:
        print(f"Error processing {doc_path}: {e}")
        return f"<div class='document-separator'><h1>Error</h1><p>Could not process {doc_path}</p></div>"

def generate_pdf():
    """Generate comprehensive investor package PDF"""
    print("🚀 Generating FacultyFinder.io Investor Package PDF...")
    
    # Check if startup_investor_package directory exists
    package_dir = Path('startup_investor_package')
    if not package_dir.exists():
        print("❌ startup_investor_package directory not found!")
        return False
    
    # Start building HTML content
    html_content = create_html_header()
    html_content += create_cover_page()
    
    # Add table of contents
    html_content += """
    <div class="document-separator">
        <h1>Table of Contents</h1>
        <ol>
            <li><strong>Executive Summary</strong> - One-page investment overview</li>
            <li><strong>Business Plan</strong> - Comprehensive business strategy and analysis</li>
            <li><strong>Financial Projections</strong> - 5-year financial forecasts and models</li>
            <li><strong>Pitch Deck</strong> - Visual presentation materials</li>
            <li><strong>Founder Profile</strong> - Leadership team background</li>
            <li><strong>Market Analysis</strong> - Industry and competitive landscape</li>
            <li><strong>Investment Memorandum</strong> - Detailed investment terms and opportunity</li>
        </ol>
        <div class="highlight">
            <strong>Package Summary:</strong> This comprehensive investor package contains over 100 pages 
            of professional investment materials for FacultyFinder.io's $500,000 CAD seed round. 
            The package includes detailed market analysis, financial projections, and business strategy 
            for the AI-powered academic intelligence platform.
        </div>
    </div>
    """
    
    # Process each document in order
    for doc_name in DOCUMENT_ORDER:
        doc_path = package_dir / doc_name
        if doc_path.exists():
            print(f"📄 Processing {doc_name}...")
            html_content += process_document(doc_path)
        else:
            print(f"⚠️ Warning: {doc_name} not found, skipping...")
    
    # Close HTML
    html_content += "</body></html>"
    
    # Generate PDF
    output_path = "FacultyFinder_Investor_Package.pdf"
    
    try:
        # Configure CSS for PDF layout
        css_string = """
        @page {
            size: A4;
            margin: 0.75in;
        }
        @media print {
            .document-separator {
                page-break-before: always;
            }
            .cover-page {
                page-break-after: always;
            }
        }
        """
        
        print("📝 Converting to PDF...")
        
        # Create font configuration
        font_config = FontConfiguration()
        
        # Generate PDF using weasyprint
        html_doc = HTML(string=html_content)
        css_doc = CSS(string=css_string, font_config=font_config)
        html_doc.write_pdf(output_path, stylesheets=[css_doc], font_config=font_config)
        
        print(f"✅ Success! Generated: {output_path}")
        print(f"📊 File size: {os.path.getsize(output_path) / 1024 / 1024:.1f} MB")
        print(f"🔗 Full path: {os.path.abspath(output_path)}")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        print("💡 Make sure you have weasyprint installed:")
        print("   pip install weasyprint")
        return False

def main():
    """Main function"""
    print("🎯 FacultyFinder.io Investor Package PDF Generator")
    print("=" * 50)
    
    # Check dependencies
    try:
        from weasyprint import HTML, CSS
        import markdown
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("💡 Install with: pip install weasyprint markdown")
        return False
    
    # Generate PDF
    success = generate_pdf()
    
    if success:
        print("\n🎉 Investor Package PDF Generated Successfully!")
        print("📧 Ready to send to potential investors")
        print("💼 Professional 100+ page investment package")
    else:
        print("\n❌ PDF generation failed")
    
    return success

if __name__ == "__main__":
    main()
