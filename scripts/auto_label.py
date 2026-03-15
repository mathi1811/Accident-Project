import os
import cv2
from ultralytics import YOLO

# Auto-label using pretrained YOLO model
model = YOLO("yolov8m.pt")  # medium model → better for accident detection

IMAGE_DIR = "/Users/mathiyazhagi/Documents/accident_project/dataset/images/train"
LABEL_DIR = "/Users/mathiyazhagi/Documents/accident_project/dataset/labels/train"

os.makedirs(LABEL_DIR, exist_ok=True)

def auto_label(image_path, label_path):
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Cannot read: {image_path}")
        return

    h, w = img.shape[:2]
    results = model(image_path)[0]

    with open(label_path, "w") as f:
        for box in results.boxes:
            cls = int(0)  # Force class "accident"
            x1, y1, x2, y2 = box.xyxy[0]

            xc = ((x1 + x2) / 2) / w
            yc = ((y1 + y2) / 2) / h
            bw = (x2 - x1) / w
            bh = (y2 - y1) / h

            f.write(f"{cls} {xc} {yc} {bw} {bh}\n")

    print(f"✔ Saved label: {label_path}")

for file in os.listdir(IMAGE_DIR):
    if file.lower().endswith((".jpg", ".png", ".jpeg")):
        img_path = os.path.join(IMAGE_DIR, file)
        label_path = os.path.join(
            LABEL_DIR, file.rsplit(".", 1)[0] + ".txt"
        )
        auto_label(img_path, label_path)

print("\n🎉 Auto-labeling complete!")
