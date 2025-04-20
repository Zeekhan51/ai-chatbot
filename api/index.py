import os
import google.generativeai as genai
from flask import Flask, request, jsonify

app = Flask(__name__)

# Use environment variable for API key
genai.configure(api_key=os.environ.get("AIzaSyDreaNAgCWpZfEoWyBGKM-nvphuUUh7JDE"))

# [Keep all your original code from healthcare_gemini.py here]
# [Include profile management, chat handling, and upload endpoints]

# Remove the app.run() line at the bottom
