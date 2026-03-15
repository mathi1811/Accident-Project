from ultralytics import YOLO
import os

MODEL = "../runs/accident_detector/weights/best.pt"
IMAGE = "../inference/input/test1.jpg"
OUTPUT = "../inference/output"

model = YOLO(MODEL)

model.predict(
    source=IMAGE,
    save=True,
    project=OUTPUT,
    name="results"
)

print("✔ Detection complete!")
