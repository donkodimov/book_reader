# Book Reader

A web-based book reader application that supports EPUB and PDF formats with AI-powered chapter summaries.

## Features

- Support for EPUB and PDF files
- Chapter/page navigation
- AI-powered chapter summaries using OpenAI GPT
- Dark/Light theme toggle
- Resizable panels with persistent layout
- Responsive design

## Requirements

- Python 3.12+
- Flask
- ebooklib
- PyPDF2
- OpenAI Python client
- python-dotenv

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd book-reader
```

2. Install dependencies:
```bash
pip install flask ebooklib PyPDF2 openai python-dotenv
```

3. Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Development Mode

1. Start the server in development mode:
```bash
FLASK_ENV=development python app.py
```

2. Open your browser and navigate to `http://localhost:50869`

### Production Mode

For production deployment, configure the following environment variables:

```bash
# Required
OPENAI_API_KEY=your_api_key_here

# Optional (with secure defaults)
FLASK_ENV=production        # Default: production
PORT=50869                 # Default: 50869
HOST=127.0.0.1            # Default: 127.0.0.1
ALLOW_ALL_INTERFACES=false # Default: false

# Start the server
python app.py
```

### Security Notes

1. **Network Binding**:
   - Development: Always binds to localhost (127.0.0.1)
   - Production: Binds to localhost by default
   - To bind to all interfaces (0.0.0.0), set `ALLOW_ALL_INTERFACES=true`

2. **Debug Mode**:
   - Automatically enabled in development
   - Never enabled in production
   - Only works with localhost binding

3. **Rate Limiting**:
   - 100 requests per hour by default
   - Configurable through app configuration

3. Upload an EPUB or PDF file using the upload button

4. Navigate through chapters using the left sidebar

5. Click "Generate Summary" to get an AI-powered summary of the current chapter

## Features

### File Support
- EPUB files with chapter extraction
- PDF files with page-by-page navigation

### User Interface
- Resizable panels (chapters, content, and summary)
- Dark/Light theme toggle
- Persistent layout preferences
- Clean and modern design

### AI Integration
- Chapter summaries using OpenAI's GPT model
- Configurable through environment variables

## License

MIT License