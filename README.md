# Accident Detection UI

This project provides a simple web UI for detecting accidents in images using a trained YOLOv8 model.

## Setup

1. Activate your virtual environment (if using one):
   ```
   source project_env/bin/activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the UI

Run the Streamlit app:
```
streamlit run app.py
```

Or if using system Python:
```
/usr/bin/python3 -m streamlit run app.py
```

The app will be available at `http://localhost:8501`

Automation
----------

For convenience there's a script to install dependencies and start the app (and ngrok if you provide a token):

1. Copy `.env.example` to `.env` and fill in values you want to export automatically, or set env vars in your shell.

2. Run the automation script (makes the project env optional):

```bash
cd /Users/mathiyazhagi/Documents/accident_project
chmod +x run_ui.sh
./run_ui.sh
```

Logs are written to `runs/logs/streamlit.log` and `runs/logs/ngrok.log` (if ngrok was started).

To stop the background processes:

```bash
kill $(cat runs/streamlit.pid)
if [ -f runs/ngrok.pid ]; then kill $(cat runs/ngrok.pid); fi
```


## Features

- Upload an image (JPG, JPEG, PNG, AVIF)
- Run accident detection using the trained YOLOv8 model
- View the detection results with bounding boxes
- See confidence scores for detected classes (accident/no_accident)

## Model

The UI uses the best weights from `runs/accident_detector2/weights/best.pt`

## Requirements

- Python 3.9+
- ultralytics
- streamlit
- pillow