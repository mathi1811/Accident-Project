import streamlit as st
from ultralytics import YOLO
from PIL import Image
import os
import tempfile
import easyocr
import re
import json
import requests
import numpy as np
import csv
from datetime import datetime
import cv2

# Initialize session state
if 'show_ocr_form' not in st.session_state:
    st.session_state['show_ocr_form'] = False
if 'video_ocr_results' not in st.session_state:
    st.session_state.video_ocr_results = []

# Deployment debug tag (to ensure your current container is running latest code)
st.markdown("""
<div style='font-size:0.85rem; padding: 8px 12px; border-left: 4px solid #28a745; background: rgba(40, 167, 69, 0.1); margin-bottom:10px; color:#155724;'>
    <strong>App version:</strong> a424dd2 (should align with latest main commit)
    — If this shows old commit, redeploy in Streamlit Cloud.
</div>
""", unsafe_allow_html=True)

# Custom CSS for full-screen attractive styling with backgrounds
st.markdown("""
<style>
    /* Global font settings for better readability */
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    /* Full screen layout */
    .main {
        background: #ffffff;
        min-height: 100vh;
        width: 100vw;
        margin: 0;
        padding: 0;
    }

    /* App container with subtle colored background */
    .block-container {
        border: 1px solid #e5e7eb;
        background: #ffffff;
        border-radius: 0;
        margin: 0;
        padding: 20px;
        min-height: 100vh;
        box-shadow: none;
        width: 100%;
        max-width: none;
        position: relative;
    }

    .block-container::before { display: none; }

    /* Title with clean, professional styling */
    .title {
        font-size: 2.4em;
        font-weight: 700;
        text-align: center;
        margin-bottom: 20px;
        color: #0f172a;
        padding: 10px 14px;
        border-radius: 6px;
        background: transparent;
        border: none;
        width: 100%;
        box-sizing: border-box;
        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
        letter-spacing: 0.5px;
        line-height: 1.1;
    }

    .title::before, .title::after { content: none; }

    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(-50%) scale(1); }
        40% { transform: translateY(-50%) scale(1.2); }
        60% { transform: translateY(-50%) scale(0.9); }
    }

    .subtitle {
        font-size: 1.1em;
        text-align: center;
        margin-bottom: 20px;
        font-weight: 500;
        color: #334155;
        background: transparent;
        padding: 8px 12px;
        border-radius: 0;
        border: none;
        width: 100%;
        box-sizing: border-box;
        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
        line-height: 1.4;
        letter-spacing: 0.2px;
    }

    .subtitle::before { content: none; }
    
    /* Special styling for How it Works section */
    .how-it-works-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: none;
        border: 1px solid #e5e7eb;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        position: relative;
        overflow: visible;
        border-left: 5px solid #e5e7eb;
    }

    .how-it-works-card::before { content: none; }

    .how-it-works-card:hover {
        transform: none;
        box-shadow: none;
    }

    .how-it-works-card > * {
        position: relative;
        z-index: 2;
    }

    /* Special styling for Features section */
    .features-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: none;
        border: 1px solid #e5e7eb;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        position: relative;
        overflow: visible;
        border-left: 5px solid #e5e7eb;
    }

    .features-card::before { content: none; }

    .features-card:hover {
        transform: none;
        box-shadow: none;
    }

    .features-card > * {
        position: relative;
        z-index: 2;
    }

    /* Enhanced list styling with vibrant colors */
    .how-it-works-card h3 {
        color: #0f172a !important;
        font-size: 1.6em;
        font-weight: 700;
        margin-bottom: 12px;
        text-shadow: none;
        background: transparent;
        padding: 0;
        border-radius: 0;
        border: none;
    }

    .how-it-works-card ol {
        padding-left: 25px;
        counter-reset: step-counter;
    }

    .how-it-works-card li {
        margin-bottom: 12px;
        padding: 10px 14px;
        background: #ffffff;
        border-radius: 6px;
        border-left: 4px solid #e5e7eb;
        transition: all 0.4s ease;
        position: relative;
        counter-increment: step-counter;
        font-size: 1.1em;
        font-weight: 600;
        color: #1f2937;
    }

    .how-it-works-card li::before {
        content: counter(step-counter);
        position: absolute;
        left: -15px;
        top: 50%;
        transform: translateY(-50%);
        background: #3b82f6;
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 0.85em;
        box-shadow: 0 2px 4px rgba(15, 23, 42, 0.1);
    }

    .how-it-works-card li:hover {
        background: #f9fafb;
        transform: none;
        box-shadow: none;
        border-left-color: #e5e7eb;
    }

    .how-it-works-card strong {
        color: #0f172a;
        font-weight: 700;
        text-shadow: none;
    }

    .features-card h4 {
        color: #0f172a !important;
        font-size: 1.6em;
        font-weight: 700;
        margin-bottom: 12px;
        text-shadow: none;
        background: transparent;
        padding: 0;
        border-radius: 0;
        border: none;
    }

    .features-card ul {
        list-style: none;
        padding: 0;
    }

    .features-card li {
        margin-bottom: 10px;
        padding: 10px 14px;
        background: #ffffff;
        border-radius: 6px;
        border-left: 4px solid #e5e7eb;
        transition: all 0.4s ease;
        position: relative;
        font-size: 1.1em;
        font-weight: 600;
        color: #1f2937;
    }

    .features-card li::before {
        content: '✓';
        position: absolute;
        left: -12px;
        top: 50%;
        transform: translateY(-50%);
        background: #22c55e;
        color: white;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 0.75em;
        box-shadow: 0 2px 4px rgba(15, 23, 42, 0.1);
    }

    .features-card li:hover {
        background: #f9fafb;
        transform: none;
        box-shadow: none;
        border-left-color: #e5e7eb;
    }

    .card::before { display: none; }

    .card:hover {
        transform: none;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.12);
    }

    .card > * {
        position: relative;
        z-index: 2;
    }

    /* Card variants with different background colors */
    .card-danger {
        background: #fee2e2;
        border-left: 4px solid #dc2626;
    }

    .card-danger::after { content: none; }

    .card-success {
        background: #d1fae5;
        border-left: 4px solid #16a34a;
    }

    .card-success::after { content: none; }

    .card-warning {
        background: #fef9c3;
        border-left: 4px solid #ca8a04;
    }

    .card-warning::after { content: none; }
    
    /* Enhanced button styling with vibrant gradients */
    .stButton>button {
        background: #ffffff;
        color: #1f2937;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 700;
        font-size: 15px;
        transition: all 0.2s ease;
        box-shadow: none;
        position: relative;
        overflow: visible;
        width: 100%;
        margin: 10px 0;
        text-transform: none;
        letter-spacing: 0.2px;
    }

    .stButton>button::before { content: none; }

    .stButton>button:hover {
        background: #ffffff;
        transform: none;
        box-shadow: none;
        border-color: #d1d5db;
    }

    .stButton>button:active {
        transform: translateY(-1px); 
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.2);
    }

    /* Danger button variant with vibrant red gradient */
    .stButton>button[data-testid*="detect"] {
        background: #f9fafb;
        border-color: #d1d5db;
        color: #1f2937;
        box-shadow: none;
    }

    .stButton>button[data-testid*="detect"]:hover {
        background: #ffffff;
        box-shadow: none;
    }

    /* Success button variant with vibrant green gradient */
    .stButton>button[data-testid*="ocr"] {
        background: #f9fafb;
        border-color: #d1d5db;
        color: #1f2937;
        box-shadow: none;
    }

    .stButton>button[data-testid*="ocr"]:hover {
        background: #ffffff;
        box-shadow: none;
    }
    
    /* File uploader styling with vibrant design */
    .uploadedFile {
        border: 1px solid #d1d5db;
        border-radius: 12px;
        padding: 28px 20px;
        text-align: center;
        background: #ffffff;
        transition: all 0.2s ease;
        position: relative;
        overflow: visible;
        width: 100%;
        margin: 20px 0;
        box-shadow: none;
    }

    .uploadedFile::before { content: none; }

    .uploadedFile:hover {
        border-color: #d1d5db;
        background: #ffffff;
        transform: none;
        box-shadow: none;
    }

    .uploadedFile::after {
        content: 'Drop your image here or click to browse';
        position: absolute;
        bottom: 18px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 1.0em;
        color: #1f2937;
        font-weight: 500;
        opacity: 0.75;
        text-shadow: none;
        z-index: 2;
        letter-spacing: 0.1px;
    }
    
    /* Enhanced message styling with icons */
    .success-msg {
        background: #f7fdf8;
        color: #0f172a;
        border: 1px solid #d1d5db;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        position: relative;
        box-shadow: none;
    }
    
    .success-msg::before {
        content: '✅';
        font-size: 1.5em;
        margin-right: 10px;
    }
    
    .warning-msg {
        background: #fefcf2;
        color: #0f172a;
        border: 1px solid #d1d5db;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        position: relative;
        box-shadow: none;
    }
    
    .warning-msg::before {
        content: '⚠️';
        font-size: 1.5em;
        margin-right: 10px;
    }
    
    .error-msg {
        background: #fff5f5;
        color: #0f172a;
        border: 1px solid #d1d5db;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        position: relative;
        box-shadow: none;
    }
    
    .error-msg::before {
        content: '❌';
        font-size: 1.5em;
        margin-right: 10px;
    }
    
    /* Detection results styling with enhanced colors */
    .detection-result {
        background: linear-gradient(135deg, #e7f3ff 0%, #d4e8ff 100%);
        border: 3px solid #007bff;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        position: relative;
        box-shadow: 0 6px 20px rgba(0, 123, 255, 0.2);
    }
    
    .detection-result::before {
        content: '🎯';
        position: absolute;
        top: 10px;
        right: 15px;
        font-size: 2em;
        opacity: 0.7;
    }
    
    /* OCR results styling */
    .ocr-result {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 3px solid #17a2b8;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        position: relative;
        box-shadow: 0 6px 20px rgba(23, 162, 184, 0.2);
    }
    
    .ocr-result::before {
        content: '🔤';
        position: absolute;
        top: 10px;
        right: 15px;
        font-size: 2em;
        opacity: 0.7;
    }
    
    /* Enhanced spinner styling */
    .stSpinner {
        text-align: center;
        padding: 20px;
    }
    
    .stSpinner > div > div {
        border-color: #007bff transparent transparent transparent;
        border-width: 4px;
    }
    
    /* Column styling */
    .css-1lcbmhc {
        background: rgba(255, 255, 255, 0.8);
        border-radius: 10px;
        padding: 15px;
        margin: 5px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Footer with enhanced full-screen styling */
    .footer {
        text-align: center;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #3a7bd5 100%);
        color: white;
        margin-top: 50px;
        padding: 40px 20px;
        border-radius: 0;
        box-shadow: 0 -8px 30px rgba(0, 0, 0, 0.3);
        position: relative;
        width: 100vw;
        left: 50%;
        transform: translateX(-50%);
        backdrop-filter: blur(10px);
    }

    .footer::before {
        content: '🚨 🚨 🚨';
        font-size: 2.5em;
        display: block;
        margin-bottom: 15px;
        animation: blink 2s infinite;
    }

    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.7; }
    }

    /* Make all columns full width on mobile */
    @media (max-width: 768px) {
        .css-1lcbmhc {
            width: 100% !important;
            margin: 10px 0 !important;
        }

        .card {
            margin: 10px 0 !important;
            padding: 20px !important;
        }

        .stButton>button {
            font-size: 16px !important;
            padding: 12px 20px !important;
        }
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #28a745, #20c997, #17a2b8);
    }
    
    /* Sidebar styling if used */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Enhanced text input styling */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 2px solid rgba(102, 126, 234, 0.3);
        padding: 12px 18px;
        transition: all 0.3s ease;
        background: rgba(255, 255, 255, 0.9);
        font-size: 16px;
        font-weight: 600;
        color: #2c3e50;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
    }

    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
        background: rgba(255, 255, 255, 1);
        transform: scale(1.02);
    }

    .stTextInput > div > div > input::placeholder {
        color: #7f8c8d;
        font-weight: 500;
    }    /* Full screen layout adjustments */
    .css-18e3th9 {
        width: 100% !important;
        max-width: none !important;
        padding: 0 !important;
    }

    .css-1d391kg {
        width: 100% !important;
        max-width: none !important;
    }

    /* Remove Streamlit default margins */
    .css-1adrfps {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Background image overlays for different sections */
    .detection-section {
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="traffic" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="10" cy="10" r="2" fill="rgba(255,255,255,0.1)"/><path d="M5 5 L15 15 M15 5 L5 15" stroke="rgba(255,255,255,0.1)" stroke-width="1"/></pattern></defs><rect width="100" height="100" fill="url(%23traffic)"/></svg>');
        background-size: 100px 100px;
        border-radius: 20px;
        padding: 20px;
        margin: 20px 0;
    }

    .ocr-section {
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="scan" width="15" height="15" patternUnits="userSpaceOnUse"><rect x="2" y="2" width="11" height="11" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="1"/><line x1="5" y1="5" x2="10" y2="10" stroke="rgba(255,255,255,0.1)" stroke-width="1"/><line x1="10" y1="5" x2="5" y2="10" stroke="rgba(255,255,255,0.1)" stroke-width="1"/></pattern></defs><rect width="100" height="100" fill="url(%23scan)"/></svg>');
        background-size: 75px 75px;
        border-radius: 20px;
        padding: 20px;
        margin: 20px 0;
    }

    .sms-section {
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="message" width="25" height="25" patternUnits="userSpaceOnUse"><path d="M5 5 L20 5 L20 15 L12.5 20 L5 15 Z" fill="rgba(255,255,255,0.1)" stroke="rgba(255,255,255,0.1)" stroke-width="1"/><circle cx="8" cy="8" r="1" fill="rgba(255,255,255,0.2)"/><circle cx="12" cy="8" r="1" fill="rgba(255,255,255,0.2)"/><circle cx="16" cy="8" r="1" fill="rgba(255,255,255,0.2)"/></pattern></defs><rect width="100" height="100" fill="url(%23message)"/></svg>');
        background-size: 125px 125px;
        border-radius: 20px;
        padding: 20px;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Basic startup check
try:
    # Test that we can import all required modules
    import streamlit as st
    from ultralytics import YOLO
    from PIL import Image
    import easyocr
    import numpy as np
    import csv
    from datetime import datetime
    
    # Test model file exists
    MODEL_PATH = "runs/accident_detector2/weights/best.pt"
    if not os.path.exists(MODEL_PATH):
        st.error(f"Model file not found: {MODEL_PATH}")
        st.stop()
    
    STARTUP_OK = True
except Exception as e:
    st.error(f"Startup error: {e}")
    STARTUP_OK = False
    st.stop()

if not STARTUP_OK:
    st.stop()

def log_report(payload, result):
    # Try multiple possible log locations for deployment compatibility
    possible_paths = [
        "runs/reports.csv",
        "/tmp/reports.csv",
        "./reports.csv"
    ]
    
    log_written = False
    for log_path in possible_paths:
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            
            is_new = not os.path.exists(log_path)
            with open(log_path, "a", newline="") as f:
                writer = csv.writer(f)
                if is_new:
                    writer.writerow(["timestamp", "plate", "confidence", "location", "status", "sid", "error", "raw_result"])
                writer.writerow([
                    datetime.now().isoformat(),
                    payload.get("plate"),
                    payload.get("confidence"),
                    (payload.get("extra") or {}).get("location"),
                    result.get("status"),
                    result.get("sid", ""),
                    result.get("error", ""),
                    str(result)
                ])
            log_written = True
            break  # Success, no need to try other paths
        except Exception as e:
            continue  # Try next path
    
    # Only show debug messages if logging failed completely
    if not log_written:
        try:
            st = __import__('streamlit')
            st.warning("Could not write to any log location. Reports will not be saved.")
        except Exception:
            pass



st.markdown('<h1 class="title">Accident Detection & License Plate OCR</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Advanced AI-powered accident detection with automatic license plate recognition and emergency reporting</p>', unsafe_allow_html=True)

# Add input type selection
input_type = st.radio("Select Input Type", ["Image", "Video"], horizontal=True)

# Create two columns for the main content
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    <div class="how-it-works-card">
        <h3 style="color: #0f172a; margin-top: 0;">How it works:</h3>
        <ol>
            <li><strong>📤 Upload</strong> an image or video containing a vehicle</li>
            <li><strong>🤖 Detect</strong> accidents using AI vision models</li>
            <li><strong>🔤 Extract</strong> license plate information via OCR</li>
            <li><strong>📱 Report</strong> incidents automatically via SMS</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="features-card">
        <h4 style="color: #0f172a; margin-top: 0;">Features:</h4>
        <ul style="margin-bottom: 0;">
            <li>🎯 Real-time accident detection</li>
            <li>🔤 License plate OCR</li>
            <li>📱 Emergency SMS alerts</li>
            <li>📊 Confidence scoring</li>
            <li>🎥 Video frame processing</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


def detect_license_plate_text(pil_image):
    """Run EasyOCR on the provided PIL image and return plausible plate candidates.

    Returns a list of tuples (text, confidence).
    """
    try:
        # Convert PIL image to numpy array (RGB)
        img = np.array(pil_image.convert("RGB"))
        print(f"OCR Input image shape: {img.shape}, dtype: {img.dtype}")

        # Preprocessing for better OCR
        # Convert to grayscale for OCR
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        print(f"Grayscale shape: {gray.shape}")

        # Apply some preprocessing to improve OCR
        # Increase contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)

        # Denoise
        gray = cv2.medianBlur(gray, 3)

        reader = easyocr.Reader(["en"], gpu=False)
        # Try OCR on both original RGB and preprocessed grayscale
        results_rgb = reader.readtext(img)
        results_gray = reader.readtext(gray)
        results = results_rgb + results_gray  # Combine results
        print(f"EasyOCR found {len(results_rgb)} RGB results and {len(results_gray)} gray results")

        candidates = []
        for bbox, text, conf in results:
            print(f"OCR result: '{text}' with confidence {conf}")
            # Clean the text - remove spaces and special chars, convert to uppercase
            cleaned = re.sub(r'[^A-Za-z0-9]', '', text).upper()
            print(f"Cleaned text: '{cleaned}'")

            # Very lenient license-plate-like heuristic: 1-15 alnum characters
            # Accept almost anything that looks like it could be a plate
            if re.match(r'^[A-Z0-9]{1,15}$', cleaned) and len(cleaned) >= 1:
                candidates.append((cleaned, float(conf)))
                print(f"Added candidate: {cleaned} (conf: {conf})")
            else:
                print(f"Rejected candidate: {cleaned} (doesn't match pattern)")

        # If no candidates found with strict filtering, try a more lenient approach
        if not candidates:
            print("No candidates found with strict filtering, trying lenient approach...")
            for bbox, text, conf in results:
                cleaned = re.sub(r'[^A-Za-z0-9]', '', text).upper()
                # Accept any alphanumeric string with at least 1 character
                if len(cleaned) >= 1 and any(c.isalnum() for c in cleaned):
                    candidates.append((cleaned, float(conf)))
                    print(f"Added lenient candidate: {cleaned} (conf: {conf})")

        # Sort by confidence desc
        candidates.sort(key=lambda x: x[1], reverse=True)

        # Return top candidates (limit to 5)
        print(f"Returning {len(candidates)} candidates")
        return candidates[:5]
    except Exception as e:
        print(f"OCR error: {e}")
        return []


def prepare_report_payload(plate_text, confidence, image_path=None, extra=None):
    payload = {
        "plate": plate_text,
        "confidence": confidence,
        "image_path": image_path,
        "extra": extra or {}
    }
    return payload


def send_report(payload):
    """Send the payload to an emergency endpoint if configured via env var.

    If no endpoint provided, the payload will be printed to the app for copy/paste.
    """
    endpoint = os.environ.get("EMERGENCY_ENDPOINT")
    if endpoint:
        try:
            resp = requests.post(endpoint, json=payload, timeout=10)
            return {"status": resp.status_code, "response": resp.text}
        except Exception as e:
            return {"error": str(e)}

    # If no HTTP endpoint, try Twilio if credentials provided via env or UI
    tw_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    tw_token = os.environ.get("TWILIO_AUTH_TOKEN")
    tw_from = os.environ.get("TWILIO_FROM_NUMBER")
    tw_to = os.environ.get("TWILIO_TO_NUMBER")

    # UI-driven credentials may be supplied via st.session_state (set in UI)
    ui_sid = st.session_state.get("tw_sid") if "tw_sid" in st.session_state else None
    ui_token = st.session_state.get("tw_token") if "tw_token" in st.session_state else None
    ui_from = st.session_state.get("tw_from") if "tw_from" in st.session_state else None
    ui_to = st.session_state.get("tw_to") if "tw_to" in st.session_state else None

    sid = ui_sid or tw_sid
    token = ui_token or tw_token
    frm = ui_from or tw_from
    to = ui_to or tw_to

    if sid and token and frm and to:
        try:
            from twilio.rest import Client
            client = Client(sid, token)
            
            # Format as alert message
            plate = payload.get("plate", "Unknown")
            confidence = payload.get("confidence", 0)
            location = (payload.get("extra") or {}).get("location", "Unknown")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            alert_body = f"""🚨 ACCIDENT ALERT 🚨
            
License Plate: {plate}
Confidence: {confidence:.2%}
Location: {location}
Time: {timestamp}

Emergency services have been notified."""
            
            # Send SMS
            sms_result = client.messages.create(body=alert_body, from_=frm, to=to)
            sms_status = "sent"
            sms_sid = sms_result.sid
            
            # Send voice call alert
            call_result = None
            call_sid = None
            call_status = "not_sent"
            try:
                call_text = f"Alert: Accident detected. License plate {plate} at {location}. Confidence {confidence:.0%}. Emergency services notified."
                call_result = client.calls.create(
                    to=to,
                    from_=frm,
                    twiml=f'<Response><Say>{call_text}</Say></Response>'
                )
                call_sid = call_result.sid
                call_status = "sent"
            except Exception as call_error:
                call_status = f"failed: {str(call_error)}"
            
            return {
                "status": "sent",
                "sms_sid": sms_sid,
                "sms_status": sms_status,
                "call_sid": call_sid,
                "call_status": call_status
            }
        except Exception as e:
            return {"error": f"Twilio send failed: {e}"}

    # No endpoint or Twilio credentials found: return payload for manual reporting
    return {"payload": payload}


# Conditional uploader based on input type
if input_type == "Image":
    st.markdown("""
    <div class="card detection-section">
        <h3 style="color: #0f172a; margin-top: 0;">Upload Image for Analysis</h3>
        <p style="color: #1f2937;">Supported formats: JPG, JPEG, PNG, AVIF</p>
    </div>
    """, unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png", "avif"], 
                                   help="Choose an image file to analyze for accidents and license plates 🚗")
else:
    st.markdown("""
    <div class="card detection-section">
        <h3 style="color: #0f172a; margin-top: 0;">Upload Video for Analysis</h3>
        <p style="color: #1f2937;">Supported formats: MP4, AVI, MOV, MKV</p>
    </div>
    """, unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=["mp4", "avi", "mov", "mkv"],
                                   help="Choose a video file (CCTV or camera feed) to analyze for accidents 🎥")

if uploaded_file is not None and input_type == "Image":
    # Display the uploaded image in a styled container
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h4 style="color: #0f172a; margin-top: 0;">Uploaded Image Preview</h4>', unsafe_allow_html=True)
    
    image = Image.open(uploaded_file)
    st.image(image, caption='', use_column_width=True, 
             output_format="JPEG", 
             channels="RGB")
    st.markdown('</div>', unsafe_allow_html=True)

    # Detection button with custom styling
    st.markdown("""
    <div style="text-align: center; margin: 20px 0;">
        <h4 style="color: #0f172a;">Ready to Analyze</h4>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button('🚨 Detect Accident', key='detect_btn', help='Run AI accident detection on the uploaded image 🤖'):
        with st.spinner('🤖 Loading AI model and analyzing image...'):
            try:
                MODEL_PATH = "runs/accident_detector2/weights/best.pt"
                model = YOLO(MODEL_PATH)

                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    image.save(tmp_file.name)
                    tmp_path = tmp_file.name

                results = model(tmp_path, save=False, conf=0.5)
                result_image = results[0].plot()

                # Display results in styled container
                st.markdown('<div class="detection-result">', unsafe_allow_html=True)
                st.markdown('<h4 style="color: #0f172a; margin-top: 0;">Detection Results</h4>', unsafe_allow_html=True)
                
                st.image(result_image, caption='', use_column_width=True)

                boxes = results[0].boxes
                if len(boxes) > 0:
                    st.markdown('<h5 style="color: #0f172a;">Accidents Detected:</h5>', unsafe_allow_html=True)
                    for i, box in enumerate(boxes):
                        cls = int(box.cls.item())
                        conf = box.conf.item()
                        class_name = model.names[cls]
                        st.markdown(f"""
                        <div style="background: #f8fafc; border-left: 4px solid #e5e7eb; padding: 10px; margin: 5px 0; border-radius: 5px;">
                            <strong>{class_name}</strong> - Confidence: <span style="color: #0f172a; font-weight: bold;">{conf:.2f}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="success-msg">
                        <h5 style="margin-top: 0;">✅ No Accidents Detected</h5>
                        <p>The image appears to be safe with no accident indicators found. 👍</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)
                os.unlink(tmp_path)
            except Exception as e:
                st.markdown(f"""
                <div class="error-msg">
                    <h5 style="margin-top: 0;">❌ Detection Error</h5>
                    <p>{str(e)}</p>
                </div>
                """, unsafe_allow_html=True)

elif uploaded_file is not None and input_type == "Video":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h4 style="color: #0f172a; margin-top: 0;">Video Frame Analysis</h4>', unsafe_allow_html=True)
    
    # Video settings
    col1, col2 = st.columns(2)
    with col1:
        frame_interval = st.slider("Extract every N frames", 1, 30, 5, help="Higher value = fewer frames processed")
    with col2:
        max_frames = st.slider("Maximum frames to process", 10, 500, 100, help="Limit processing for performance")
    
    if st.button("Process Video Frames", key="process_video_btn"):
        with st.spinner("Extracting and analyzing video frames..."):
            try:
                # Save video temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
                    tmp_video.write(uploaded_file.read())
                    video_path = tmp_video.name
                
                # Open video
                cap = cv2.VideoCapture(video_path)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                duration = total_frames / fps if fps > 0 else 0
                
                st.info(f"Video: {total_frames} frames @ {fps:.1f} FPS (~{duration:.1f}s)")
                
                # Load model once
                MODEL_PATH = "runs/accident_detector2/weights/best.pt"
                model = YOLO(MODEL_PATH)
                
                frame_count = 0
                detection_results = []
                progress_bar = st.progress(0)
                
                # Process frames
                processed_frames = 0
                while cap.isOpened() and frame_count < max_frames:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                    
                    # Process every Nth frame
                    if current_frame % frame_interval == 0:
                        processed_frames += 1
                        # Run detection
                        results = model(frame, save=False, conf=0.5)
                        boxes = results[0].boxes
                        
                        if len(boxes) > 0:
                            # Found accidents
                            result_frame = results[0].plot()
                            # Convert BGR to RGB for Streamlit and make a copy
                            result_frame_rgb = cv2.cvtColor(result_frame.copy(), cv2.COLOR_BGR2RGB)
                            timestamp = current_frame / fps if fps > 0 else 0
                            
                            detection_results.append({
                                "frame_id": current_frame,
                                "timestamp": timestamp,
                                "frame": result_frame_rgb,
                                "detections": []
                            })
                            
                            for box in boxes:
                                cls = int(box.cls.item())
                                conf = box.conf.item()
                                class_name = model.names[cls]
                                detection_results[-1]["detections"].append({
                                    "class": class_name,
                                    "confidence": conf
                                })
                        
                        frame_count += 1
                        progress = min(frame_count / max_frames, 1.0)
                        progress_bar.progress(progress)
                
                cap.release()
                os.unlink(video_path)
                
                # Show processing summary
                st.info(f"Processed {processed_frames} frames out of {total_frames} total frames")
                
                # Display results
                if detection_results:
                    st.success(f"Found {len(detection_results)} frames with accidents")
                    
                    # Show all detected frames
                    st.markdown("### 📸 Accident Frames")
                    
                    for i, result in enumerate(detection_results):
                        with st.expander(f"🚨 Accident Frame {i+1} - Frame {result['frame_id']} @ {result['timestamp']:.2f}s"):
                            col1, col2 = st.columns([1, 1])
                            
                            with col1:
                                st.image(result["frame"], caption=f"Frame {result['frame_id']}", use_column_width=True)
                            
                            with col2:
                                st.markdown("**Detection Details:**")
                                for det in result["detections"]:
                                    st.markdown(f"• **{det['class']}** - Confidence: {det['confidence']:.2f}")
                                
                                st.markdown(f"**Frame Info:**")
                                st.markdown(f"• Frame ID: {result['frame_id']}")
                                st.markdown(f"• Timestamp: {result['timestamp']:.2f}s")
                                st.markdown(f"• Image shape: {result['frame'].shape}")
                    
                    # OCR and SMS section for video frames
                    st.markdown("---")
                    st.markdown("### 🔤 License Plate Recognition & Emergency Alerts")
                    
                    # Initialize video OCR state
                    if 'video_ocr_results' not in st.session_state:
                        st.session_state.video_ocr_results = []
                    
                    if st.button('🔍 Scan License Plates in Detected Frames', key='video_ocr_btn'):
                        # First, test OCR with a simple test
                        st.write("🧪 Testing OCR with a simple test image...")
                        test_img = np.ones((100, 200, 3), dtype=np.uint8) * 255  # White image
                        test_pil = Image.fromarray(test_img)
                        test_candidates = detect_license_plate_text(test_pil)
                        st.write(f"Test OCR result: {len(test_candidates)} candidates found")
                        
                        with st.spinner('🔍 Scanning license plates in accident frames...'):
                            st.session_state.video_ocr_results = []
                            
                            progress_ocr = st.progress(0)
                            total_frames = len(detection_results)
                            
                            for i, result in enumerate(detection_results):
                                # Convert numpy array back to PIL Image for OCR
                                frame_rgb = result["frame"]
                                pil_image = Image.fromarray(frame_rgb)
                                
                                # Debug: show we're processing this frame
                                st.write(f"Processing frame {result['frame_id']}...")
                                st.write(f"Frame shape: {frame_rgb.shape}, dtype: {frame_rgb.dtype}")
                                
                                # Run OCR on this frame
                                candidates = detect_license_plate_text(pil_image)
                                
                                st.write(f"Frame {result['frame_id']}: Found {len(candidates)} OCR candidates")
                                if candidates:
                                    st.write(f"Candidates: {candidates}")
                                else:
                                    st.write("No candidates found - OCR returned empty list")
                                
                                if candidates:
                                    top_text, top_conf = candidates[0]
                                    st.session_state.video_ocr_results.append({
                                        "frame_id": result["frame_id"],
                                        "timestamp": result["timestamp"],
                                        "plate": top_text,
                                        "confidence": top_conf,
                                        "all_candidates": candidates
                                    })
                                    st.write(f"✓ Added plate: {top_text} (conf: {top_conf:.2f})")
                                else:
                                    st.write(f"✗ No license plates found in frame {result['frame_id']}")
                                
                                progress_ocr.progress((i + 1) / total_frames)
                            
                            st.success(f"OCR scan complete! Found license plates in {len(st.session_state.video_ocr_results)} out of {total_frames} frames.")
                    
                    # Display OCR results and SMS options
                    if st.session_state.video_ocr_results:
                        st.markdown("#### 📋 Detected License Plates")
                        
                        for result in st.session_state.video_ocr_results:
                            with st.expander(f"Frame {result['frame_id']} - Plate: {result['plate']}"):
                                st.markdown(f"**License Plate:** {result['plate']}")
                                st.markdown(f"**Confidence:** {result['confidence']:.2f}")
                                st.markdown(f"**Timestamp:** {result['timestamp']:.2f}s")
                                
                                # Show all candidates
                                if len(result['all_candidates']) > 1:
                                    st.markdown("**Other candidates:**")
                                    for text, conf in result['all_candidates'][1:]:
                                        st.markdown(f"- {text} ({conf:.2f})")
                        
                        # SMS notification section
                        st.markdown("---")
                        st.markdown("#### 📱 Emergency SMS Notifications")
                        
                        # Check for Twilio credentials
                        tw_sid_env = os.environ.get("TWILIO_ACCOUNT_SID")
                        tw_token_env = os.environ.get("TWILIO_AUTH_TOKEN")
                        tw_from_env = os.environ.get("TWILIO_FROM_NUMBER")
                        tw_to_env = os.environ.get("TWILIO_TO_NUMBER")
                        
                        sid = tw_sid_env
                        token = tw_token_env
                        frm = tw_from_env
                        to = tw_to_env
                        
                        if sid and token and frm and to:
                            st.markdown("✅ **Twilio credentials found** - Ready to send emergency alerts!")
                            
                            # Location input
                            location = st.text_input('📍 Accident Location (optional)', 
                                                   placeholder='Enter location for emergency report',
                                                   key='video_location')
                            
                            if st.button('🚨 Send Emergency Alerts for All Detections', key='video_sms_btn'):
                                with st.spinner('📤 Sending emergency alerts...'):
                                    sent_count = 0
                                    failed_count = 0
                                    
                                    st.write(f"Attempting to send {len(st.session_state.video_ocr_results)} SMS alerts...")
                                    
                                    for result in st.session_state.video_ocr_results:
                                        st.write(f"Sending alert for plate: {result['plate']}")
                                        
                                        payload = prepare_report_payload(
                                            result['plate'], 
                                            result['confidence'], 
                                            extra={"location": location, "video_frame": True, "timestamp": result['timestamp']}
                                        )
                                        
                                        st.write(f"Payload: {payload}")
                                        
                                        try:
                                            sms_result = send_report(payload)
                                            st.write(f"SMS result: {sms_result}")
                                            
                                            if 'status' in sms_result and sms_result['status'] == 'sent':
                                                sent_count += 1
                                                st.success(f"✅ SMS sent for plate {result['plate']}")
                                            else:
                                                failed_count += 1
                                                st.error(f"❌ SMS failed for plate {result['plate']}: {sms_result}")
                                        except Exception as e:
                                            st.error(f"Exception sending alert for plate {result['plate']}: {e}")
                                            failed_count += 1
                                    
                                    st.markdown("---")
                                    if sent_count > 0:
                                        st.success(f"✅ Successfully sent {sent_count} emergency alerts!")
                                    if failed_count > 0:
                                        st.error(f"❌ Failed to send {failed_count} alerts")
                        else:
                            st.warning("⚠️ Twilio credentials not configured. Emergency SMS alerts are not available.")
                            st.info("Configure TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, and TWILIO_TO_NUMBER environment variables.")
                    
                else:
                    st.info("No accidents detected in the video frames processed.")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            except Exception as e:
                st.error(f"Video processing error: {str(e)}")
                st.markdown('</div>', unsafe_allow_html=True)

    # OCR / Reporting UI - Use session state to persist form visibility
    # (show_ocr_form is now initialized at the top of the app)

if input_type == "Image":
    st.markdown("""
    <div style="text-align: center; margin: 30px 0 20px 0;" class="ocr-section">
        <h4 style="color: #0f172a;">License Plate Recognition</h4>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button('📝 Read License Plate & Prepare Report', key='ocr_btn', 
                help='Extract license plate text and prepare emergency report 📋'):
        st.session_state['show_ocr_form'] = True

    if st.session_state.get('show_ocr_form', False):
        with st.spinner('🔍 Scanning for license plates...'):
            candidates = detect_license_plate_text(image)
            if candidates:
                st.markdown('<div class="ocr-result">', unsafe_allow_html=True)
                st.markdown('<h4 style="color: #0f172a; margin-top: 0;">License Plate Candidates</h4>', unsafe_allow_html=True)
                
                st.write("Found potential license plates:")
                for i, (text, conf) in enumerate(candidates):
                    if i == 0:
                        st.markdown(f"""
                        <div style="background: #ffffff; border: 1px solid #d1d5db; border-radius: 8px; padding: 15px; margin: 10px 0;">
                            <h5 style="color: #0f172a; margin-top: 0;">Top Match: {text}</h5>
                            <p style="margin-bottom: 0;">Confidence: <strong>{conf:.2f}</strong></p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 10px; margin: 5px 0;">
                            <strong>{text}</strong> (confidence: {conf:.2f})
                        </div>
                        """, unsafe_allow_html=True)

                # Default choose top candidate
                top_text, top_conf = candidates[0]
                st.markdown('<h5 style="color: #0f172a;">Selected License Plate:</h5>', unsafe_allow_html=True)
                st.markdown(f"""
                <div style="background: #ffffff; border: 1px solid #d1d5db; border-radius: 8px; padding: 15px; font-size: 1.2em; font-weight: bold; text-align: center; color: #0f172a;">
                    {top_text}
                </div>
                """, unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

                extra_info = {}
                col1, col2 = st.columns(2)
                with col1:
                    location = st.text_input('📍 Location (optional)', 
                                           placeholder='Enter accident location',
                                           help='Optional location information for the report')
                    extra_info['location'] = location
                
                with col2:
                    st.markdown('<br>', unsafe_allow_html=True)  # Spacing
                    location_display = location.strip() if isinstance(location, str) and location.strip() else 'Not specified'
                    st.markdown(f"""
                    <div style="background: #f8f9fa; border-radius: 8px; padding: 15px; margin-top: 10px;">
                        <h5 style="color: #6c757d; margin-top: 0;">📊 Report Summary</h5>
                        <p style="margin-bottom: 5px;"><strong>Plate:</strong> {top_text}</p>
                        <p style="margin-bottom: 5px;"><strong>Confidence:</strong> {top_conf:.2f}</p>
                        <p style="margin-bottom: 0;"><strong>Location:</strong> {location_display}</p>
                    </div>
                    """,
                    unsafe_allow_html=True)

                # Auto-send SMS if Twilio credentials are available either in env or session
                tw_sid_env = os.environ.get("TWILIO_ACCOUNT_SID")
                tw_token_env = os.environ.get("TWILIO_AUTH_TOKEN")
                tw_from_env = os.environ.get("TWILIO_FROM_NUMBER")
                tw_to_env = os.environ.get("TWILIO_TO_NUMBER")

                tw_sid_ui = st.session_state.get('tw_sid') if 'tw_sid' in st.session_state else None
                tw_token_ui = st.session_state.get('tw_token') if 'tw_token' in st.session_state else None
                tw_from_ui = st.session_state.get('tw_from') if 'tw_from' in st.session_state else None
                tw_to_ui = st.session_state.get('tw_to') if 'tw_to' in st.session_state else None

                sid = tw_sid_ui or tw_sid_env
                token = tw_token_ui or tw_token_env
                frm = tw_from_ui or tw_from_env
                to = tw_to_ui or tw_to_env

                payload = prepare_report_payload(top_text, top_conf, image_path=None, extra=extra_info)

                if sid and token and frm and to:
                    st.markdown("""
                    <div class="success-msg">
                        <h5 style="margin-top: 0;">📱 Twilio Credentials Found</h5>
                        <p>Emergency SMS will be sent automatically. 🚀</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.spinner('📤 Sending emergency alert...'):
                        result = send_report(payload)
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown('<h4 style="color: #28a745; margin-top: 0;">✅ Auto-Send Result</h4>', unsafe_allow_html=True)
                        st.json(result)
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="warning-msg">
                        <h5 style="margin-top: 0;">⚠️ Twilio Setup Required</h5>
                        <p>No Twilio credentials detected. Configure below to enable automatic SMS alerts. 📱</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Use text inputs and a button (more reliable than forms)
                    st.markdown("""
                    <div class="card card-danger sms-section">
                        <h4 style="color: #dc3545; margin-top: 0;">🚨 Configure Emergency SMS</h4>
                        <p style="margin-bottom: 15px;">Set up Twilio credentials to send automatic emergency alerts.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        tw_sid = st.text_input('🔐 Twilio Account SID', type='password', 
                                             value=tw_sid_env or '', 
                                             placeholder='Enter your Twilio SID',
                                             help='Your Twilio Account SID')
                        tw_from = st.text_input('📞 Twilio From Number', 
                                              value=tw_from_env or '', 
                                              placeholder='+15551234567',
                                              help='Your Twilio phone number')
                    with col2:
                        tw_token = st.text_input('🔑 Twilio Auth Token', type='password', 
                                               value=tw_token_env or '', 
                                               placeholder='Enter your Twilio token',
                                               help='Your Twilio Auth Token')
                        tw_to = st.text_input('📱 Emergency Number', 
                                            value=tw_to_env or '', 
                                            placeholder='+15559876543',
                                            help='Emergency contact number')

                    # Button to save and send
                    if st.button('🚀 Save & Send Emergency Alert', key='send_sms_btn',
                               help='Save credentials and send SMS alert'):
                        st.info('[DEBUG] Send SMS button clicked.')
                        # Persist entered credentials to session_state
                        st.session_state['tw_sid'] = tw_sid
                        st.session_state['tw_token'] = tw_token
                        st.session_state['tw_from'] = tw_from
                        st.session_state['tw_to'] = tw_to
                        st.info('[DEBUG] Credentials saved to session_state.')

                        # Prepare and send report
                        payload = prepare_report_payload(top_text, top_conf, image_path=None, extra=extra_info)
                        st.info(f'[DEBUG] Prepared payload: {payload}')
                        with st.spinner('📤 Sending emergency alert...'):
                            try:
                                st.info('[DEBUG] Calling send_report...')
                                result = send_report(payload)
                                st.info(f'[DEBUG] send_report result: {result}')
                            except Exception as e:
                                st.error(f"Exception during send_report: {e}")
                                st.info(f'[DEBUG] Exception during send_report: {e}')
                                result = {'error': str(e)}
                        try:
                            log_report(payload, result)
                            st.info('[DEBUG] log_report called.')
                        except Exception as e:
                            st.info(f'[DEBUG] Exception in log_report: {e}')
                        
                        # Display results in styled container
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown('<h4 style="color: #28a745; margin-top: 0;">📤 Report Status</h4>', unsafe_allow_html=True)
                        st.json(result)
                        
                        # Show detailed error if present
                        if 'error' in result:
                            st.markdown(f"""
                            <div class="error-msg">
                                <p><strong>❌ SMS Error:</strong> {result['error']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        elif 'status' in result and result['status'] != 'sent':
                            st.markdown(f"""
                            <div class="warning-msg">
                                <p><strong>⚠️ SMS Status:</strong> {result['status']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        elif not result:
                            st.markdown("""
                            <div class="warning-msg">
                                <p><strong>⚠️ No Response:</strong> Check logs and credentials.</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div class="success-msg">
                                <p><strong>✅ Emergency Alert Sent Successfully!</strong></p>
                            </div>
                            """, unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Add a close button to dismiss the form
                    st.markdown('<br>', unsafe_allow_html=True)
                    if st.button('❌ Close Report Form', key='close_ocr_form',
                               help='Close the license plate and reporting section 🔒'):
                        st.session_state['show_ocr_form'] = False
                        st.rerun()
            else:
                st.markdown("""
                <div class="warning-msg">
                    <h5 style="margin-top: 0;">🔍 No License Plates Found</h5>
                    <p>The OCR analysis didn't detect any license-plate-like text in the image. 🤔</p>
                </div>
                """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
    <h4 style="color: #495057; margin-bottom: 10px;">🚨 Accident Detection System</h4>
    <p style="margin-bottom: 5px;">Powered by AI Vision Models & OCR Technology</p>
    <p style="margin-bottom: 0; font-size: 0.9em; color: #6c757d;">
        Built with ❤️ using Streamlit, Ultralytics YOLO, and EasyOCR
    </p>
</div>
""", unsafe_allow_html=True)