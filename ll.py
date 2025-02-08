from flask import Flask, request, jsonify
import google.generativeai as genai
import fitz  # PyMuPDF for PDF handling
import os
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


API_KEY = "" 
genai.configure(api_key=API_KEY)

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def classify_and_generate_quiz(text):
    """Classifies text and generates a quiz."""
    prompt = f"""
    Classify the following text into one of three categories: 
    - QCM (Multiple Choice Questions)
    - Oui/Non (Yes/No Questions)
    - Courte réponse (Short Answer Questions)

    Then, generate quiz questions based on the text while keeping the same classification.

    Please return the quiz in a strictly JSON format like this:

    {{
        "classification": "<QCM / Oui/Non / Courte réponse>",
        "questions": [
            {{
                "question": "<question>",
                "options": ["<option1>", "<option2>", "<option3>", "<option4>"],  # Only for QCM
                "answer": "<correct answer>"
            }},
            ...
        ]
    }}

    Text:
    {text}
    """

    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text

@app.route('/generate-quiz', methods=['POST'])
def generate_quiz():
    """Generates a quiz from a PDF file."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Set the upload folder and ensure it exists
    upload_folder = 'uploads'
    os.makedirs(upload_folder, exist_ok=True)  # Ensure the folder exists
    pdf_path = os.path.join(upload_folder, file.filename)

    file.save(pdf_path)

    extracted_text = extract_text_from_pdf(pdf_path)
    if extracted_text:
        quiz_output = classify_and_generate_quiz(extracted_text)
        
        # Try parsing the output as JSON
        try:
            quiz_json = json.loads(quiz_output)
            return jsonify(quiz_json)
        except json.JSONDecodeError:
            return jsonify({'error': 'Failed to parse quiz data into JSON format.'}), 500
    else:
        return jsonify({'error': 'Failed to extract text from PDF.'}), 500

if __name__ == '__main__':
    app.run(debug=True)
