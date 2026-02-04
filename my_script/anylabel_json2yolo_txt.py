import os
import json
from glob import glob
from PIL import Image
import shutil

def build_label_map(json_files, custom_map=None):
    """
    构建 label -> id 映射
    custom_map: dict, 可选，格式 {"label1":0, "label2":1}，优先使用自定义映射
    """
    if custom_map:
        # 验证 custom_map 是否覆盖所有标签
        all_labels = set()
        for jf in json_files:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
                for shape in data.get("shapes", []):
                    all_labels.add(shape["label"])
        missing = all_labels - set(custom_map.keys())
        if missing:
            raise ValueError(f"⚠️ 自定义映射缺少以下 label: {missing}")
        return custom_map

    # 自动生成
    labels = set()
    for jf in json_files:
        with open(jf, "r", encoding="utf-8") as f:
            data = json.load(f)
            for shape in data.get("shapes", []):
                labels.add(shape["label"])
    label2id = {label: idx for idx, label in enumerate(sorted(labels))}
    return label2id

def convert_json_to_yolo(json_path, label2id, images_dir, labels_dir):
    """将单个 JSON 转换为 YOLO txt 并保存"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    image_path = os.path.join(os.path.dirname(json_path), data["imagePath"])
    if not os.path.exists(image_path):
        print(f"⚠️ 图片不存在: {image_path}")
        return

    with Image.open(image_path) as img:
        img_w, img_h = img.size

    yolo_lines = []
    for shape in data.get("shapes", []):
        label = shape["label"]
        points = shape["points"]

        if len(points) == 2:
            (x1, y1), (x2, y2) = points
        elif len(points) == 4:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
        else:
            print(f"⚠️ 不支持的 points 格式: {points} in {json_path}")
            continue

        cx = (x1 + x2) / 2.0 / img_w
        cy = (y1 + y2) / 2.0 / img_h
        w = abs(x2 - x1) / img_w
        h = abs(y2 - y1) / img_h

        class_id = label2id[label]
        yolo_lines.append(f"{class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

    os.makedirs(labels_dir, exist_ok=True)
    txt_name = os.path.splitext(os.path.basename(json_path))[0] + ".txt"
    txt_path = os.path.join(labels_dir, txt_name)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(yolo_lines))

    os.makedirs(images_dir, exist_ok=True)
    shutil.copy(image_path, os.path.join(images_dir, os.path.basename(image_path)))

    print(f"✅ 转换完成: {txt_name}")

def save_classes_txt(label2id, output_dir):
    classes_txt = os.path.join(output_dir, "classes.txt")
    with open(classes_txt, "w", encoding="utf-8") as f:
        for label, idx in sorted(label2id.items(), key=lambda x: x[1]):
            f.write(label + "\n")
    print(f"✅ classes.txt 已生成: {classes_txt}")

if __name__ == "__main__":
    folder = r"E:\object_detection_dataset\well_data\well_data4_yolo\set_negative"

    json_files = glob(os.path.join(folder, "**", "*.json"), recursive=True)
    if not json_files:
        print("⚠️ 未找到 JSON 文件，请检查路径")
        exit(0)

    # ---- 这里可以自定义 class_id ----
    custom_map = {"well": 0, "s_well": 2}  # 自定义映射
    # custom_map = None  # 不使用自定义，则自动生成


    label2id = build_label_map(json_files, custom_map)
    print("类别映射表:", label2id)

    labels_dir = os.path.join(folder, "labels")
    images_dir = os.path.join(folder, "images")

    for jf in json_files:
        convert_json_to_yolo(jf, label2id, images_dir, labels_dir)

    save_classes_txt(label2id, folder)
    print("\n🎉 全部转换完成！")


