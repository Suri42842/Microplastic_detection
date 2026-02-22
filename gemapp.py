import os
import google.generativeai as genai
from flask import Flask, request, render_template_string
import PIL.Image

app = Flask(__name__)

# --- CONFIGURATION ---
API_KEY = 'x'
genai.configure(api_key=API_KEY)

# UPDATED: Using the model from your list
MODEL_NAME = 'gemini-flash-latest'

def analyze_with_gemini(image_path):
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        img = PIL.Image.open(image_path)
        
        # UPDATED PROMPT: Asking for a detailed analysis instead of just one word
        prompt = """
        You are an expert researcher in microplastics. Analyze this image and provide a report in the following format:

        1. **Classification**: Identify the object as one of these types: Fiber, Film, Fragment, or Pellet.
        2. **Visual Analysis**: Describe what you see in the image. Mention the shape (e.g., thread-like, irregular, spherical), the color, and the texture.
        3. **Reasoning**: Explain why you chose this category. For example, "It is classified as a Fiber because the length is significantly greater than the width."
        
        Keep the tone scientific but easy to understand.
        """
        
        response = model.generate_content([prompt, img])
        return response.text
        
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    result = None
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"

        # Save temporarily
        if not os.path.exists('static'):
            os.makedirs('static')
        
        filepath = os.path.join('static', file.filename)
        file.save(filepath)

        result = analyze_with_gemini(filepath)

    # HTML to display the result nicely
    html = """
    <!doctype html>
    <title>Microplastic Analysis</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .box { border: 2px solid #333; padding: 20px; border-radius: 10px; background-color: #f9f9f9; }
        .result-text { white-space: pre-wrap; text-align: left; } 
        h1 { color: #0056b3; }
        input[type=submit] { background-color: #0056b3; color: white; padding: 10px 20px; border: none; cursor: pointer; }
    </style>

    <h1>Microplastic Smart Detector</h1>
    
    <div class="box">
        <form method=post enctype=multipart/form-data>
          <p>Upload your microscope image:</p>
          <input type=file name=file>
          <input type=submit value="Analyze Image">
        </form>
    </div>

    {% if result %}
        <br>
        <h2>Analysis Result:</h2>
        <div class="box">
            <div class="result-text">{{ result }}</div>
        </div>
    {% endif %}
    """
    return render_template_string(html, result=result)

if __name__ == '__main__':
    app.run(debug=True)
