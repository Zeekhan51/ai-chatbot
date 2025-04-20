# healthcare_gemini.py
import os
import google.generativeai as genai
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import tempfile

app = Flask(__name__)

# Configure Gemini with your API key
genai.configure(api_key="AIzaSyDreaNAgCWpZfEoWyBGKM-nvphuUUh7JDE")

# Initialize Gemini models
health_model = genai.GenerativeModel('gemini-pro')
vision_model = genai.GenerativeModel('gemini-pro-vision')

# In-memory user profiles (for demonstration, use database in production)
user_profiles = {}

# Health assessment guidelines
SYSTEM_PROMPT = """You are a certified healthcare assistant. Follow these rules:
1. Provide professional medical/nutrition advice
2. Consider user profile: {profile}
3. For symptoms: ask severity, duration, other symptoms
4. Never diagnose - suggest doctor consultation for serious issues
5. For nutrition: suggest diet charts with calories
6. Explain medical terms simply
7. Include preventive measures
8. Highlight urgent care needs
9. Mention possible drug interactions if medications listed"""

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_profile_context(user_id):
    profile = user_profiles.get(user_id, {})
    return f"""
    Patient Profile:
    Name: {profile.get('name', 'Not provided')}
    Age: {profile.get('age', 'Not provided')}
    Weight: {profile.get('weight', 'Not provided')} kg
    Height: {profile.get('height', 'Not provided')} cm
    Medical Conditions: {profile.get('conditions', 'None')}
    Allergies: {profile.get('allergies', 'None')}
    Fitness Goals: {profile.get('goals', 'Not specified')}
    Dietary Preferences: {profile.get('diet', 'Regular')}
    """

@app.route('/profile', methods=['POST'])
def manage_profile():
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    
    if user_id not in user_profiles:
        user_profiles[user_id] = {}
    
    profile = user_profiles[user_id]
    updates = request.json.get('updates', {})
    
    # Update profile fields
    for field in ['name', 'age', 'weight', 'height', 
                  'conditions', 'allergies', 'goals', 'diet']:
        if field in updates:
            profile[field] = updates[field]
    
    return jsonify({"message": "Profile updated", "profile": profile})

@app.route('/chat', methods=['POST'])
def handle_chat():
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')
    image = data.get('image')
    
    if not user_id or not message:
        return jsonify({"error": "user_id and message required"}), 400
    
    # Get user profile
    profile_context = get_profile_context(user_id)
    
    try:
        if image:
            # Image analysis for nutrition
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                tmp.write(image.read())
                response = vision_model.generate_content([
                    "Analyze this food image. List: 1. Nutrients (carbs, proteins, fats, vitamins, minerals)"
                    "2. Calories per 100g 3. Health benefits 4. Allergens 5. Diet recommendations based on:",
                    profile_context,
                    genai.types.Part.from_image(tmp.name)
                ])
                os.unlink(tmp.name)
        else:
            # Health conversation
            prompt = SYSTEM_PROMPT.format(profile=profile_context) + f"\n\nUser: {message}"
            response = health_model.generate_content(prompt)
        
        return jsonify({
            "response": response.text,
            "profile": user_profiles.get(user_id, {})
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400
    
    try:
        return handle_chat()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
