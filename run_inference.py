from ultralytics import YOLO

model = YOLO("/Users/mathiyazhagi/Documents/accident_project/runs/accident_detector2/weights/best.pt")

results = model(
    "/Users/mathiyazhagi/Documents/accident_project/test_images/sample1.jpeg",
    save=True
)

print("Inference Done!")
print("Output saved to: runs/detect/predict")
