#!/usr/bin/env python3
"""
Simple HTTP server for the AI Image Categorizer frontend
Serves the frontend files and provides API endpoints to access images and JSON data
"""

import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import urllib.parse

# Get the absolute path to the script directory
SCRIPT_DIR = Path(__file__).resolve().parent

class ImageGalleryHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from (root directory)
        super().__init__(*args, directory=str(SCRIPT_DIR), **kwargs)
    
    def log_error(self, format, *args):
        """Suppress connection reset errors - they're harmless"""
        # Suppress ConnectionAbortedError and BrokenPipeError messages
        if args and len(args) > 0:
            if 'ConnectionAbortedError' in str(args) or 'BrokenPipeError' in str(args):
                return
        super().log_error(format, *args)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        # Parse the URL
        parsed_path = urllib.parse.urlparse(self.path)
        
        # Ignore favicon requests
        if parsed_path.path == '/favicon.ico':
            self.send_response(204)  # No content
            self.end_headers()
            return
        
        # API endpoint to get all images with their metadata
        if parsed_path.path == '/api/images':
            # Parse query parameters for pagination
            query_params = urllib.parse.parse_qs(parsed_path.query)
            page = int(query_params.get('page', ['1'])[0])
            self.serve_images_api(page)
            return
        
        # Root path - serve index.html
        if parsed_path.path == '/':
            self.path = '/frontend/index.html'
        
        # Let the parent class handle file serving
        super().do_GET()
    
    def serve_images_api(self, page=1):
        """Serve JSON data with paginated images and their metadata"""
        IMAGES_PER_PAGE = 10
        
        try:
            output_folder = SCRIPT_DIR / 'output'
            
            if not output_folder.exists():
                print(f"⚠️  Output folder not found at: {output_folder}")
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'images': [],
                    'page': page,
                    'total_images': 0,
                    'total_pages': 0,
                    'error': f'Output folder not found'
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            all_images = []
            
            # Find all JSON files in output folder
            for json_file in sorted(output_folder.glob('*.json')):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        
                    # Check if corresponding image exists
                    image_filename = metadata.get('filename', '')
                    if image_filename:
                        image_path = output_folder / image_filename
                        if image_path.exists():
                            all_images.append(metadata)
                        else:
                            print(f"⚠️  Image not found: {image_filename}")
                    else:
                        print(f"⚠️  No filename in metadata: {json_file.name}")
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON in {json_file.name}: {e}")
                    continue
                except Exception as e:
                    print(f"❌ Error reading {json_file.name}: {e}")
                    continue
            
            # Sort by filename
            all_images.sort(key=lambda x: x.get('filename', ''))
            
            total_images = len(all_images)
            total_pages = (total_images + IMAGES_PER_PAGE - 1) // IMAGES_PER_PAGE
            
            # Validate page number
            if page < 1:
                page = 1
            elif page > total_pages and total_pages > 0:
                page = total_pages
            
            # Get images for this page
            start_idx = (page - 1) * IMAGES_PER_PAGE
            end_idx = start_idx + IMAGES_PER_PAGE
            page_images = all_images[start_idx:end_idx]
            
            print(f"✓ Page {page}/{total_pages}: Loaded {len(page_images)} images (Total: {total_images})")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'images': page_images,
                'page': page,
                'total_images': total_images,
                'total_pages': total_pages,
                'images_per_page': IMAGES_PER_PAGE
            }
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"❌ API Error: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'images': [], 'page': page, 'total_images': 0, 'total_pages': 0, 'error': str(e)}
            self.wfile.write(json.dumps(response).encode())

def run_server(port=8000):
    """Start the HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, ImageGalleryHandler)
    
    print("=" * 60)
    print(f"🌐 AI Image Categorizer - Frontend Server")
    print("=" * 60)
    print(f"\n✓ Server running on http://localhost:{port}")
    print(f"✓ Open your browser and visit: http://localhost:{port}")
    print(f"\nPress Ctrl+C to stop the server\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped.")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
