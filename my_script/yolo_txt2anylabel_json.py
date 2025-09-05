import os
import json
from glob import glob
from PIL import Image

def load_classes(classes_path):
    """加载 classes.txt"""
    with open(classes_path, "r", encoding="utf-8") as f:
        classes = [line.strip() for line in f.readlines()]
    return classes

def yolo_to_json(txt_path, classes, images_dir, output_dir):
    """将单个 YOLO txt 文件转换为 JSON"""
    txt_name = os.path.basename(txt_path)
    base_name = os.path.splitext(txt_name)[0]
    image_path = os.path.join(images_dir, base_name + ".jpg")
    if not os.path.exists(image_path):
        image_path = os.path.join(images_dir, base_name + ".png")
        if not os.path.exists(image_path):
            print(f"⚠️ 图片不存在: {base_name}")
            return

    with Image.open(image_path) as img:
        img_w, img_h = img.size

    shapes = []
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 5:
                print(f"⚠️ 格式错误: {line}")
                continue
            class_id, cx, cy, w, h = map(float, parts)
            class_id = int(class_id)
            label = classes[class_id]

            # YOLO → 左上右下
            x1 = (cx - w / 2) * img_w
            y1 = (cy - h / 2) * img_h
            x2 = (cx + w / 2) * img_w
            y2 = (cy + h / 2) * img_h

            shape = {
                "label": label,
                "points": [[x1, y1], [x2, y2]],
                "group_id": None,
                "shape_type": "rectangle",
                "flags": {}
            }
            shapes.append(shape)

    data = {
        "imagePath": os.path.basename(image_path),
        "imageWidth": img_w,
        "imageHeight": img_h,
        "shapes": shapes,
        "flags": {},
        "version": "1.0"
    }

    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, base_name + ".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 转换完成: {json_path}")

if __name__ == "__main__":
    folder = r"E:\object_detection_dataset\well_data\set_5_labels_yolo"  # YOLO txt 和 images 根目录
    txt_files = glob(os.path.join(folder, "labels", "*.txt"))
    images_dir = os.path.join(folder, "images")
    classes_path = os.path.join(folder, "classes.txt")
    output_dir = os.path.join(folder, "json_labels")

    classes = load_classes(classes_path)

    for txt_file in txt_files:
        yolo_to_json(txt_file, classes, images_dir, output_dir)

    print("\n🎉 全部 YOLO txt 已转换为 JSON！")
