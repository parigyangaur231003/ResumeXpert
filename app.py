import streamlit as st
from groq import Groq
import PyPDF2 as pdf
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# Initialize Groq client
try:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
except Exception as e:
    st.error(f"❌ Failed to initialize Groq client: {str(e)}")
    st.stop()

def get_groq_response(input_text):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": input_text}
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"❌ Error getting response from Groq: {str(e)}")
        return None

def input_pdf_text(uploaded_file):
    try:
        reader = pdf.PdfReader(uploaded_file)
        text = "".join(page.extract_text() or "" for page in reader.pages)
        return text.strip() if text else None
    except Exception as e:
        st.error(f"❌ Error reading PDF: {str(e)}")
        return None

# Prompt Template
input_prompt = """
Act as an ATS (Application Tracking System) specializing in technical roles (Software Engineering, Data Science, Data Analysis, Big Data Engineering).
Analyze the following:

Resume: {text}
Job Description: {jd}

Provide your response in JSON format:
{{
  "JD Match": "X%",
  "MissingKeywords": ["keyword1", "keyword2", ...],
  "ProfileSummary": "summary text",
  "Suggestions": ["suggestion1", "suggestion2", ...]
}}
"""

# Streamlit UI
st.set_page_config(page_title="ResumeXpert", page_icon="📄", layout="wide")
st.title("📄 ResumeXpert - ATS Resume Analyzer")
st.markdown("""
**Optimize Your Resume for ATS Compliance**

This tool evaluates how well your resume matches a job description and provides actionable feedback to enhance your chances.
""")

# Instructions
with st.expander("ℹ️ How to Use"):
    st.markdown("""
    1. Paste the job description in the text area below.
    2. Upload your resume in **PDF format**.
    3. Click **Submit for Analysis**.
    4. Review your match score, missing keywords, and improvement suggestions.
    """)

# Input Fields
jd = st.text_area("📌 Paste the Job Description", height=200, placeholder="Copy and paste the full job description here...")
uploaded_file = st.file_uploader("📂 Upload Your Resume (PDF only)", type=["pdf"], help="Upload a PDF resume for analysis")
submit = st.button("🚀 Submit for Analysis", use_container_width=True)

if submit:
    if not jd.strip():
        st.warning("⚠️ Please enter a job description")
        st.stop()
    
    if uploaded_file is None:
        st.warning("⚠️ Please upload your resume")
        st.stop()
    
    with st.spinner("🔍 Analyzing your resume..."):
        text = input_pdf_text(uploaded_file)
        if text is None:
            st.error("❌ Could not extract text from the PDF. Please upload a valid resume.")
            st.stop()
        
        formatted_prompt = input_prompt.format(text=text, jd=jd)
        response = get_groq_response(formatted_prompt)
        
        if response is None:
            st.error("❌ No response received from AI. Please try again.")
            st.stop()
        
        try:
            result = json.loads(response)
            
            # Display results
            st.success("✅ Analysis Complete!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📊 Match Score", result.get("JD Match", "N/A"))
            with col2:
                missing_keywords = result.get("MissingKeywords", [])
                st.metric("🔎 Missing Keywords", len(missing_keywords))
            
            # Profile Summary
            with st.expander("📝 Profile Summary", expanded=True):
                st.write(result.get("ProfileSummary", "No summary provided"))
            
            # Missing Keywords
            with st.expander("🔎 Missing Keywords"):
                if missing_keywords:
                    st.write(", ".join(missing_keywords))
                else:
                    st.info("No significant missing keywords found")
            
            # Improvement Suggestions
            with st.expander("💡 Improvement Suggestions"):
                suggestions = result.get("Suggestions", [])
                if suggestions:
                    for i, suggestion in enumerate(suggestions, 1):
                        st.markdown(f"{i}. {suggestion}")
                else:
                    st.info("No specific suggestions available")
            
            # Raw response (debugging)
            if st.checkbox("🛠 Show Raw Response"):
                st.code(json.dumps(result, indent=2))
                
        except json.JSONDecodeError:
            st.error("❌ The response format was not as expected. Displaying raw response:")
            st.code(response)
