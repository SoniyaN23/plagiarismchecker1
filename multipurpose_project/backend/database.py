import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '../instance/plagiarism.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            text TEXT,
            similarity INTEGER,
            sources TEXT,
            highlighted_text TEXT,
            explanation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_report(report_type, text, similarity, sources, highlighted_text, explanation):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reports (type, text, similarity, sources, highlighted_text, explanation)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (report_type, text, similarity, ','.join(sources), highlighted_text, ','.join(explanation)))
    conn.commit()
    conn.close()

def get_reports():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reports ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    reports = []
    for row in rows:
        reports.append({
            "id": row[0],
            "type": row[1],
            "text": row[2],
            "similarity": row[3],
            "sources": row[4].split(',') if row[4] else [],
            "highlighted_text": row[5],
            "explanation": row[6].split(',') if row[6] else [],
            "created_at": row[7]
        })
    return reports
