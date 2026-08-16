#!/usr/bin/env python3
"""
1995 Ford Truck Service Manuals - Web Search Interface
Human-AI Collaboration Demo: Rosco @ HephzibahForge + DeepSeek AI
"""
import json
import os
from flask import Flask, request, render_template

# Use the existing search class
import sys
from app.search.search_engine import FixedSearch

# Set up paths
BASE_DIR = "/media/data/webapps/f250_ai_manual"
PDF_DIR = os.path.join(BASE_DIR, "data/manuals")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Initialize Flask with explicit paths
app = Flask(__name__, 
            template_folder=TEMPLATE_DIR,
            static_folder=STATIC_DIR)
search_engine = FixedSearch()


@app.route('/')
def cover_page():
    """Serve the cover/presentation page."""
    # Get list of manual files for display (optional - could be hardcoded)
    manual_files = []
    try:
        manual_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
    except Exception as e:
        print(f"Error reading manual directory: {e}")
    
    return render_template('cover.html', manuals=manual_files)


@app.route('/search')
def search_results():
    """Handle search requests and display results."""
    query = request.args.get('q', '').strip()
    results = []
    
    if query:
        # Use the existing weighted_search method
        raw_results = search_engine.weighted_search(query)
        # Format results for display
        for item in raw_results[:50]:  # Limit to 50 for performance
            manual_name = item.get('manual', 'Unknown')
            page_num = item.get('page', 1)
            results.append({
                'manual_name': manual_name,
                'page_num': page_num,
                'context_snippet': item.get('context', item.get('full_text', '')[:400]),  # Increased to 400 chars
                'pdf_filename': f"{manual_name}.pdf",
                'page_anchor': page_num if isinstance(page_num, int) else 1
            })
    
    return render_template('search_results.html', query=query, results=results)


@app.route('/serve_pdf/<path:filename>')
def serve_pdf(filename):
    """Serve PDF files directly."""
    from flask import send_from_directory
    return send_from_directory(PDF_DIR, filename)


@app.route('/view_pdf/<path:filename>/<int:page>')
def view_pdf(filename, page):
    """Redirect to PDF with page anchor."""
    import urllib.parse
    # URL-encode the filename for safety
    encoded_filename = urllib.parse.quote(filename)
    # Create URL with page anchor (browser PDF viewer should handle #page=N)
    pdf_url = f"/serve_pdf/{encoded_filename}#page={page}"
    return f'''
    <html>
    <head><meta http-equiv="refresh" content="0; url={pdf_url}"></head>
    <body>
        <p>Opening PDF... If not redirected, <a href="{pdf_url}">click here</a>.</p>
    </body>
    </html>
    '''


if __name__ == '__main__':
    print("Starting 1995 Ford Truck Service Manuals Web Search...")
    print("Data loaded:", "Yes" if search_engine.data else "No")
    print("Template folder:", TEMPLATE_DIR)
    print("Static folder:", STATIC_DIR)
    print("Access the interface at: http://localhost:5050")
    print("Press Ctrl+C to stop")
    app.run(host='0.0.0.0', port=5050, debug=False)

