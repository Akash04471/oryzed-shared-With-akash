# LegalAI - Professional Legal Assistant

A sophisticated legal chatbot powered by advanced AI technology, featuring memory management, session storage, and a professional ChatGPT-like interface designed specifically for legal consultations.

## ✨ Features

### 🎯 Advanced Legal AI Capabilities
- **Professional Legal Advisor**: Provides detailed legal analysis with case facts, legal issues, step-by-step analysis, and relevant law references
- **Comprehensive Legal Research**: Cites landmark cases, statutory provisions, and legal commentaries
- **Contextual Memory**: Remembers conversation history and maintains context across the session
- **Web Search Integration**: Real-time legal information retrieval from authoritative sources

### 💼 Professional Interface
- **ChatGPT-like Sidebar**: Clean, modern interface with chat history and session management
- **Session Management**: Create, save, and manage multiple legal consultations
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Legal Domain Theming**: Professional color scheme and legal iconography

### 🗄️ Data Management
- **SQLite Database**: Persistent storage for chat sessions and messages
- **Session History**: Browse and resume previous legal consultations
- **Memory Persistence**: Maintains context and conversation flow
- **Session Titles**: Auto-generated titles based on initial queries

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Groq API key

### 1. Clone and Setup Environment
```bash
# Clone the repository
git clone <repository-url>
cd LegalAI

# Create virtual environment
python -m venv legalai-env

# Activate virtual environment
# On Windows:
legalai-env\Scripts\activate
# On macOS/Linux:
source legalai-env/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=your_secret_key_for_flask_sessions
```

### 4. Run the Application
```bash
python app.py
```

The application will be available at `http://localhost:8080`

## 🏗️ Architecture

### Backend Components
- **Flask Application**: RESTful API endpoints for chat management
- **SQLite Database**: Session and message storage
- **Groq AI Integration**: Advanced language model for legal reasoning
- **Session Management**: UUID-based session tracking

### Frontend Components
- **Responsive UI**: Modern, professional interface
- **Real-time Chat**: WebSocket-like experience with AJAX
- **Sidebar Navigation**: Session history and management
- **Loading States**: Professional loading indicators

### Database Schema
```sql
-- Chat Sessions
CREATE TABLE chat_sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat Messages
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
);
```

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main application interface |
| POST | `/api/new_session` | Create new chat session |
| GET | `/api/sessions` | Get all chat sessions |
| GET | `/api/chat/<session_id>` | Get chat history for session |
| POST | `/api/chat/<session_id>/message` | Send message to session |
| DELETE | `/api/delete_session/<session_id>` | Delete chat session |

## 💡 Usage

### Starting a New Consultation
1. Click "New Consultation" in the sidebar
2. Describe your legal query in detail
3. Receive comprehensive legal analysis and guidance

### Managing Sessions
- **View History**: Browse previous consultations in the sidebar
- **Resume Session**: Click on any previous session to continue
- **Delete Session**: Use the delete button (appears on hover)

### Legal Query Best Practices
- Provide detailed facts and circumstances
- Specify jurisdiction if relevant
- Ask for specific legal analysis or guidance
- Request case law or statutory references

## ⚖️ Legal Disclaimer

**IMPORTANT**: This application provides legal information for educational and informational purposes only. It does not constitute legal advice and should not be relied upon as a substitute for consultation with a qualified attorney. 

- Consult with a licensed attorney for specific legal matters
- Laws vary by jurisdiction and change over time
- AI-generated content may contain errors or omissions
- Use this tool as a starting point for legal research, not as definitive legal guidance

## 🛠️ Development

### Project Structure
```
LegalAI/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── legal_chat.db         # SQLite database (auto-created)
├── templates/
│   └── legal_chat.html   # Main UI template
├── static/
│   └── legal_style.css   # Professional styling
└── README.md             # This file
```

### Key Technologies
- **Backend**: Flask, SQLite, Groq AI
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), jQuery
- **Styling**: Custom CSS with legal domain theming
- **Icons**: Font Awesome 6.4.0

## 🔒 Security & Privacy

- Session data is stored locally in SQLite database
- No chat data is transmitted to external services (except Groq API for AI responses)
- Environment variables used for sensitive configuration
- Input validation and sanitization implemented

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Professional Legal AI Assistant** - Empowering legal professionals and individuals with intelligent legal guidance and research capabilities.

