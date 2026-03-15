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
    /* Main background and text colors */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Title styling */
    .title {
        color: #dc3545;
        font-size: 2.5em;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Subtitle styling */
    .subtitle {
        color: #495057;
        font-size: 1.2em;
        text-align: center;
        margin-bottom: 30px;
        font-style: italic;
    }
    
    /* Card styling */
    .card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #007bff;
    }
    
    .card-danger {
        border-left-color: #dc3545;
    }
    
    .card-success {
        border-left-color: #28a745;
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(45deg, #007bff, #0056b3);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* File uploader styling */
    .uploadedFile {
        border: 2px dashed #007bff;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        background: #f8f9ff;
    }
    
    /* Success messages */
    .success-msg {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    
    /* Warning messages */
    .warning-msg {
        background: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    
    /* Error messages */
    .error-msg {
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    
    /* Detection results styling */
    .detection-result {
        background: #e7f3ff;
        border: 1px solid #b3d9ff;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* OCR results styling */
    .ocr-result {
        background: #f0f9ff;
        border: 1px solid #b3e5fc;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #6c757d;
        margin-top: 50px;
        padding: 20px;
        border-top: 1px solid #dee2e6;
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
st.markdown('<p class="subtitle">Advanced AI-powered accident detection with automatic license plate recognition and emergency reporting</p>', unsafe_allow_html=True)

# Create two columns for the main content
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    <div class="card">
        <h3 style="color: #007bff; margin-top: 0;">📋 How it works:</h3>
        <ol>
            <li><strong>Upload</strong> an image containing a vehicle</li>
            <li><strong>Detect</strong> accidents using AI vision models</li>
            <li><strong>Extract</strong> license plate information via OCR</li>
            <li><strong>Report</strong> incidents automatically via SMS</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card card-success">
        <h4 style="color: #28a745; margin-top: 0;">✅ Features:</h4>
        <ul style="margin-bottom: 0;">
            <li>Real-time accident detection</li>
            <li>License plate OCR</li>
            <li>Emergency SMS alerts</li>
            <li>Confidence scoring</li>
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
    <p style="color: #6c757d;">Supported formats: JPG, JPEG, PNG, AVIF</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png", "avif"], 
                               help="Choose an image file to analyze for accidents and license plates")

if uploaded_file is not None:
    # Display the uploaded image in a styled container
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h4 style="color: #28a745; margin-top: 0;">📸 Uploaded Image</h4>', unsafe_allow_html=True)
    
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
    
    if st.button('🚨 Detect Accident', key='detect_btn', help='Run AI accident detection on the uploaded image'):
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
                            <strong>{class_name}</strong> - Confidence: <span style="color: #dc3545; font-weight: bold;">{conf:.2f}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="success-msg">
                        <h5 style="margin-top: 0;">✅ No Accidents Detected</h5>
                        <p>The image appears to be safe with no accident indicators found.</p>
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
                help='Extract license plate text and prepare emergency report'):
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
                st.markdown('<h5 style="color: #17a2b8;">📍 Selected License Plate:</h5>', unsafe_allow_html=True)
                st.markdown(f"""
                <div style="background: #fff3cd; border: 2px solid #ffc107; border-radius: 8px; padding: 15px; font-size: 1.2em; font-weight: bold; text-align: center; color: #856404;">
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
                        <p>Emergency SMS will be sent automatically.</p>
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
                        <p>No Twilio credentials detected. Configure below to enable automatic SMS alerts.</p>
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
                               help='Close the license plate and reporting section'):
                        st.session_state.show_ocr_form = False
                        st.rerun()
            else:
                st.markdown("""
                <div class="warning-msg">
                    <h5 style="margin-top: 0;">🔍 No License Plates Found</h5>
                    <p>The OCR analysis didn't detect any license-plate-like text in the image.</p>
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