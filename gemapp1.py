import os
import json
import google.generativeai as genai
from flask import Flask, request, render_template_string
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

# --- CONFIGURATION ---
API_KEY = 'AIzaSyCDFscjtk9gWA2PFLQ5LsN2sRA5xTKbySs'   # <--- Make sure your key is here
genai.configure(api_key=API_KEY)

MODEL_NAME = 'gemini-flash-latest'

def draw_bounding_boxes(image_path, boxes_data):
    """
    Draws boxes based on the list of coordinates provided by the AI.
    """
    try:
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        width, height = img.size
        detected_items = []

        for item in boxes_data:
            # Convert 0-1000 scale to real pixels
            box_ymin = (item["ymin"] / 1000) * height
            box_xmin = (item["xmin"] / 1000) * width
            box_ymax = (item["ymax"] / 1000) * height
            box_xmax = (item["xmax"] / 1000) * width
            label = item["label"]

            # Draw the red box (Thickness 5)
            draw.rectangle([box_xmin, box_ymin, box_xmax, box_ymax], outline="red", width=5)
            
            # Draw label background and text
            try:
                # Try larger font if available, else default
                font = ImageFont.truetype("arial.ttf", 20) 
            except:
                font = ImageFont.load_default()
            
            # Draw red background for text
            draw.rectangle([box_xmin, box_ymin - 25, box_xmin + 150, box_ymin], fill="red")
            draw.text((box_xmin + 5, box_ymin - 25), label, fill="white", font=font)
            
            detected_items.append(label)

        # Save result
        result_path = image_path.replace(".", "_detected.")
        img.save(result_path)
        return result_path, detected_items

    except Exception as e:
        return None, f"Drawing Error: {str(e)}"

def analyze_and_detect(image_path):
    # We ask for JSON so we can separate the "Report" from the "Boxes"
    model = genai.GenerativeModel(
        MODEL_NAME,
        generation_config={"response_mime_type": "application/json"}
    )
    img = Image.open(image_path)
    
    # --- UPDATED PROMPT ---
    # This prompt asks for BOTH the text analysis AND the boxes
    prompt = """
    Analyze this image of microplastics. Perform two tasks and return a JSON object.

    1. "report": Write a scientific analysis text (no markdown formatting inside the string). 
       - Identify the morphology (shape).
       - Classify it 
       - Describe characteristics (color, texture).
       - Predict the likely source (e.g., clothing, packaging).
    
    2. "boxes": Detect all plastic items. Return a list of bounding boxes.
       - Keys: ymin, xmin, ymax, xmax, label.
       - Scale: 0 to 1000.

    Output JSON Format:
    {
      "report": "1. Analysis of Your Image... 2. Categories...",
      "boxes": [
         {"ymin": 100, "xmin": 100, "ymax": 200, "xmax": 200, "label": "Fiber"}
      ]
    }
    """
    
    try:
        response = model.generate_content([prompt, img])
        return json.loads(response.text) # Parse JSON immediately
    except Exception as e:
        return {"error": str(e)}

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    original_img = None
    processed_img = None
    item_list = []
    analysis_report = None
    error_msg = None
    
    if request.method == 'POST':
        if 'file' not in request.files: return "No file"
        file = request.files['file']
        if file.filename == '': return "No file"

        if not os.path.exists('static'): os.makedirs('static')
        filepath = os.path.join('static', file.filename)
        file.save(filepath)
        original_img = filepath

        # 1. Ask AI (Get both Report and Boxes)
        ai_result = analyze_and_detect(filepath)
        
        if "error" in ai_result:
            error_msg = ai_result["error"]
        else:
            # 2. Extract the Text Report
            analysis_report = ai_result.get("report", "No report generated.")
            
            # 3. Draw the Boxes
            boxes = ai_result.get("boxes", [])
            if boxes:
                processed_path, items = draw_bounding_boxes(filepath, boxes)
                if processed_path:
                    processed_img = processed_path
                    item_list = items
            else:
                error_msg = "No microplastics detected in the image."

    # HTML Template
    html = """
    <!doctype html>
    <style>
        body { font-family: sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }
        .container { display: flex; gap: 20px; margin-top: 20px; }
        .image-box { flex: 1; text-align: center; }
        img { max-width: 100%; border: 2px solid #333; border-radius: 8px; }
        .report-box { 
            background: #f4f4f4; padding: 20px; border-left: 5px solid #007bff; 
            white-space: pre-wrap; margin-bottom: 20px; text-align: left;
        }
        h1 { color: #007bff; text-align: center; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; font-size: 16px; }
    </style>

    <h1>Microplastic Analysis & Detection</h1>
    
    <div style="text-align: center;">
        <form method=post enctype=multipart/form-data>
          <input type=file name=file required>
          <input type=submit value="Analyze Image" class="btn">
        </form>
    </div>

    {% if error_msg %}
        <h3 style="color:red; text-align: center;">{{ error_msg }}</h3>
    {% endif %}

    {% if analysis_report %}
        <h2>1. Scientific Analysis Report</h2>
        <div class="report-box">{{ analysis_report }}</div>
    {% endif %}

    {% if processed_img %}
        <h2>2. Detection Results</h2>
        <div class="container">
            <div class="image-box">
                <h3>Original Image</h3>
                <img src="{{ original_img }}">
            </div>
            <div class="image-box">
                <h3>AI Detection</h3>
                <img src="{{ processed_img }}">
                <p><strong>Detected:</strong> {{ item_list }}</p>
            </div>
        </div>
    {% endif %}
    """
    return render_template_string(html, original_img=original_img, processed_img=processed_img, item_list=item_list, analysis_report=analysis_report, error_msg=error_msg)

if __name__ == '__main__':
    app.run(debug=True)
