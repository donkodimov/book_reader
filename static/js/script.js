/* JavaScript code for Book Reader app */

let currentChapters = [];
let isDarkTheme = false;

// Theme toggle
function toggleTheme() {
    isDarkTheme = !isDarkTheme;
    document.body.setAttribute('data-theme', isDarkTheme ? 'dark' : 'light');
    localStorage.setItem('theme', isDarkTheme ? 'dark' : 'light');
}

// Sidebar toggle for mobile devices
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('active');
}

// Initialize theme from localStorage
document.addEventListener('DOMContentLoaded', () => {
    let savedTheme = localStorage.getItem('theme') || 'dark';
    localStorage.setItem('theme', savedTheme);
    isDarkTheme = savedTheme === 'dark';
    document.body.setAttribute('data-theme', savedTheme);
});

// Resizable panels
function initializeResizers() {
    const container = document.querySelector('.container');
    const resizer1 = document.getElementById('resizer1');
    const resizer2 = document.getElementById('resizer2');
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    const summary = document.querySelector('.summary');

    let isResizing = false;
    let currentResizer = null;
    let startX, startWidthSidebar, startWidthSummary;

    function startResize(e, resizer) {
        isResizing = true;
        currentResizer = resizer;
        startX = e.pageX;
        
        // Add resizing class for visual feedback
        currentResizer.classList.add('resizing');
        document.body.style.cursor = 'col-resize';
        
        // Prevent text selection while resizing
        document.body.style.userSelect = 'none';
        
        if (currentResizer.id === 'resizer1') {
            startWidthSidebar = sidebar.offsetWidth;
        } else {
            startWidthSummary = summary.offsetWidth;
        }

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', stopResize);
    }

    function handleMouseMove(e) {
        if (!isResizing) return;

        const containerWidth = container.offsetWidth;
        const minWidth = 200;
        const maxContentWidth = containerWidth - 450; // Minimum space for content

        if (currentResizer.id === 'resizer1') {
            const diff = e.pageX - startX;
            const newWidth = Math.min(Math.max(startWidthSidebar + diff, minWidth), maxContentWidth);
            sidebar.style.width = `${newWidth}px`;
        } else {
            const diff = startX - e.pageX;
            const newWidth = Math.min(Math.max(startWidthSummary + diff, minWidth), maxContentWidth);
            summary.style.width = `${newWidth}px`;
        }

        // Save the widths to localStorage
        localStorage.setItem('sidebarWidth', sidebar.style.width);
        localStorage.setItem('summaryWidth', summary.style.width);
    }

    function stopResize() {
        isResizing = false;
        currentResizer.classList.remove('resizing');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', stopResize);
    }

    // Restore saved widths from localStorage
    const savedSidebarWidth = localStorage.getItem('sidebarWidth');
    const savedSummaryWidth = localStorage.getItem('summaryWidth');
    if (savedSidebarWidth) sidebar.style.width = savedSidebarWidth;
    if (savedSummaryWidth) summary.style.width = savedSummaryWidth;

    resizer1.addEventListener('mousedown', (e) => startResize(e, resizer1));
    resizer2.addEventListener('mousedown', (e) => startResize(e, resizer2));

    // Double-click to reset to default widths
    resizer1.addEventListener('dblclick', () => {
        sidebar.style.width = '250px';
        localStorage.setItem('sidebarWidth', '250px');
    });

    resizer2.addEventListener('dblclick', () => {
        summary.style.width = '300px';
        localStorage.setItem('summaryWidth', '300px');
    });
}

// Initialize resizers after DOM is loaded
document.addEventListener('DOMContentLoaded', initializeResizers);

async function uploadBook() {
    const fileInput = document.getElementById('bookFile');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please select a file');
        return;
    }
    const formData = new FormData();
    formData.append('file', file);
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        console.log(data);
        if (data.error) {
            alert(data.error);
            return;
        }
        currentChapters = data.chapters;
        displayChapters(data.chapters);
        
        // Update the uploaded book's name (display only the file name)
        document.getElementById('book-name').textContent = data.book_name;
    } catch (error) {
        alert('Error uploading file: ' + error);
    }
}

function displayChapters(chapters) {
    const chaptersDiv = document.getElementById('chapters');
    chaptersDiv.innerHTML = '';
    
    chapters.forEach((chapter, index) => {
        const chapterDiv = document.createElement('div');
        chapterDiv.className = 'chapter-link';
        chapterDiv.textContent = chapter.title;
        chapterDiv.onclick = () => {
            // Remove active class from all chapters
            document.querySelectorAll('.chapter-link').forEach(ch => ch.classList.remove('active'));
            // Add active class to clicked chapter
            chapterDiv.classList.add('active');
            displayChapter(index);
        };
        chaptersDiv.appendChild(chapterDiv);
    });
}

let currentChapterIndex = -1;

function displayChapter(index) {
    currentChapterIndex = index;
    const chapter = currentChapters[index];
    document.getElementById('content').innerHTML = chapter.content;
    document.getElementById('summary-content').textContent = 'Click "Generate Summary" to get an AI-generated summary for this chapter.';
    document.getElementById('generate-summary').disabled = false;
}

async function generateSummary() {
    if (currentChapterIndex === -1) {
        alert('Please select a chapter first');
        return;
    }

    const chapter = currentChapters[currentChapterIndex];
    const summaryButton = document.getElementById('generate-summary');
    const summaryLoading = document.getElementById('summary-loading');
    
    // Disable button and show loading
    summaryButton.disabled = true;
    summaryLoading.style.display = 'block';
    document.getElementById('summary-content').textContent = '';

    try {
        const response = await fetch('/summarize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content: chapter.content })
        });
        const data = await response.json();
        if (data.error) {
            document.getElementById('summary-content').textContent = data.error;
        } else {
            document.getElementById('summary-content').textContent = data.summary;
        }
    } catch (error) {
        document.getElementById('summary-content').textContent = 'Error generating summary: ' + error.message;
    } finally {
        summaryButton.disabled = false;
        summaryLoading.style.display = 'none';
    }
}

function nextChapter() {
    if (currentChapters.length > 0 && currentChapterIndex < currentChapters.length - 1) {
        displayChapter(currentChapterIndex + 1);
    }
}

function previousChapter() {
    if (currentChapters.length > 0 && currentChapterIndex > 0) {
        displayChapter(currentChapterIndex - 1);
    }
} 