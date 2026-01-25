from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
# Agno imports
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.models.groq import Groq
# Python standard libraries
import os
import sqlite3
import uuid
from datetime import datetime
import json
# Web Scraping Imports
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any # For type hinting the tool's run method

# Load environment variables
load_dotenv()
if not os.environ.get("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY is not set. Please set it in the environment or in a .env file.")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-here")

# Database setup
DB_PATH = "legal_chat.db"

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
        )
    """)

    conn.commit()
    conn.close()

def create_new_session():
    session_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO chat_sessions (id, title)
        VALUES (?, ?)
    """, (session_id, "New Legal Consultation"))

    conn.commit()
    conn.close()
    return session_id

def get_chat_sessions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, created_at, updated_at
        FROM chat_sessions
        ORDER BY updated_at DESC
    """)

    sessions = cursor.fetchall()
    conn.close()

    return [{"id": s[0], "title": s[1], "created_at": s[2], "updated_at": s[3]} for s in sessions]

def get_chat_history(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, role, content, timestamp
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY timestamp ASC
    """, (session_id,))

    messages = cursor.fetchall()
    conn.close()

    return [{"id": m[0], "role": m[1], "content": m[2], "timestamp": m[3]} for m in messages]

def save_message(session_id, role, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO chat_messages (session_id, role, content)
        VALUES (?, ?, ?)
    """, (session_id, role, content))

    cursor.execute("""
        UPDATE chat_sessions
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (session_id,))

    conn.commit()
    conn.close()

def update_session_title(session_id, title):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    display_title = title[:50] + "..." if len(title) > 50 else title
    
    cursor.execute("""
        UPDATE chat_sessions
        SET title = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (display_title, session_id))

    conn.commit()
    conn.close()

# ------------------------------------------------------
#             CUSTOM LAW BHOOMI SCRAPER TOOL CLASS
# ------------------------------------------------------

class LawbhoomiScraperTool:
    """
    Tool to fetch and extract all law notes content from the fixed LawBhoomi URL.
    Use this tool for comprehensive, pre-indexed legal research on topics found in notes.
    """
    def __init__(self):
        self.name = "LawbhoomiScraperTool"
        # The description tells the Agent what data this tool provides
        self.description = "A specialized tool that scrapes the text content from the LawBhoomi Law Notes URL: https://lawbhoomi.com/law-notes/. Use it to find detailed legal concepts, notes, and topic summaries. It takes NO arguments."
        self.fixed_url = "https://lawbhoomi.com/law-notes/"

    def run(self) -> str:
        """
        Scrapes the content from the fixed LawBhoomi URL and returns the main text.
        
        Args:
            No arguments needed.

        Returns:
            str: The extracted text content or an error message.
        """
        url = self.fixed_url
        try:
            # 1. Fetch the content
            headers = {
                'User-Agent': 'LegalAI-LawBhoomi-Scraper/1.0 (Python; Flask; Agno Agent)'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            # 2. Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # 3. Extract the main body text
            for script_or_style in soup(["script", "style"]):
                script_or_style.extract() 

            # Attempt to find the main content block for better accuracy
            main_content = soup.find('div', class_='content-area') 
            if main_content:
                text_content = main_content.get_text(separator=' ', strip=True)
            else:
                # Fallback to the entire body text
                text_content = soup.body.get_text(separator=' ', strip=True)

            clean_text = ' '.join(text_content.split()) 

            if len(clean_text) < 50:
                 return f"Successfully accessed URL {url}, but extracted very little content. Extracted snippet: {clean_text[:50]}..."

            return f"--- START OF LAW BHOOMI NOTES CONTENT ---\n\n{clean_text}\n\n--- END OF LAW BHOOMI NOTES CONTENT ---"

        except requests.exceptions.RequestException as e:
            return f"Error: Could not access LawBhoomi URL {url}. Details: {e}"
        except Exception as e:
            return f"Error: Failed to process content from URL {url}. Details: {e}"

# ------------------------------------------------------
#              LEGAL AI AGENT
# ------------------------------------------------------

def create_legal_agent(chat_history=None):
    context_prompt = ""
    if chat_history:
        context_prompt = "\n\nPrevious conversation context:\n"
        for msg in chat_history[-5:]:
            context_prompt += f"{msg['role'].title()}: {msg['content'][:200]}...\n"

    instructions = [
        "🚨 CRITICAL: You are EXCLUSIVELY a Legal AI Assistant. You MUST ONLY respond to legal questions and legal matters.",
        "❌ STRICTLY REFUSE: If asked about anything non-legal, respond: 'I apologize, but I am a specialized Legal AI Assistant. I can only provide assistance with legal matters, legal research, case analysis, statutory interpretation, and legal consultation. Please ask me a legal question.'",
        "🔍 RESEARCH: Use the **DuckDuckGoTools** for general web search, and specifically use the **LawbhoomiScraperTool** when the user asks for legal concepts, detailed notes, or statutory overviews, as this tool provides pre-indexed legal notes.", # UPDATED INSTRUCTION
        "📋 REQUIRED FORMAT: For all legal responses, always provide: A summary of the facts of the case, Identification of legal issues, Step-by-step legal analysis, Reference to relevant laws (Acts, Sections, Articles), Mention of landmark cases and their citations, A well-structured judgment/conclusion.",
        "💼 PROFESSIONAL: Use clear, professional legal language, while ensuring simplicity and accessibility for users.",
        "⚖️ ACCURACY: Provide comprehensive yet concise explanations, ensuring every answer is backed by relevant authority and interpretation.",
        "🧠 MEMORY: You are an intelligent AI assistant that remembers the ongoing chat context and refers to it when responding.",
        "🚨 CRITICAL: You are EXCLUSIVELY a Legal AI Assistant. You MUST ONLY respond to legal questions and legal matters.",
        "❌ STRICTLY REFUSE: If asked about anything non-legal (technology, cooking, sports, entertainment, personal advice, general knowledge, math, science, etc.), respond: 'I apologize, but I am a specialized Legal AI Assistant. I can only provide assistance with legal matters, legal research, case analysis, statutory interpretation, and legal consultation. Please ask me a legal question.'",
        "✅ LEGAL TOPICS ONLY: Constitutional law, civil law, criminal law, corporate law, family law, property law, contract law, tort law, administrative law, labor law, tax law, intellectual property law, international law, legal procedures, case analysis, statutory interpretation, legal research, court procedures, legal documentation, legal precedents, and legal advice.",
        "📋 REQUIRED FORMAT: For all legal responses, always provide: A summary of the facts of the case, Identification of legal issues, Step-by-step legal analysis, Reference to relevant laws (Acts, Sections, Articles), Mention of landmark cases and their citations, A well-structured judgment/conclusion, Citations of law commission reports, official gazettes, or legal commentaries where appropriate.",
        "🔍 RESEARCH: Pull factual and statutory data from Google API and authoritative legal websites like Indian Kanoon, SCC Online, Manupatra, Bar & Bench, LiveLaw.",
        "💼 PROFESSIONAL: Use clear, professional legal language, while ensuring simplicity and accessibility for users.",
        "⚖️ ACCURACY: Provide comprehensive yet concise explanations, ensuring every answer is backed by relevant authority and interpretation.",
        "🔒 ETHICS: Always ensure the output maintains legal accuracy, neutrality, and ethical standards.",
        "🧠 MEMORY: You are an intelligent AI assistant that remembers the ongoing chat context and refers to it when responding.",
        "🔄 CONTINUITY: Maintain continuity and coherence within the same chat session.",
        "❓ FOLLOW-UP: Understand follow-up questions based on earlier user inputs and your responses.",
        "🚫 NO REPEAT: Avoid repeating the same content unless requested.",
        "📋 REQUIRED FORMAT: For all legal responses, always provide: A introduction of the topic, Identification of legal issues, Analysis, Reference to relevant laws (Acts, Sections, Articles), Mention of landmark cases and their citations, A well-structured conclusion, Citations of law commission reports, official gazettes, or legal commentaries where appropriate.",
        "REQUIRED FORMAT OF CASE LAWS : A summary of facts of the case, Identification of Legal issues involved, Identification of law applicable, mention the section, article with he act, Judgment of case and conclusion " ,            
        "🔍 RESEARCH: Pull factual and statutory data from Google and authoritative legal websites like Indian Kanoon, SCC Online, Manupatra, Bar & Bench, LiveLaw, Law Bhoomi, Case Mine, Drishti Judiciary, Law Jurist.",
        "⚖️ LEGAL CONSULTATION: Provide detailed legal consultation, including potential outcomes, risks, and benefits of different legal strategies.",
        "⚖️ LEGAL ONLY: Stay strictly within the context of legal consultation only - no exceptions.",
        f"Context from previous conversation: {context_prompt}" if context_prompt else ""
    ]

    agent = Agent(
        model=Groq(id="llama-3.3-70b-versatile", temperature=0.1),
        description="You are a highly qualified legal advisor.",
        instructions=instructions,
        tools=[DuckDuckGoTools(), LawbhoomiScraperTool()], # --- ADDED CUSTOM LAW BHOOMI TOOL HERE ---
        markdown=True
    )

    return agent

# ------------------------------------------------------
#                  ROUTES (No Changes Below)
# ------------------------------------------------------

@app.route("/")
def index():
    return render_template('legal_chat.html')

@app.route("/api/new_session", methods=["POST"])
def new_session():
    session_id = create_new_session()
    return jsonify({"session_id": session_id, "status": "success"})

@app.route("/api/sessions", methods=["GET"])
def get_sessions_route():
    return jsonify({"sessions": get_chat_sessions()})

@app.route("/api/chat/<session_id>", methods=["GET"])
def get_chat(session_id):
    return jsonify({"history": get_chat_history(session_id)})

@app.route("/api/chat/<session_id>/message", methods=["POST"])
def send_message(session_id):
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        chat_history = get_chat_history(session_id)

        if len(chat_history) == 0:
            update_session_title(session_id, user_message)

        save_message(session_id, "user", user_message)

        agent = create_legal_agent(chat_history)
        response = agent.run(user_message)
        ai_response = str(response.content)

        save_message(session_id, "assistant", ai_response)

        return jsonify({"response": ai_response, "status": "success"})

    except Exception as e:
        print("Error in send_message:", e)
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route("/api/delete_session/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM chat_messages WHERE session_id = ?', (session_id,))
        cursor.execute('DELETE FROM chat_sessions WHERE id = ?', (session_id,))
        conn.commit()
        conn.close()

        return jsonify({"status": "success"})
    except Exception as e:
        print("Error deleting session:", e)
        return jsonify({"error": "Failed to delete session"}), 500

@app.route("/api/chat/<session_id>/edit/<int:message_id>", methods=["PUT"])
def edit_message(session_id, message_id):
    try:
        data = request.get_json()
        new_message = data.get("message", "").strip()

        if not new_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT role FROM chat_messages WHERE id = ? AND session_id = ?",
            (message_id, session_id)
        )

        result = cursor.fetchone()
        if not result or result[0] != 'user':
            conn.close()
            return jsonify({"error": "Message not found or cannot edit assistant messages"}), 404

        cursor.execute("""
            UPDATE chat_messages
            SET content = ?, timestamp = CURRENT_TIMESTAMP
            WHERE id = ? AND session_id = ?
        """, (new_message, message_id, session_id))

        cursor.execute("""
            DELETE FROM chat_messages
            WHERE session_id = ? AND id > ?
        """, (session_id, message_id))

        cursor.execute("""
            UPDATE chat_sessions
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (session_id,))

        conn.commit()
        conn.close()

        chat_history = get_chat_history(session_id)
        agent = create_legal_agent(chat_history)

        response = agent.run(new_message)
        ai_response = str(response.content)

        save_message(session_id, "assistant", ai_response)

        return jsonify({"response": ai_response, "status": "success"})

    except Exception as e:
        print("Error in edit_message:", e)
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# ------------------------------------------------------
#                  RUN APP
# ------------------------------------------------------

if __name__ == "__main__":
    init_db() 
    app.run(host="0.0.0.0", port=8080, debug=True)