import streamlit as st
import json
from pdfplumber import PDF
import docx
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="Whole-Brain Tender Questions", page_icon="🧠", layout="wide")

st.title("🧠 Whole-Brain Tender Analyser")
st.markdown("Upload a tender/RFP and get **10 questions per HBDI quadrant**.")

# ====================== MODEL SELECTOR ======================
model_options = {
    "Gemini 2.5 Flash (Google - FREE to start)": "gemini",
    "Grok 4.1 Fast (xAI - cheap & powerful)": "grok"
}
selected_model_name = st.selectbox("Choose AI Model:", options=list(model_options.keys()), index=0)
selected_model = model_options[selected_model_name]

# ====================== API KEYS ======================
if selected_model == "grok":
    api_key = st.secrets.get("XAI_API_KEY")
    if not api_key:
        st.warning("⚠️ Add your XAI_API_KEY in Streamlit secrets to use Grok.")
else:
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.warning("⚠️ Add your GEMINI_API_KEY in Streamlit secrets to use Gemini.")

# ====================== FILE UPLOAD ======================
uploaded_file = st.file_uploader("Upload tender document (PDF or Word)", type=["pdf", "docx"])

def extract_text(file):
    if file.type == "application/pdf":
        text = ""
        with PDF(file) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        return text
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    return ""

# ====================== PDF GENERATION FUNCTION (Fixed for Streamlit) ======================
def create_whole_brain_pdf(questions):
    class PDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 16)
            self.cell(0, 10, "Whole-Brain Tender Approach", ln=1, align="C")
            self.set_font("Helvetica", "", 10)
            self.cell(0, 6, f"Generated on {datetime.now().strftime('%d %B %Y')}", ln=1, align="C")
            self.ln(15)

        def quadrant_title(self, title, rgb):
            self.set_font("Helvetica", "B", 14)
            self.set_fill_color(*rgb)
            self.set_text_color(255, 255, 255)
            self.cell(0, 12, title, ln=1, align="C", fill=True)
            self.ln(8)

    pdf = PDF()
    pdf.add_page()

    colors = {
        "A": (0, 102, 204),   # Blue
        "B": (0, 153, 0),     # Green
        "C": (204, 0, 0),     # Red
        "D": (204, 153, 0)    # Yellow
    }

    quadrant_names = {
        "A": "Quadrant A - Analytical (Blue)",
        "B": "Quadrant B - Practical (Green)",
        "C": "Quadrant C - Relational (Red)",
        "D": "Quadrant D - Conceptual (Yellow)"
    }

    for q in ["A", "B", "C", "D"]:
        pdf.quadrant_title(quadrant_names[q], colors[q])
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 11)
        
        for i, question in enumerate(questions.get(q, []), 1):
            clean_question = question.replace("–", "-").replace("—", "-").replace("’", "'")
            pdf.multi_cell(0, 8, f"{i}. {clean_question}")
            pdf.ln(5)
        
        if q != "D":
            pdf.add_page()

    # Fixed: Convert to bytes properly for Streamlit
    pdf_output = pdf.output(dest="S")
    if isinstance(pdf_output, bytearray):
        return bytes(pdf_output)
    return pdf_output

# ====================== MAIN LOGIC ======================
if uploaded_file:
    with st.spinner("Extracting text from document..."):
        tender_text = extract_text(uploaded_file)
    
    if len(tender_text.strip()) < 200:
        st.error("Not enough text extracted. Please try a different file.")
        st.stop()

    st.success(f"✅ Extracted ~{len(tender_text):,} characters")

    if st.button("Generate 40 Whole-Brain Questions", type="primary", use_container_width=True):
        if not api_key:
            st.error("Missing API key for the selected model. Please check Streamlit secrets.")
            st.stop()

        with st.spinner(f"Analysing tender with {selected_model_name}..."):
            prompt = f"""You are an expert bid strategist and HBDI specialist.
Analyse this tender document and create exactly 10 specific, actionable questions for EACH HBDI quadrant.

Tender text:
=== TENDER START ===
{tender_text}
=== TENDER END ===

Output ONLY valid JSON with this exact structure:
{{
  "A": ["question 1", "question 2", ...],
  "B": ["question 1", ...],
  "C": ["question 1", ...],
  "D": ["question 1", ...]
}}

Quadrants:
- A (Blue): Analytical, data, ROI, technical specs, risk, metrics
- B (Green): Process, timelines, compliance, steps, organisation
- C (Red): People, stakeholders, culture, communication, values, team fit
- D (Yellow): Innovation, big picture, future vision, creative
