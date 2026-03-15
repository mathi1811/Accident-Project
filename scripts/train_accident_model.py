from ultralytics import YOLO

model = YOLO("yolov8m.pt")

model.train(
    data="/Users/mathiyazhagi/Documents/accident_project/config/accident_dataset.yaml",
    epochs=60,
    imgsz=640,
    batch=8,
    project="../runs",
    name="accident_detector"
)

print("Training complete!")
