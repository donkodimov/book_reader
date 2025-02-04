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

1. Start the server:
```bash
python app.py
```

2. Open your browser and navigate to `http://localhost:50869`

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