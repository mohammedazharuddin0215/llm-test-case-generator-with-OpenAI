import streamlit as st
from litellm import completion
from PIL import Image
import pytesseract
import streamlit as st
from litellm import completion
from PIL import Image
import os
os.system("pip install litellm==1.78.4 --quiet")
from dotenv import load_dotenv




pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import docx

st.set_page_config(page_title="AI Test Case Generator", layout="wide")

st.title("🧠 AI Test Case Generator")
st.write("Choose how you want to provide input and generate **detailed Positive and Negative test cases** automatically.")

# --- Option selection ---
option = st.radio(
    "Select Input Type:",
    [
        "1️⃣ Manual Description",
        "2️⃣ Upload Design (Image / UI Screenshot)",
        "3️⃣ Upload Requirement Document (PDF / DOCX / TXT)"
    ]
)

input_text = ""

# --- Option 1: Manual Entry ---
if option == "1️⃣ Manual Description":
    input_text = st.text_area("Enter your screen or functionality details:", placeholder="e.g., Payment Flow with Amount, Pay Now, and Cancel buttons")

# --- Option 2: Upload Design ---
elif option == "2️⃣ Upload Design (Image / UI Screenshot)":
    uploaded_file = st.file_uploader("Upload Design (PNG, JPG, JPEG):", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Design", use_container_width=True)
        st.info("Extracting text from design...")
        input_text = pytesseract.image_to_string(image)
        st.success("Extracted text from image:")
        st.text_area("Detected Text", input_text, height=200)

# --- Option 3: Upload Requirement Document ---
elif option == "3️⃣ Upload Requirement Document (PDF / DOCX / TXT)":
    uploaded_doc = st.file_uploader("Upload requirement file:", type=["pdf", "docx", "txt"])
    if uploaded_doc is not None:
        if uploaded_doc.type == "application/pdf":
            with pdfplumber.open(uploaded_doc) as pdf:
                input_text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
        elif uploaded_doc.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_doc)
            input_text = "\n".join([para.text for para in doc.paragraphs])
        else:  # txt
            input_text = uploaded_doc.read().decode("utf-8")

        st.success("Extracted requirement text:")
        st.text_area("Extracted Content", input_text, height=200)

# --- Generate Test Cases ---
if st.button("🚀 Generate Test Cases"):
    if input_text.strip():
        with st.spinner("Generating detailed test cases..."):
            try:
                full_prompt = f"""
You are an experienced QA test case designer.
Based on the provided description or design or requirement document, generate **detailed positive and negative test cases**.

Description/Extracted Requirement:
{input_text}

Requirements:
- Divide test cases into **Positive Test Cases** and **Negative Test Cases** sections.
- Use a **table format** with columns:
  1. Functionality
  2. Test Summary
  3. Precondition
  4. Expected Result
- Include validation for **fields, UI controls, actions, boundaries, mandatory checks, and error messages**.
- Cover edge cases, form submission, and button workflows.
- Make sure all functional aspects are covered.

Now generate the full detailed test cases.
"""

                response = completion(
                    model="ollama/mistral",
                    messages=[{"role": "user", "content": full_prompt}],
                )
                result = response["choices"][0]["message"]["content"]
                st.success("✅ Detailed Test Cases Generated Successfully!")
                st.markdown(result)
            except Exception as e:
                st.error(f"Error generating test cases: {str(e)}")
    else:
        st.warning("Please provide a description, design, or document first.")
