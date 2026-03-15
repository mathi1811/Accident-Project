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



st.title("Accident Detection & License Plate OCR UI")
st.write("Upload an image to detect accidents and read license plates (if present).")


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


uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png", "avif"])

if uploaded_file is not None:
    # Display the uploaded image
    image = Image.open(uploaded_file)
    st.image(image, caption='Uploaded Image.', use_column_width=True)

    # Detection button
    if st.button('Detect Accident'):
        with st.spinner('Loading model and running detection...'):
            try:
                MODEL_PATH = "runs/accident_detector2/weights/best.pt"
                model = YOLO(MODEL_PATH)

                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    image.save(tmp_file.name)
                    tmp_path = tmp_file.name

                results = model(tmp_path, save=False, conf=0.5)
                result_image = results[0].plot()

                st.image(result_image, caption='Detection Result.', use_column_width=True)

                boxes = results[0].boxes
                if len(boxes) > 0:
                    st.write("Detections:")
                    for box in boxes:
                        cls = int(box.cls.item())
                        conf = box.conf.item()
                        class_name = model.names[cls]
                        st.write(f"- {class_name} (confidence: {conf:.2f})")
                else:
                    st.write("No accidents detected.")

                os.unlink(tmp_path)
            except Exception as e:
                st.error(f"An error occurred during detection: {str(e)}")

    # OCR / Reporting UI - Use session state to persist form visibility
    if 'show_ocr_form' not in st.session_state:
        st.session_state.show_ocr_form = False

    if st.button('Read Plate & Prepare Report'):
        st.session_state.show_ocr_form = True

    if st.session_state.show_ocr_form:
        with st.spinner('Running OCR to find license plates...'):
            candidates = detect_license_plate_text(image)
            if candidates:
                st.write("Plate candidates (text, confidence):")
                for text, conf in candidates:
                    st.write(f"- {text}  (conf: {conf:.2f})")

                # Default choose top candidate
                top_text, top_conf = candidates[0]
                st.markdown("**Selected plate:**")
                st.write(top_text)

                extra_info = {}
                location = st.text_input('Location (optional)')
                extra_info['location'] = location

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
                    with st.spinner('Twilio credentials found — sending SMS automatically...'):
                        result = send_report(payload)
                        st.write("Auto-send result:")
                        st.json(result)
                else:
                    st.markdown("---")
                    st.subheader("Optional: SMS (Twilio) settings")
                    st.write("No Twilio credentials detected in environment or session. Provide them below or set env vars to enable auto-send.")

                    # Use text inputs and a button (more reliable than forms)
                    col1, col2 = st.columns(2)
                    with col1:
                        tw_sid = st.text_input('Twilio Account SID', type='password', value=tw_sid_env or '', key='tw_sid_input')
                        tw_from = st.text_input('Twilio From Number (e.g. +15551234567)', value=tw_from_env or '', key='tw_from_input')
                    with col2:
                        tw_token = st.text_input('Twilio Auth Token', type='password', value=tw_token_env or '', key='tw_token_input')
                        tw_to = st.text_input('Destination Phone Number (e.g. +15557654321)', value=tw_to_env or '', key='tw_to_input')

                    # Button to save and send
                    if st.button('Save credentials & Send SMS', key='send_sms_btn'):
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
                        with st.spinner('Sending report via Twilio...'):
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
                        st.write("Report result:")
                        st.json(result)
                        # Show detailed error if present
                        if 'error' in result:
                            st.error(f"Twilio error: {result['error']}")
                        elif 'status' in result and result['status'] != 'sent':
                            st.warning(f"Twilio status: {result['status']}")
                        elif not result:
                            st.warning("No response from send_report. Check logs and credentials.")
                        st.success('[DEBUG] SMS send process completed!')
                    
                    # Add a close button to dismiss the form
                    if st.button('Close Report Form', key='close_ocr_form'):
                        st.session_state.show_ocr_form = False
                        st.rerun()
            else:
                st.write("No license-plate-like text found by OCR.")