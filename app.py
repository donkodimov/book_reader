import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from flask import Flask, request, render_template, jsonify, abort
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import ebooklib
from ebooklib import epub
from PyPDF2 import PdfReader
import openai
from dotenv import load_dotenv
from functools import wraps
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Validate required environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable is not set")
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Initialize Flask app with security headers
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Security configurations
app.config['UPLOAD_FOLDER'] = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads'))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
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
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

def extract_chapters_epub(file_path: str) -> List[Dict[str, str]]:
    """Extract chapters from an EPUB file."""
    try:
        book = epub.read_epub(file_path)
        chapters = []
        
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                try:
                    content = item.get_content().decode('utf-8')
                    chapters.append({
                        'title': item.get_name(),
                        'content': content
                    })
                except UnicodeDecodeError as e:
                    logger.error(f"Error decoding chapter content: {e}")
                    continue
        
        return chapters
    except Exception as e:
        logger.error(f"Error processing EPUB file: {e}")
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
                logger.error(f"Error extracting text from page {i + 1}: {e}")
                continue
        
        return chapters
    except Exception as e:
        logger.error(f"Error processing PDF file: {e}")
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
        logger.error(f"Error generating summary: {e}")
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
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save file securely
        file.save(filepath)
        
        try:
            # Process file based on type
            if filename.endswith('.epub'):
                chapters = extract_chapters_epub(filepath)
            else:
                chapters = extract_chapters_pdf(filepath)
            
            # Clean up the uploaded file
            os.remove(filepath)
            
            if not chapters:
                return jsonify({'error': 'No content found in file'}), 400
            
            return jsonify({'chapters': chapters})
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return jsonify({'error': 'Internal server error'}), 500
        finally:
            # Ensure file is cleaned up even if processing fails
            if os.path.exists(filepath):
                os.remove(filepath)
                
    except Exception as e:
        logger.error(f"Error handling file upload: {e}")
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
        logger.error(f"Error generating summary: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def create_app(testing=False):
    """Create and configure the Flask application."""
    if testing:
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
    return app

if __name__ == '__main__':
    try:
        logger.info("Starting server...")
        port = int(os.getenv('PORT', 50869))
        debug = os.getenv('FLASK_ENV') == 'development'
        
        # In production, debug should always be False
        if not debug:
            app.config['DEBUG'] = False
        
        app.run(
            host='127.0.0.1' if debug else '0.0.0.0',
            port=port,
            debug=debug
        )
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        raise