import os
import requests
import pdfplumber
from flask import Flask, request, jsonify, send_from_directory, json
from flask_cors import CORS
from difflib import SequenceMatcher
from plagiarism_checker import check_plagiarism
from database import init_db, save_report, get_reports
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from dotenv import load_dotenv


load_dotenv()  


app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(app.root_path, '../uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


init_db()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

def get_paraphrasing_suggestion(sentence):
    if not GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY not set in .env or environment."
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    payload = {
        "contents": [
            {"parts": [{"text": f"Paraphrase this sentence to make it original: {sentence}"}]}
        ]
    }
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        suggestion = data["candidates"][0]["content"]["parts"][0]["text"]
        return suggestion
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return f"Error calling Gemini API: {e}"


def extract_text(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def compare_pdfs_simple(pdf1, pdf2, top_n=3):
    text1 = extract_text(pdf1)
    text2 = extract_text(pdf2)
    similarity = SequenceMatcher(None, text1, text2).ratio() * 100
    sentences1 = text1.split(".")
    sentences2 = text2.split(".")
    matches = []
    for s1 in sentences1:
        for s2 in sentences2:
            if SequenceMatcher(None, s1.strip(), s2.strip()).ratio() > 0.8:
                matches.append(s1.strip())
    top_matches = matches[:top_n]
    return {"similarity": round(similarity, 2), "top_matches": top_matches, "text1": text1, "text2": text2}

def check_code_similarity(code1, code2):
    from code_checker import check_code_similarity as check_code_logic 
    return check_code_logic(code1, code2)

def generate_pdf_report(similarity, matches, text1, text2, output_path="report.pdf"):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []
    elements.append(Paragraph("<b>PDF Plagiarism Report</b>", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Plagiarism Percentage: <b>{round(similarity,2)}%</b>", styles["Normal"]))
    elements.append(Spacer(1, 12))
    if matches:
        elements.append(Paragraph("<b>Plagiarized Sentences Highlighted Below:</b>", styles["Heading2"]))
        elements.append(Spacer(1, 12))
        highlighted_text1 = text1
        highlighted_text2 = text2
        for sent in matches:
            highlighted_text1 = highlighted_text1.replace(sent, f'<font color="red">{sent}</font>')
            highlighted_text2 = highlighted_text2.replace(sent, f'<font color="red">{sent}</font>')
        elements.append(Paragraph("<b>Document 1:</b>", styles["Heading2"]))
        elements.append(Paragraph(highlighted_text1, styles["Normal"]))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("<b>Document 2:</b>", styles["Heading2"]))
        elements.append(Paragraph(highlighted_text2, styles["Normal"]))
    else:
        elements.append(Paragraph("No plagiarized sentences detected.", styles["Normal"]))
    doc.build(elements)
    return output_path

def generate_text_report(result_data, output_path="report.pdf"):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []
    elements.append(Paragraph("<b>Text Similarity Analysis Report</b>", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Overall Similarity: <b>{result_data['similarity']}%</b>", styles["Normal"]))
    elements.append(Paragraph(f"AI Detection (Mock): <b>{result_data.get('ai', 0)}%</b>", styles["Normal"]))
    elements.append(Paragraph(f"Human Detection (Mock): <b>{result_data.get('human', 0)}%</b>", styles["Normal"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("<b>Matched Sources:</b>", styles["Heading3"]))
    for source_obj in result_data.get('sources', []):
        url = source_obj.get('url', 'N/A')
        excerpt = source_obj.get('excerpt', 'No snippet provided')
        elements.append(Paragraph(f"- <a href='{url}'>{url}</a>: {excerpt}", styles["Normal"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("<b>Suggestions:</b>", styles["Heading3"]))
    for suggestion in result_data.get('explanation', []):
        elements.append(Paragraph(f"- {suggestion}", styles["Normal"]))
    doc.build(elements)
    return output_path


@app.route('/api/check', methods=['POST'])
def api_check_text():
    text = request.form.get('text')
    file = request.files.get('file')

    if file:
        filename = (file.filename or "").lower()
        mimetype = (file.mimetype or "").lower()

        if filename.endswith('.pdf') or 'pdf' in mimetype:
            try:
                text = extract_text(file)
            except Exception as e:
                print(f"Error extracting PDF text: {e}")
                return jsonify({"error": "Failed to extract text from PDF"}), 500
        else:
            raw = file.read()
            if isinstance(raw, bytes):
                try:
                    text = raw.decode('utf-8')
                except UnicodeDecodeError:
                    text = raw.decode('latin-1', errors='replace')
            else:
                text = raw

    if not text:
        return jsonify({"error": "No text provided"}), 400

    
    result = check_plagiarism(text)

   
    mock_result = {**result, "ai": 45, "human": 55}

  
    report_path = os.path.join(app.root_path, "report.pdf")
    generate_text_report(result_data=mock_result, output_path=report_path)

   
    source_urls = [s.get('url', 'N/A') for s in result.get('sources', [])]
    save_report('text', text, result['similarity'], source_urls,
                result['highlighted_text'], result['explanation'])

    return jsonify(mock_result)

@app.route('/api/suggest_paraphrase', methods=['POST'])
def api_suggest_paraphrase():
    data = request.get_json()
    sentence = data.get('sentence', '')
    if not sentence:
        return jsonify({"error": "No sentence provided"}), 400
    suggestion = get_paraphrasing_suggestion(sentence)
    return jsonify({"original": sentence, "suggestion": suggestion})

@app.route('/api/compare_pdfs', methods=['POST'])
def api_compare_pdfs():
    pdf1 = request.files.get('file1')
    pdf2 = request.files.get('file2')
    if not pdf1 or not pdf2:
        return jsonify({"error": "Both PDFs required"}), 400
    result = compare_pdfs_simple(pdf1, pdf2)
    report_path = os.path.join(app.root_path, "report.pdf")
    generate_pdf_report(result['similarity'], result['top_matches'],
                        result['text1'], result['text2'], output_path=report_path)
    save_report('pdf', "PDF comparison", result['similarity'], [], "", [])
    return jsonify({**result, "report_file": "report.pdf"})

@app.route('/api/check_code', methods=['POST'])
def api_check_code():
    code1_file = request.files.get("file1")
    code2_file = request.files.get("file2")
    if not code1_file or not code2_file:
        return jsonify({"error": "Both code files are required"}), 400
    code1 = code1_file.read().decode('utf-8')
    code2 = code2_file.read().decode('utf-8')
    result = check_code_similarity(code1, code2) 
    save_report('code', f"{code1[:50]}...", result['similarity'], [], result['highlighted_code'], [])
    return jsonify(result)

@app.route('/api/reports', methods=['GET'])
def api_reports():
    reports = get_reports()
    return jsonify(reports)

@app.route('/api/download_report', methods=['GET'])
def api_download_report():
    report_path = os.path.join(app.root_path, "report.pdf")
    if not os.path.exists(report_path):
        return jsonify({"error": "Report not found. Please run a check first."}), 404
    return send_from_directory(app.root_path, "report.pdf", as_attachment=True)

@app.route('/')
def index():
    return send_from_directory(os.path.join(app.root_path, '../frontend'), 'index.html')

@app.route('/<path:filename>')
def serve_frontend(filename):
    return send_from_directory(os.path.join(app.root_path, '../frontend'), filename)


if __name__ == '__main__':
    app.run(debug=True)
