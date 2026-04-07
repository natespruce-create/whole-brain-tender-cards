import streamlit as st
import json
from pdfplumber import PDF
import docx
from fpdf import FPDF
from datetime import datetime

st.set_page_config(page_title="Whole-Brain Tender Questions", page_icon="🧠", layout="wide")
st.title("🧠 Whole-Brain Tender Analyser")

# Model selector (same as before)
model_options = {
    "Gemini 2.5 Flash (Google - FREE to start)": "gemini",
    "Grok 4.1 Fast (xAI - cheap & powerful)": "grok"
}
selected_model_name = st.selectbox("Choose AI Model:", options=list(model_options.keys()), index=0)
selected_model = model_options[selected_model_name]

# ... (keep your existing API key and file upload code exactly the same until the results part) ...

# After generating the result (inside the try block, after displaying the questions):

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

                # ====================== DOWNLOAD PRETTY PDF ======================
                if st.button("📄 Download Pretty PDF (One Quadrant Per Page)", type="primary", use_container_width=True):
                    with st.spinner("Creating beautiful PDF..."):
                        pdf = create_whole_brain_pdf(result, tender_text[:500])  # pass first 500 chars as summary
                        st.download_button(
                            label="⬇️ Click here to download the PDF",
                            data=pdf,
                            file_name=f"Whole_Brain_Tender_Questions_{datetime.now().strftime('%Y-%m-%d')}.pdf",
                            mime="application/pdf"
                        )

# ====================== PDF GENERATION FUNCTION ======================
def create_whole_brain_pdf(questions, tender_summary):
    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 16)
            self.set_text_color(0, 0, 0)
            self.cell(0, 10, "Whole-Brain Tender Approach", ln=1, align="C")
            self.set_font("Arial", "", 10)
            self.cell(0, 6, f"Generated on {datetime.now().strftime('%d %B %Y')}", ln=1, align="C")
            self.ln(10)

        def quadrant_title(self, title, rgb):
            self.set_font("Arial", "B", 14)
            self.set_fill_color(*rgb)
            self.set_text_color(255, 255, 255)
            self.cell(0, 12, title, ln=1, align="C", fill=True)
            self.ln(5)

    pdf = PDF()
    pdf.add_page()

    colors = {
        "A": (0, 102, 204),   # Blue
        "B": (0, 153, 0),     # Green
        "C": (204, 0, 0),     # Red
        "D": (204, 153, 0)    # Yellow
    }

    quadrant_names = {
        "A": "Quadrant A – Analytical (Blue)",
        "B": "Quadrant B – Practical (Green)",
        "C": "Quadrant C – Relational (Red)",
        "D": "Quadrant D – Conceptual (Yellow)"
    }

    for q in ["A", "B", "C", "D"]:
        pdf.quadrant_title(quadrant_names[q], colors[q])
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "", 11)
        
        for i, question in enumerate(questions.get(q, []), 1):
            pdf.multi_cell(0, 8, f"{i}. {question}")
            pdf.ln(3)
        
        pdf.add_page()  # New page for next quadrant

    return pdf.output(dest="S").encode("latin-1")
