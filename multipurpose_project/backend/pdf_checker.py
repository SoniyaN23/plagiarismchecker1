import PyPDF2
from difflib import SequenceMatcher
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def extract_pdf_text(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + " "
    return text.strip()


def compare_pdfs(file1, file2, output_report="report.pdf"):
    text1 = extract_pdf_text(file1)
    text2 = extract_pdf_text(file2)

   
    ratio = SequenceMatcher(None, text1, text2).ratio()
    similarity = int(ratio * 100)

   
    sentences1 = text1.split(".")
    sentences2 = text2.split(".")
    matching_sentences = []

    for s1 in sentences1:
        for s2 in sentences2:
            if s1.strip() and s2.strip():
                if SequenceMatcher(None, s1.strip(), s2.strip()).ratio() > 0.8:
                    if s1.strip() not in matching_sentences:
                        matching_sentences.append(s1.strip())

   
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(output_report, pagesize=A4)
    elements = []

    elements.append(Paragraph("<b>PDF Plagiarism Report</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Plagiarism Percentage: <b>{similarity}%</b>", styles["Normal"]))
    elements.append(Spacer(1, 12))

    if matching_sentences:
        elements.append(Paragraph("<b>Plagiarized Sentences:</b>", styles["Heading2"]))
        for sent in matching_sentences:
            
            highlighted = f'<font color="red">{sent}</font>'
            elements.append(Paragraph(highlighted, styles["Normal"]))
            elements.append(Spacer(1, 6))
    else:
        elements.append(Paragraph("No plagiarized sentences detected.", styles["Normal"]))

    doc.build(elements)

    return {
        "similarity": similarity,
        "report_file": output_report  
    }
