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

# Custom CSS for attractive styling
st.markdown("""
<style>
    /* Main background with gradient */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    /* App container background */
    .block-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        margin: 20px;
        padding: 30px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
    }
    
    /* Title styling with glow effect */
    .title {
        color: #dc3545;
        font-size: 3em;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
        text-shadow: 3px 3px 6px rgba(220, 53, 69, 0.3);
        background: linear-gradient(45deg, #dc3545, #ff6b6b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { text-shadow: 3px 3px 6px rgba(220, 53, 69, 0.3); }
        to { text-shadow: 3px 3px 12px rgba(220, 53, 69, 0.6); }
    }
    
    /* Subtitle styling */
    .subtitle {
        color: #495057;
        font-size: 1.3em;
        text-align: center;
        margin-bottom: 40px;
        font-style: italic;
        background: rgba(255, 255, 255, 0.8);
        padding: 15px;
        border-radius: 10px;
        border: 2px solid #e9ecef;
    }
    
    /* Enhanced card styling with gradients */
    .card {
        background: linear-gradient(145deg, #ffffff, #f8f9fa);
        border-radius: 15px;
        padding: 25px;
        margin: 15px 0;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        border-left: 6px solid #007bff;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.2);
    }
    
    .card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #007bff, #6610f2, #e83e8c);
    }
    
    .card-danger {
        border-left-color: #dc3545;
    }
    
    .card-danger::before {
        background: linear-gradient(90deg, #dc3545, #fd7e14, #ffc107);
    }
    
    .card-success {
        border-left-color: #28a745;
    }
    
    .card-success::before {
        background: linear-gradient(90deg, #28a745, #20c997, #17a2b8);
    }
    
    .card-warning {
        border-left-color: #ffc107;
    }
    
    .card-warning::before {
        background: linear-gradient(90deg, #ffc107, #fd7e14, #dc3545);
    }
    
    /* Enhanced button styling with multiple variants */
    .stButton>button {
        background: linear-gradient(45deg, #007bff, #0056b3);
        color: white;
        border: none;
        border-radius: 30px;
        padding: 12px 25px;
        font-weight: bold;
        font-size: 16px;
        transition: all 0.4s ease;
        box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .stButton>button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .stButton>button:hover::before {
        left: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 8px 25px rgba(0, 123, 255, 0.4);
    }
    
    /* Danger button variant */
    .stButton>button[data-testid*="detect"] {
        background: linear-gradient(45deg, #dc3545, #c82333);
        box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);
    }
    
    .stButton>button[data-testid*="detect"]:hover {
        box-shadow: 0 8px 25px rgba(220, 53, 69, 0.4);
    }
    
    /* Success button variant */
    .stButton>button[data-testid*="ocr"] {
        background: linear-gradient(45deg, #28a745, #218838);
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
    }
    
    .stButton>button[data-testid*="ocr"]:hover {
        box-shadow: 0 8px 25px rgba(40, 167, 69, 0.4);
    }
    
    /* File uploader styling with animation */
    .uploadedFile {
        border: 3px dashed #007bff;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        background: linear-gradient(135deg, #f8f9ff 0%, #e8f2ff 100%);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .uploadedFile:hover {
        border-color: #0056b3;
        background: linear-gradient(135deg, #e8f2ff 0%, #d4e8ff 100%);
        transform: scale(1.02);
    }
    
    .uploadedFile::before {
        content: '📤';
        font-size: 3em;
        display: block;
        margin-bottom: 10px;
        animation: bounce 2s infinite;
    }
    
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-10px); }
        60% { transform: translateY(-5px); }
    }
    
    /* Enhanced message styling with icons */
    .success-msg {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        color: #155724;
        border: 2px solid #28a745;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        position: relative;
        box-shadow: 0 4px 12px rgba(40, 167, 69, 0.2);
    }
    
    .success-msg::before {
        content: '✅';
        font-size: 1.5em;
        margin-right: 10px;
    }
    
    .warning-msg {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        color: #856404;
        border: 2px solid #ffc107;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        position: relative;
        box-shadow: 0 4px 12px rgba(255, 193, 7, 0.2);
    }
    
    .warning-msg::before {
        content: '⚠️';
        font-size: 1.5em;
        margin-right: 10px;
    }
    
    .error-msg {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        color: #721c24;
        border: 2px solid #dc3545;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        position: relative;
        box-shadow: 0 4px 12px rgba(220, 53, 69, 0.2);
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
    
    /* Footer with enhanced styling */
    .footer {
        text-align: center;
        background: linear-gradient(135deg, #495057 0%, #343a40 100%);
        color: white;
        margin-top: 50px;
        padding: 30px;
        border-radius: 15px 15px 0 0;
        box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.2);
        position: relative;
    }
    
    .footer::before {
        content: '🚨';
        font-size: 2em;
        display: block;
        margin-bottom: 10px;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #28a745, #20c997, #17a2b8);
    }
    
    /* Sidebar styling if used */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Text input styling */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #ced4da;
        padding: 10px 15px;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #007bff;
        box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
    }
    
    /* Select box styling */
    .stSelectbox > div > div {
        border-radius: 10px;
        border: 2px solid #ced4da;
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #007bff;
    }
    
    /* Image styling */
    .stImage {
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transition: transform 0.3s ease;
    }
    
    .stImage:hover {
        transform: scale(1.02);
    }
    
    /* JSON display styling */
    .stJson {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #dee2e6;
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



st.markdown('<h1 class="title">🚨 Accident Detection & License Plate OCR</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">🔍 Advanced AI-powered accident detection with automatic license plate recognition and 🚀 emergency reporting</p>', unsafe_allow_html=True)

# Create two columns for the main content
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    <div class="card">
        <h3 style="color: #007bff; margin-top: 0;">📋 How it works:</h3>
        <ol>
            <li><strong>📤 Upload</strong> an image containing a vehicle</li>
            <li><strong>🤖 Detect</strong> accidents using AI vision models</li>
            <li><strong>🔤 Extract</strong> license plate information via OCR</li>
            <li><strong>📱 Report</strong> incidents automatically via SMS</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card card-success">
        <h4 style="color: #28a745; margin-top: 0;">✅ Features:</h4>
        <ul style="margin-bottom: 0;">
            <li>🎯 Real-time accident detection</li>
            <li>🔤 License plate OCR</li>
            <li>📱 Emergency SMS alerts</li>
            <li>📊 Confidence scoring</li>
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
        reader = easyocr.Reader(["en"], gpu=False)
        results = reader.readtext(img)

        candidates = []
        for bbox, text, conf in results:
            cleaned = re.sub(r'[^A-Za-z0-9]', '', text).upper()
            # License-plate-like heuristic: 4-10 alnum characters
            if re.match(r'^[A-Z0-9]{4,10}$', cleaned):
                candidates.append((cleaned, float(conf)))

        # Sort by confidence desc
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates
    except Exception as e:
        st.error(f"OCR error: {e}")
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


st.markdown("""
<div class="card">
    <h3 style="color: #007bff; margin-top: 0;">📤 Upload Image for Analysis</h3>
    <p style="color: #6c757d;">Supported formats: JPG, JPEG, PNG, AVIF 📸</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png", "avif"], 
                               help="Choose an image file to analyze for accidents and license plates 🚗")

if uploaded_file is not None:
    # Display the uploaded image in a styled container
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h4 style="color: #28a745; margin-top: 0;">📸 Uploaded Image Preview</h4>', unsafe_allow_html=True)
    
    image = Image.open(uploaded_file)
    st.image(image, caption='', use_column_width=True, 
             output_format="JPEG", 
             channels="RGB")
    st.markdown('</div>', unsafe_allow_html=True)

    # Detection button with custom styling
    st.markdown("""
    <div style="text-align: center; margin: 20px 0;">
        <h4 style="color: #dc3545;">🔍 Ready to Analyze</h4>
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
                st.markdown('<h4 style="color: #007bff; margin-top: 0;">🎯 Detection Results</h4>', unsafe_allow_html=True)
                
                st.image(result_image, caption='', use_column_width=True)

                boxes = results[0].boxes
                if len(boxes) > 0:
                    st.markdown('<h5 style="color: #dc3545;">⚠️ Accidents Detected:</h5>', unsafe_allow_html=True)
                    for i, box in enumerate(boxes):
                        cls = int(box.cls.item())
                        conf = box.conf.item()
                        class_name = model.names[cls]
                        st.markdown(f"""
                        <div style="background: #ffe6e6; border-left: 4px solid #dc3545; padding: 10px; margin: 5px 0; border-radius: 5px;">
                            <strong>🚨 {class_name}</strong> - Confidence: <span style="color: #dc3545; font-weight: bold;">{conf:.2f}</span>
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

    # OCR / Reporting UI - Use session state to persist form visibility
    if 'show_ocr_form' not in st.session_state:
        st.session_state.show_ocr_form = False

    st.markdown("""
    <div style="text-align: center; margin: 30px 0 20px 0;">
        <h4 style="color: #17a2b8;">🔤 License Plate Recognition</h4>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button('📝 Read License Plate & Prepare Report', key='ocr_btn', 
                help='Extract license plate text and prepare emergency report 📋'):
        st.session_state.show_ocr_form = True

    if st.session_state.show_ocr_form:
        with st.spinner('🔍 Scanning for license plates...'):
            candidates = detect_license_plate_text(image)
            if candidates:
                st.markdown('<div class="ocr-result">', unsafe_allow_html=True)
                st.markdown('<h4 style="color: #17a2b8; margin-top: 0;">📋 License Plate Candidates</h4>', unsafe_allow_html=True)
                
                st.write("Found potential license plates:")
                for i, (text, conf) in enumerate(candidates):
                    if i == 0:
                        st.markdown(f"""
                        <div style="background: #e8f5e8; border: 2px solid #28a745; border-radius: 8px; padding: 15px; margin: 10px 0;">
                            <h5 style="color: #28a745; margin-top: 0;">🎯 Top Match: {text}</h5>
                            <p style="margin-bottom: 0;">Confidence: <strong>{conf:.2f}</strong> 🎯</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 10px; margin: 5px 0;">
                            <strong>🔤 {text}</strong> (confidence: {conf:.2f})
                        </div>
                        """, unsafe_allow_html=True)

                # Default choose top candidate
                top_text, top_conf = candidates[0]
                st.markdown('<h5 style="color: #17a2b8;">📍 Selected License Plate:</h5>', unsafe_allow_html=True)
                st.markdown(f"""
                <div style="background: #fff3cd; border: 2px solid #ffc107; border-radius: 8px; padding: 15px; font-size: 1.2em; font-weight: bold; text-align: center; color: #856404;">
                    🚗 {top_text} 🚗
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
                    st.markdown("""
                    <div style="background: #f8f9fa; border-radius: 8px; padding: 15px; margin-top: 10px;">
                        <h5 style="color: #6c757d; margin-top: 0;">📊 Report Summary</h5>
                        <p style="margin-bottom: 5px;"><strong>Plate:</strong> {top_text}</p>
                        <p style="margin-bottom: 5px;"><strong>Confidence:</strong> {top_conf:.2f}</p>
                        <p style="margin-bottom: 0;"><strong>Location:</strong> {location or 'Not specified'}</p>
                    </div>
                    """.format(top_text=top_text, top_conf=top_conf, location=location or 'Not specified'), 
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
                    <div class="card card-danger">
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
                        st.session_state.show_ocr_form = False
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