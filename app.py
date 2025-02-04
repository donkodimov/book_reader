import os
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
import ebooklib
from ebooklib import epub
from PyPDF2 import PdfReader
import openai
from dotenv import load_dotenv

load_dotenv()

# Set OpenAI API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'epub', 'pdf'}

# Initialize OpenAI client
client = openai.OpenAI()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_chapters_epub(file_path):
    book = epub.read_epub(file_path)
    chapters = []
    
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapters.append({
                'title': item.get_name(),
                'content': item.get_content().decode('utf-8')
            })
    
    return chapters

def extract_chapters_pdf(file_path):
    reader = PdfReader(file_path)
    chapters = []
    
    for i in range(len(reader.pages)):
        content = reader.pages[i].extract_text()
        chapters.append({
            'title': f'Page {i + 1}',
            'content': content
        })
    
    return chapters

def get_chapter_summary(content):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes book chapters."},
                {"role": "user", "content": f"Please provide a brief summary of the following chapter content: {content[:4000]}"}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating summary: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        if filename.endswith('.epub'):
            chapters = extract_chapters_epub(filepath)
        else:
            chapters = extract_chapters_pdf(filepath)
        
        return jsonify({'chapters': chapters})
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/summarize', methods=['POST'])
def summarize():
    content = request.json.get('content')
    if not content:
        return jsonify({'error': 'No content provided'}), 400
    
    summary = get_chapter_summary(content)
    return jsonify({'summary': summary})

if __name__ == '__main__':
    try:
        print("Starting server...")
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        print("Upload directory created/verified")
        print("Attempting to start server on port 50869...")
        app.run(host='0.0.0.0', port=50869, debug=True)
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        raise