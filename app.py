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

if uploaded_file:
    with st.spinner("Extracting text from document..."):
        tender_text = extract_text(uploaded_file)
    
    if len(tender_text.strip()) < 200:
        st.error("Not enough text extracted. Please try a different file.")
        st.stop()

    st.success(f"✅ Extracted ~{len(tender_text):,} characters")

    if st.button("Generate 40 Whole-Brain Questions", type="primary", use_container_width=True):
        if not api_key:
            st.error("Missing API key for the selected model.")
            st.stop()

        with st.spinner(f"Analysing with {selected_model_name}..."):
            prompt = f"""You are an expert bid strategist and HBDI specialist.
Analyse this tender and create exactly 10 specific questions for EACH HBDI quadrant.

Tender text:
=== TENDER START ===
{tender_text}
=== TENDER END ===

Output ONLY valid JSON:
{{
  "A": ["question 1", "question 2", ...],
  "B": ["question 1", ...],
  "C": ["question 1", ...],
  "D": ["question 1", ...]
}}

Quadrants:
- A (Blue): Analytical, data, ROI, technical, risk
- B (Green): Process, timelines, compliance, steps
- C (Red): People, stakeholders, culture, team
- D (Yellow): Innovation, big picture, future, creative"""

                        try:
                if selected_model == "grok":
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
                    response = client.chat.completions.create(
                        model="grok-4-1-fast-reasoning",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        response_format={"type": "json_object"}
                    )
                    result = json.loads(response.choices[0].message.content)
                else:  # gemini
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    response = model.generate_content(
                        prompt,
                        generation_config={"response_mime_type": "application/json", "temperature": 0.3}
                    )
                    result = json.loads(response.text)

                # Store the result so it survives page reruns
                st.session_state.questions = result
                st.session_state.tender_text = tender_text[:500]  # short summary

                # ====================== DISPLAY QUESTIONS ======================
                st.markdown("### 🎯 Your Whole-Brain Tender Questions")
                col1, col2 = st.columns(2)
                col3, col4 = st.columns(2)

                quadrants = {
                    "A": ("🔵 Quadrant A – Analytical (Blue)", col1, (0, 102, 204)),
                    "B": ("🟢 Quadrant B – Practical (Green)", col2, (0, 153, 0)),
                    "C": ("🔴 Quadrant C – Relational (Red)", col3, (204, 0, 0)),
                    "D": ("🟡 Quadrant D – Conceptual (Yellow)", col4, (204, 153, 0)),
                }

                for q, (title, col, rgb) in quadrants.items():
                    with col:
                        st.markdown(f"**{title}**")
                        for i, question in enumerate(result.get(q, []), 1):
                            st.markdown(f"{i}. {question}")

            except Exception as e:
                st.error(f"Error generating questions: {str(e)}")

# ====================== PDF DOWNLOAD (OUTSIDE the generate block) ======================
if "questions" in st.session_state:
    if st.button("📄 Download PDF", type="primary", use_container_width=True):
        with st.spinner("Creating beautiful PDF..."):
            pdf_bytes = create_whole_brain_pdf(st.session_state.questions)
            st.download_button(
                label="⬇️ Click here to download the PDF",
                data=pdf_bytes,
                file_name=f"Whole_Brain_Tender_Questions_{datetime.now().strftime('%Y-%m-%d')}.pdf",
                mime="application/pdf",
                key="pdf_download"   # important to avoid conflicts
            )
