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
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #3a7bd5 100%);
        background-attachment: fixed;
        min-height: 100vh;
        width: 100vw;
        margin: 0;
        padding: 0;
    }

    /* App container with subtle colored background */
    .block-container {
        background: linear-gradient(135deg,
            rgba(240, 248, 255, 0.95) 0%,
            rgba(248, 250, 252, 0.95) 25%,
            rgba(255, 250, 240, 0.95) 50%,
            rgba(248, 252, 248, 0.95) 75%,
            rgba(252, 248, 255, 0.95) 100%);
        border-radius: 0;
        margin: 0;
        padding: 20px;
        min-height: 100vh;
        box-shadow: none;
        backdrop-filter: blur(10px);
        width: 100%;
        max-width: none;
        position: relative;
    }

    .block-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="subtle-pattern" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="10" cy="10" r="1" fill="rgba(0,123,255,0.05)"/><circle cx="10" cy="10" r="0.3" fill="rgba(40,167,69,0.03)"/></pattern></defs><rect width="100" height="100" fill="url(%23subtle-pattern)"/></svg>');
        opacity: 0.3;
        pointer-events: none;
    }

    /* Title with vibrant, attractive styling */
    .title {
        font-size: 3.5em;
        font-weight: 900;
        text-align: center;
        margin-bottom: 25px;
        background: linear-gradient(45deg, #ff6b6b, #ffd93d, #6bcf7f, #4d96ff, #9b59b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow:
            0 0 20px rgba(255, 107, 107, 0.5),
            0 0 40px rgba(255, 217, 61, 0.3),
            0 0 60px rgba(107, 207, 127, 0.3),
            0 0 80px rgba(77, 150, 255, 0.3);
        padding: 25px 30px;
        border-radius: 20px;
        background-color: rgba(0, 0, 0, 0.8);
        border: 3px solid;
        border-image: linear-gradient(45deg, #ff6b6b, #ffd93d, #6bcf7f, #4d96ff) 1;
        display: inline-block;
        width: 100%;
        box-sizing: border-box;
        font-family: 'Arial Black', 'Impact', 'Helvetica Bold', Arial, sans-serif;
        letter-spacing: 3px;
        line-height: 1.1;
        animation: rainbow-glow 3s ease-in-out infinite alternate;
        position: relative;
    }

    .title::before {
        content: '🚨';
        position: absolute;
        left: 20px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 0.8em;
        animation: bounce 1s infinite;
    }

    .title::after {
        content: '🚨';
        position: absolute;
        right: 20px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 0.8em;
        animation: bounce 1s infinite 0.5s;
    }

    @keyframes rainbow-glow {
        from {
            filter: brightness(1) contrast(1);
            text-shadow:
                0 0 20px rgba(255, 107, 107, 0.5),
                0 0 40px rgba(255, 217, 61, 0.3);
        }
        to {
            filter: brightness(1.2) contrast(1.1);
            text-shadow:
                0 0 30px rgba(255, 107, 107, 0.8),
                0 0 60px rgba(255, 217, 61, 0.5),
                0 0 90px rgba(107, 207, 127, 0.4);
        }
    }

    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(-50%) scale(1); }
        40% { transform: translateY(-50%) scale(1.2); }
        60% { transform: translateY(-50%) scale(0.9); }
    }

    /* Subtitle with vibrant styling */
    .subtitle {
        font-size: 1.6em;
        text-align: center;
        margin-bottom: 40px;
        font-weight: 700;
        color: #ffffff;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(248, 249, 250, 0.95));
        padding: 25px 30px;
        border-radius: 20px;
        border: 3px solid;
        border-image: linear-gradient(135deg, #4d96ff, #9b59b6, #ff6b6b) 1;
        backdrop-filter: blur(15px);
        box-shadow:
            0 10px 30px rgba(77, 150, 255, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, -apple-system, BlinkMacSystemFont, sans-serif;
        line-height: 1.4;
        letter-spacing: 0.5px;
        position: relative;
    }

    .subtitle::before {
        content: '🔍';
        position: absolute;
        left: 20px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 1.5em;
        opacity: 0.8;
    }
    
    /* Special styling for How it Works section */
    .how-it-works-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(240, 248, 255, 0.9));
        border-radius: 20px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 10px 30px rgba(0, 123, 255, 0.15);
        border: none;
        transition: transform 0.4s ease, box-shadow 0.4s ease;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
        border-left: 8px solid #007bff;
    }

    .how-it-works-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="workflow" width="25" height="25" patternUnits="userSpaceOnUse"><circle cx="12.5" cy="12.5" r="3" fill="none" stroke="rgba(0,123,255,0.1)" stroke-width="1"/><path d="M12.5 6.5 L12.5 18.5 M6.5 12.5 L18.5 12.5" stroke="rgba(0,123,255,0.1)" stroke-width="1"/><text x="12.5" y="16" text-anchor="middle" font-size="6" fill="rgba(0,123,255,0.2)">→</text></pattern></defs><rect width="100" height="100" fill="url(%23workflow)"/></svg>');
        opacity: 0.4;
        z-index: 1;
    }

    .how-it-works-card:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 15px 40px rgba(0, 123, 255, 0.25);
    }

    .how-it-works-card > * {
        position: relative;
        z-index: 2;
    }

    /* Special styling for Features section */
    .features-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(240, 255, 240, 0.9));
        border-radius: 20px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 10px 30px rgba(40, 167, 69, 0.15);
        border: none;
        transition: transform 0.4s ease, box-shadow 0.4s ease;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
        border-left: 8px solid #28a745;
    }

    .features-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="features" width="30" height="30" patternUnits="userSpaceOnUse"><circle cx="15" cy="15" r="4" fill="none" stroke="rgba(40,167,69,0.1)" stroke-width="2"/><path d="M10 15 L13 18 L20 11" stroke="rgba(40,167,69,0.2)" stroke-width="2" fill="none"/><circle cx="15" cy="15" r="1" fill="rgba(40,167,69,0.1)"/></pattern></defs><rect width="100" height="100" fill="url(%23features)"/></svg>');
        opacity: 0.4;
        z-index: 1;
    }

    .features-card:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 15px 40px rgba(40, 167, 69, 0.25);
    }

    .features-card > * {
        position: relative;
        z-index: 2;
    }

    /* Enhanced list styling with vibrant colors */
    .how-it-works-card h3 {
        color: #ffffff !important;
        background: linear-gradient(45deg, #4d96ff, #6bcf7f);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.8em;
        font-weight: 800;
        margin-bottom: 25px;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        border-bottom: 3px solid #4d96ff;
        padding-bottom: 10px;
    }

    .how-it-works-card ol {
        padding-left: 25px;
        counter-reset: step-counter;
    }

    .how-it-works-card li {
        margin-bottom: 18px;
        padding: 15px 20px;
        background: linear-gradient(135deg, rgba(77, 150, 255, 0.1), rgba(107, 207, 127, 0.1));
        border-radius: 12px;
        border-left: 5px solid #4d96ff;
        transition: all 0.4s ease;
        position: relative;
        counter-increment: step-counter;
        font-size: 1.1em;
        font-weight: 600;
        color: #2c3e50;
    }

    .how-it-works-card li::before {
        content: counter(step-counter);
        position: absolute;
        left: -15px;
        top: 50%;
        transform: translateY(-50%);
        background: linear-gradient(45deg, #4d96ff, #6bcf7f);
        color: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 0.9em;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }

    .how-it-works-card li:hover {
        background: linear-gradient(135deg, rgba(77, 150, 255, 0.2), rgba(107, 207, 127, 0.2));
        transform: translateX(8px) scale(1.02);
        box-shadow: 0 8px 20px rgba(77, 150, 255, 0.3);
        border-left-color: #6bcf7f;
    }

    .how-it-works-card strong {
        color: #4d96ff;
        font-weight: 800;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    }

    .features-card h4 {
        color: #ffffff !important;
        background: linear-gradient(45deg, #28a745, #ffc107, #fd7e14);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.6em;
        font-weight: 800;
        margin-bottom: 20px;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        border-bottom: 3px solid #28a745;
        padding-bottom: 8px;
    }

    .features-card ul {
        list-style: none;
        padding: 0;
    }

    .features-card li {
        margin-bottom: 15px;
        padding: 12px 18px;
        background: linear-gradient(135deg, rgba(40, 167, 69, 0.1), rgba(255, 193, 7, 0.1));
        border-radius: 10px;
        border-left: 5px solid #28a745;
        transition: all 0.4s ease;
        position: relative;
        font-size: 1.1em;
        font-weight: 600;
        color: #2c3e50;
    }

    .features-card li::before {
        content: '✓';
        position: absolute;
        left: -12px;
        top: 50%;
        transform: translateY(-50%);
        background: linear-gradient(45deg, #28a745, #ffc107);
        color: white;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 0.8em;
        box-shadow: 0 3px 6px rgba(0, 0, 0, 0.2);
    }

    .features-card li:hover {
        background: linear-gradient(135deg, rgba(40, 167, 69, 0.2), rgba(255, 193, 7, 0.2));
        transform: translateX(8px) scale(1.02);
        box-shadow: 0 8px 20px rgba(40, 167, 69, 0.3);
        border-left-color: #ffc107;
    }

    .card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(0,123,255,0.1)" stroke-width="1"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
        opacity: 0.1;
        z-index: 1;
    }

    .card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
    }

    .card > * {
        position: relative;
        z-index: 2;
    }

    /* Card variants with different background colors */
    .card-danger {
        background: linear-gradient(135deg, rgba(220, 53, 69, 0.1), rgba(255, 107, 107, 0.1));
        border-left: 8px solid #dc3545;
    }

    .card-danger::after {
        content: '🚨';
        position: absolute;
        top: 20px;
        right: 20px;
        font-size: 2em;
        opacity: 0.3;
    }

    .card-success {
        background: linear-gradient(135deg, rgba(40, 167, 69, 0.1), rgba(32, 201, 151, 0.1));
        border-left: 8px solid #28a745;
    }

    .card-success::after {
        content: '✅';
        position: absolute;
        top: 20px;
        right: 20px;
        font-size: 2em;
        opacity: 0.3;
    }

    .card-warning {
        background: linear-gradient(135deg, rgba(255, 193, 7, 0.1), rgba(253, 126, 20, 0.1));
        border-left: 8px solid #ffc107;
    }

    .card-warning::after {
        content: '⚠️';
        position: absolute;
        top: 20px;
        right: 20px;
        font-size: 2em;
        opacity: 0.3;
    }
    
    /* Enhanced button styling with vibrant gradients */
    .stButton>button {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 15px;
        padding: 18px 35px;
        font-weight: 800;
        font-size: 18px;
        transition: all 0.4s ease;
        box-shadow:
            0 8px 25px rgba(102, 126, 234, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
        position: relative;
        overflow: hidden;
        width: 100%;
        margin: 12px 0;
        text-transform: uppercase;
        letter-spacing: 1px;
        border: 2px solid transparent;
        background-clip: padding-box;
    }

    .stButton>button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        transition: left 0.6s;
        z-index: 1;
    }

    .stButton>button:hover::before {
        left: 100%;
    }

    .stButton>button:hover {
        background: linear-gradient(45deg, #764ba2 0%, #667eea 100%);
        transform: translateY(-4px) scale(1.03);
        box-shadow:
            0 12px 35px rgba(102, 126, 234, 0.6),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
        border-color: rgba(255, 255, 255, 0.3);
    }

    .stButton>button:active {
        transform: translateY(-2px) scale(1.01);
        box-shadow:
            0 6px 15px rgba(102, 126, 234, 0.4),
            inset 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    /* Danger button variant with vibrant red gradient */
    .stButton>button[data-testid*="detect"] {
        background: linear-gradient(45deg, #ff6b6b 0%, #ee5a24 100%);
        box-shadow:
            0 8px 25px rgba(255, 107, 107, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }

    .stButton>button[data-testid*="detect"]:hover {
        background: linear-gradient(45deg, #ee5a24 0%, #ff6b6b 100%);
        box-shadow:
            0 12px 35px rgba(255, 107, 107, 0.6),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
    }

    /* Success button variant with vibrant green gradient */
    .stButton>button[data-testid*="ocr"] {
        background: linear-gradient(45deg, #6bcf7f 0%, #28a745 100%);
        box-shadow:
            0 8px 25px rgba(107, 207, 127, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }

    .stButton>button[data-testid*="ocr"]:hover {
        background: linear-gradient(45deg, #28a745 0%, #6bcf7f 100%);
        box-shadow:
            0 12px 35px rgba(107, 207, 127, 0.6),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
    }
    
    /* File uploader styling with vibrant design */
    .uploadedFile {
        border: 4px dashed;
        border-image: linear-gradient(45deg, #667eea, #764ba2, #ff6b6b, #6bcf7f) 1;
        border-radius: 20px;
        padding: 50px 40px;
        text-align: center;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(248, 249, 255, 0.9));
        transition: all 0.5s ease;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(15px);
        width: 100%;
        margin: 25px 0;
        box-shadow:
            0 10px 30px rgba(102, 126, 234, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
    }

    .uploadedFile::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="upload-pattern" width="25" height="25" patternUnits="userSpaceOnUse"><circle cx="12.5" cy="12.5" r="2" fill="none" stroke="rgba(102,126,234,0.1)" stroke-width="1"/><path d="M8 12.5 L12.5 17.5 L17 12.5 M12.5 8 L12.5 17.5" stroke="rgba(102,126,234,0.15)" stroke-width="1.5" fill="none"/></pattern></defs><rect width="100" height="100" fill="url(%23upload-pattern)"/></svg>');
        opacity: 0.6;
        z-index: 1;
    }

    .uploadedFile:hover {
        border-color: transparent;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(248, 249, 255, 0.95));
        transform: translateY(-5px) scale(1.02);
        box-shadow:
            0 15px 40px rgba(102, 126, 234, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.4);
    }

    .uploadedFile::after {
        content: '📤 Drop your image here or click to browse 📸';
        position: absolute;
        bottom: 25px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 1.3em;
        color: #667eea;
        font-weight: 700;
        opacity: 0.9;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        z-index: 2;
        letter-spacing: 0.5px;
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



st.markdown('<h1 class="title">🚨 Accident Detection & License Plate OCR</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">🔍 Advanced AI-powered accident detection with automatic license plate recognition and 🚀 emergency reporting</p>', unsafe_allow_html=True)

# Create two columns for the main content
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    <div class="how-it-works-card">
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
    <div class="features-card">
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
<div class="card detection-section">
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
    <div style="text-align: center; margin: 30px 0 20px 0;" class="ocr-section">
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