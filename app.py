import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from flask import Flask, request, render_template, jsonify, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import ebooklib
from ebooklib import epub
from pypdf import PdfReader
import openai
from dotenv import load_dotenv
from functools import wraps
import time
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Validate required environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY environment variable is not set")
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Initialize Flask app with security headers
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for testing
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Security configurations
app.config['UPLOAD_FOLDER'] = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads'))
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'epub', 'pdf'}
app.config['RATE_LIMIT'] = {'requests': 100, 'window': 3600}  # 100 requests per hour

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Create uploads directory if it doesn't exist
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)

# Helper functions
def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Rate limiting
request_history: List[float] = []

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        now = time.time()
        request_history[:] = [t for t in request_history if now - t < app.config['RATE_LIMIT']['window']]
        if len(request_history) >= app.config['RATE_LIMIT']['requests']:
            abort(429, description="Too many requests")
        request_history.append(now)
        return f(*args, **kwargs)
    return decorated_function

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src * 'unsafe-inline' 'unsafe-eval'; img-src * data:"
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

def extract_chapters_epub(file_path: str) -> List[Dict[str, str]]:
    """Extract chapters from an EPUB file using the TOC when available."""
    try:
        book = epub.read_epub(file_path)
        chapters = []

        # Build a mapping from document href (filename) to the item
        doc_items = {
            item.get_name(): item
            for item in book.get_items()
            if item.get_type() == ebooklib.ITEM_DOCUMENT
        }

        def get_chapter_title(content: bytes, default: str) -> str:
            """Try to extract a chapter title from HTML using BeautifulSoup."""
            try:
                soup = BeautifulSoup(content, 'html.parser')
                # Look for an <h1> first, then fallback to <title>
                header = soup.find('h1') or soup.find('title')
                if header and header.string:
                    return header.string.strip()
            except Exception as e:
                logger.warning(f"Error parsing HTML for chapter title: {e}")
            return default

        def process_toc(toc_entries):
            # Process each toc entry (which could be a Link or a tuple for nested chapters)
            for entry in toc_entries:
                if isinstance(entry, tuple) and len(entry) == 2:
                    link, sub_entries = entry
                else:
                    link, sub_entries = entry, None

                chapter_title = link.title  # The title from TOC should be preferred
                href = link.href  # This is the reference for the chapter

                # Look up the document item that matches the href
                doc_item = doc_items.get(href)
                content = b""
                if doc_item:
                    try:
                        content = doc_item.get_content()
                    except UnicodeDecodeError as e:
                        logger.warning(f"Error decoding chapter content: {e}")

                # If no title present in the TOC (or if it seems to be a file name), try to extract from content
                if not chapter_title or chapter_title.lower().endswith(('.xhtml', '.html', '.htm')):
                    chapter_title = get_chapter_title(content, default=href)

                chapters.append({
                    'title': chapter_title,
                    'content': content.decode('utf-8', errors='ignore')
                })

                # If there are sub-chapters, process them recursively
                if sub_entries:
                    process_toc(sub_entries)

        # Process the TOC if it exists.
        if book.toc:
            process_toc(book.toc)
        else:
            # Fallback: if no TOC available, use all document items
            for name, item in doc_items.items():
                try:
                    content = item.get_content()
                    chapter_title = get_chapter_title(content, default=name)
                    chapters.append({
                        'title': chapter_title,
                        'content': content.decode('utf-8', errors='ignore')
                    })
                except Exception as e:
                    logger.warning(f"Error processing document item {name}: {e}")
                    continue

        return chapters
    except Exception as e:
        logger.warning(f"Error processing EPUB file: {e}")
        raise ValueError("Failed to process EPUB file")

def extract_chapters_pdf(file_path: str) -> List[Dict[str, str]]:
    """Extract pages from a PDF file."""
    try:
        reader = PdfReader(file_path)
        chapters = []
        
        for i in range(len(reader.pages)):
            try:
                content = reader.pages[i].extract_text()
                if content.strip():  # Only include non-empty pages
                    chapters.append({
                        'title': f'Page {i + 1}',
                        'content': content
                    })
            except Exception as e:
                logger.warning(f"Error extracting text from page {i + 1}: {e}")
                continue
        
        return chapters
    except Exception as e:
        logger.warning(f"Error processing PDF file: {e}")
        raise ValueError("Failed to process PDF file")

def get_chapter_summary(content: str) -> str:
    """Generate a summary of the chapter content using OpenAI's API."""
    if not content or len(content.strip()) < 10:
        raise ValueError("Content is too short to summarize")
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes book chapters."},
                {"role": "user", "content": f"Please provide a brief summary of the following chapter content: {content[:4000]}"}
            ],
            max_tokens=500,
            temperature=0.7,
            presence_penalty=0.0,
            frequency_penalty=0.0
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.warning(f"Error generating summary: {e}")
        raise ValueError("Failed to generate summary")

@app.route('/')
@rate_limit
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
@rate_limit
def upload_file():
    """Handle file upload and chapter extraction."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only EPUB and PDF files are allowed'}), 400
    
    try:
        filename = secure_filename(file.filename)
        name_without_ext, _ = os.path.splitext(filename)
        # Replace underscores with spaces.
        clean_book_name = name_without_ext.replace("_", " ")
        print(f"name_without_ext: {name_without_ext}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save file securely
        file.save(filepath)
        
        try:
            # Process file based on type
            if filename.lower().endswith('.epub'):
                chapters = extract_chapters_epub(filepath)
            else:
                chapters = extract_chapters_pdf(filepath)
            
            # Clean up the uploaded file
            os.remove(filepath)
            
            if not chapters:
                return jsonify({'error': 'No content found in file'}), 400

            # Return the chapters along with the book name (without extension)
            return jsonify({'chapters': chapters, 'book_name': clean_book_name})
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.warning(f"Error processing file: {e}")
            return jsonify({'error': 'Internal server error'}), 500
        finally:
            # Ensure file is cleaned up even if processing fails
            if os.path.exists(filepath):
                os.remove(filepath)
                
    except Exception as e:
        logger.warning(f"Error handling file upload: {e}")
        return jsonify({'error': 'Failed to process upload'}), 500

@app.route('/summarize', methods=['POST'])
@rate_limit
def summarize():
    """Generate a summary of the provided content."""
    try:
        content = request.json.get('content')
        if not content:
            return jsonify({'error': 'No content provided'}), 400
        
        summary = get_chapter_summary(content)
        return jsonify({'summary': summary})
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.warning(f"Error generating summary: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def create_app(testing=False):
    """Create and configure the Flask application."""
    if testing:
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
    return app

# Constants with security documentation
LOCALHOST = '127.0.0.1'
ALL_INTERFACES = '0.0.0.0'  # nosec B104 # Required for external access, protected by explicit configuration and security measures

def get_server_config() -> tuple[str, int, bool]:
    """
    Get server configuration from environment variables.
    
    Returns:
        tuple: (host, port, debug_mode)
        
    Security Note:
        - In development: Binds to localhost only
        - In production: Binds to localhost by default
        - External access requires explicit configuration
        - Debug mode only allowed with localhost binding
        - Additional security measures in place:
            * Rate limiting
            * Security headers
            * File upload restrictions
            * Input validation
    """
    # Get environment variables with secure defaults
    env = os.getenv('FLASK_ENV', 'production')
    port = int(os.getenv('PORT', '50869'))
    allow_external = os.getenv('ALLOW_ALL_INTERFACES', '').lower() == 'true'
    
    # In development, always bind to localhost for security
    if env == 'development':
        host = LOCALHOST
        debug = True
        # Prevent debug mode with external access
        if allow_external:
            logger.warning("Debug mode not allowed with external access. Using production configuration.")
            debug = False
    else:
        # In production, use secure defaults
        host = LOCALHOST
        debug = False
        
    # Allow external access only when explicitly configured
    if allow_external:
        if host == LOCALHOST:  # Only log when actually changing from localhost
            logger.warning("Security Warning: Binding to all network interfaces!")
            logger.warning("Ensure proper security measures are in place:")
            logger.warning("- Network firewall rules")
            logger.warning("- Rate limiting enabled")
            logger.warning("- Security headers configured")
            logger.warning("- File upload restrictions active")
        host = ALL_INTERFACES  # nosec B104 # Protected by ALLOW_ALL_INTERFACES check and security measures
    
    return host, port, debug

if __name__ == '__main__':
    try:
        logger.info("Starting server...")
        
        # Get secure server configuration
        host, port, debug = get_server_config()
        
        # Additional security checks
        if debug:
            if not host.startswith('127.0.0.1'):
                raise ValueError("Debug mode can only be used with localhost")
            logger.warning("Running in debug mode - NOT FOR PRODUCTION USE")
        
        # Configure app security
        app.config['DEBUG'] = debug
        app.config['TESTING'] = False
        app.config['PROPAGATE_EXCEPTIONS'] = not debug
        
        # Start server with secure configuration
        logger.info(f"Server starting on {host}:{port} (debug={debug})")
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        logger.warning(f"Error starting server: {e}")
        raise