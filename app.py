import streamlit as st
import pandas as pd
from generator import TestCaseGenerator
import os
from datetime import datetime
from save_excel import test_cases_to_excel


def extract_text_from_image(uploaded_file):
    try:
        from PIL import Image
        import pytesseract
    except Exception:
        st.error("OCR libraries (Pillow/pytesseract) are not installed. Install them to extract text from images.")
        return ""

    image = Image.open(uploaded_file)
    text = pytesseract.image_to_string(image)
    return text


def extract_text_from_document(uploaded_file):
    # Try PDF and docx parsing if libraries are available
    try:
        import pdfplumber
    except Exception:
        pdfplumber = None
    try:
        import docx
    except Exception:
        docx = None

    content = ""
    if uploaded_file.type == "application/pdf" and pdfplumber:
        with pdfplumber.open(uploaded_file) as pdf:
            pages = [p.extract_text() for p in pdf.pages]
            content = "\n".join([p for p in pages if p])
    elif uploaded_file.type in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword") and docx:
        document = docx.Document(uploaded_file)
        content = "\n".join([p.text for p in document.paragraphs])
    else:
        try:
            content = uploaded_file.read().decode("utf-8")
        except Exception:
            st.warning("Unable to extract text from the uploaded document. Consider converting it to TXT or ensure required parsing libraries are installed.")

    return content


def main():
    st.title("Test Case Generator")

    st.markdown("## Generate detailed positive & negative test cases from your requirement or design files.")
    st.write("Select input type and provide the requirement. The generator will return structured test cases covering positive, negative and edge cases.")

    option = st.radio("Select Input Type:", ["1️⃣ Manual Description", "2️⃣ Upload Design/Image", "3️⃣ Upload Requirement Document"])

    input_text = ""

    # Show the appropriate input control based on the selected radio option.
    if "Manual" in option or "Description" in option:
        input_text = st.text_area("Enter requirement / description:", height=200, placeholder="Describe the feature, screen or user flow here...")

    elif "Design" in option or "Image" in option:
        uploaded = st.file_uploader("Upload image (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])
        if uploaded is not None:
            try:
                st.image(uploaded, caption="Uploaded image", use_column_width=True)
            except Exception:
                st.write("Uploaded image preview not available.")
            st.info("Extracting text from the uploaded image (OCR)...")
            input_text = extract_text_from_image(uploaded)
            if input_text:
                st.success("Text extracted from image:")
                st.text_area("Extracted text:", value=input_text, height=200)
            else:
                st.warning("No text detected in the image or OCR not available.")

    elif "Document" in option or "Requirement" in option:
        uploaded = st.file_uploader("Upload document (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
        if uploaded is not None:
            st.info("Extracting text from the uploaded document...")
            input_text = extract_text_from_document(uploaded)
            if input_text:
                st.success("Text extracted from document:")
                st.text_area("Extracted text:", value=input_text, height=200)
            else:
                st.warning("No text could be extracted from the document.")

    # Info and generate button
    st.write("")
    st.info("The generator will automatically produce comprehensive Positive, Negative and Edge test cases for the provided input.")

    if st.button("🚀 Generate Test Cases"):
        if not input_text or not input_text.strip():
            st.warning("Please provide input via the selected mode first.")
        else:
            with st.spinner("Generating comprehensive test cases (positive, negative, edge)..."):
                generator = TestCaseGenerator()
                # Use automatic comprehensive counts - adjust here if you want different defaults
                result = generator.generate_test_cases(input_text, positive=20, negative=20, edge=5)


                # result may be list(dict) or raw string
                if not result:
                    st.error("Failed to generate test cases. Check logs or API quota.")
                    return

                parsed_list = None

                if isinstance(result, list):
                    parsed_list = result

                elif isinstance(result, str):
                    # Try to parse JSON directly
                    import json as _json
                    try:
                        parsed = _json.loads(result)
                        if isinstance(parsed, list):
                            parsed_list = parsed
                        elif isinstance(parsed, dict):
                            parsed_list = [parsed]
                    except Exception:
                        # Try to locate JSON substring
                        try:
                            start = result.index('[')
                            end = result.rindex(']') + 1
                            json_str = result[start:end]
                            parsed = _json.loads(json_str)
                            if isinstance(parsed, list):
                                parsed_list = parsed
                            elif isinstance(parsed, dict):
                                parsed_list = [parsed]
                        except Exception:
                            # Try to parse markdown table (| col | col |) into DataFrame
                            try:
                                import io
                                lines = [l.strip() for l in result.splitlines() if l.strip()]
                                table_lines = [l for l in lines if '|' in l]
                                if table_lines:
                                    md = '\n'.join(table_lines)
                                    # Remove leading/trailing pipes
                                    md = '\n'.join([ln.strip().strip('|') for ln in md.splitlines()])
                                    df = pd.read_csv(io.StringIO(md), sep=r'\|', engine='python')
                                    parsed_list = df.to_dict(orient='records')
                            except Exception:
                                parsed_list = None

                if not parsed_list:
                    # Could not parse into structured list - show raw output so user can inspect
                    st.subheader("Raw output from model (unstructured)")
                    st.text_area("Model output", value=result if isinstance(result, str) else str(result), height=800)
                    return

                # Normalize parsed_list entries into table-friendly dicts
                rows = []
                for tc in parsed_list:
                    if not isinstance(tc, dict):
                        continue
                    steps = tc.get('Test Steps') or tc.get('TestSteps') or tc.get('Steps') or []
                    if isinstance(steps, list):
                        steps_text = '\n'.join([str(s) for s in steps])
                    else:
                        steps_text = str(steps)

                    test_data = tc.get('Test Data') or tc.get('TestData') or ''
                    if isinstance(test_data, dict):
                        # Pretty print dict as key: value pairs
                        td = ', '.join([f"{k}: {v}" for k, v in test_data.items()])
                    else:
                        td = str(test_data)

                    rows.append({
                        'Functionality': tc.get('Functionality', tc.get('Function', '')),
                        'Test Summary': tc.get('Test Summary', tc.get('Summary', '')),
                        'Pre Condition': tc.get('Pre Condition', tc.get('Precondition', '')),
                        'Test Data': td,
                        'Test Steps': steps_text,
                        'Expected Result': tc.get('Expected Result', tc.get('Expected', ''))
                    })

                if not rows:
                    st.subheader("Raw output from model (no structured test cases found)")
                    st.text_area("Model output", value=str(result), height=900)
                    return

                df = pd.DataFrame(rows, columns=['Functionality', 'Test Summary', 'Pre Condition', 'Test Data', 'Test Steps', 'Expected Result'])
                st.subheader("Generated Test Cases (table)")
                st.dataframe(df)

                # Save to excel
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join("outputs", f"testcases_{timestamp}.xlsx")
                saved = test_cases_to_excel(rows, filename)
                st.success(f"Saved to {saved}")

                # Download button
                with open(saved, "rb") as fh:
                    st.download_button("Download Excel", data=fh, file_name=os.path.basename(saved))
if __name__ == "__main__":
    # When run with `streamlit run app.py`, __name__ == "__main__" and main() will execute.
    # This keeps the module import-safe while ensuring the Streamlit app runs when executed.
    main()
