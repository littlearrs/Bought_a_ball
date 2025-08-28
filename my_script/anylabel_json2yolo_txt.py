import os
import json
from glob import glob
from PIL import Image
import shutil

def build_label_map(json_files):
    """扫描所有 JSON，建立 label -> id 的映射"""
    labels = set()
    for jf in json_files:
        with open(jf, "r", encoding="utf-8") as f:
            data = json.load(f)
            for shape in data.get("shapes", []):
                labels.add(shape["label"])
    label2id = {label: idx for idx, label in enumerate(sorted(labels))}
    return label2id

def convert_json_to_yolo(json_path, label2id, images_dir, labels_dir):
    """将单个 JSON 转换为 YOLO txt 并保存到 labels 文件夹，同时拷贝图片到 images 文件夹"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 图片原路径
    img_dir = os.path.dirname(json_path)
    image_path = os.path.join(img_dir, data["imagePath"])
    if not os.path.exists(image_path):
        print(f"⚠️ 图片不存在: {image_path}")
        return

    # 读取图片尺寸
    with Image.open(image_path) as img:
        img_w, img_h = img.size

    yolo_lines = []
    for shape in data.get("shapes", []):
        label = shape["label"]
        points = shape["points"]

        # 自动识别标注点类型
        if len(points) == 2:  # 左上 + 右下
            (x1, y1), (x2, y2) = points
        elif len(points) == 4:  # 四个顶点
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
        else:
            print(f"⚠️ 不支持的 points 格式: {points} in {json_path}")
            continue

        # 转换为 YOLO 格式
        cx = (x1 + x2) / 2.0 / img_w
        cy = (y1 + y2) / 2.0 / img_h
        w = abs(x2 - x1) / img_w
        h = abs(y2 - y1) / img_h

        class_id = label2id[label]
        yolo_lines.append(f"{class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")

    # 保存 txt 到 labels 文件夹
    os.makedirs(labels_dir, exist_ok=True)
    txt_name = os.path.splitext(os.path.basename(json_path))[0] + ".txt"
    txt_path = os.path.join(labels_dir, txt_name)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(yolo_lines))

    # 拷贝图片到 images 文件夹
    os.makedirs(images_dir, exist_ok=True)
    img_name = os.path.basename(image_path)
    shutil.copy(image_path, os.path.join(images_dir, img_name))

    print(f"✅ 转换完成: {txt_name}")

def save_classes_txt(label2id, output_dir):
    """生成 classes.txt 文件"""
    classes_txt = os.path.join(output_dir, "classes.txt")
    with open(classes_txt, "w", encoding="utf-8") as f:
        for label, idx in sorted(label2id.items(), key=lambda x: x[1]):
            f.write(label + "\n")
    print(f"✅ classes.txt 已生成: {classes_txt}")

if __name__ == "__main__":
    folder = r"E:\object_detection_dataset\well_data\well_data_2\set_2_labels"  # 修改为你的数据集路径

    # 递归扫描所有 JSON 文件
    json_files = glob(os.path.join(folder, "**", "*.json"), recursive=True)
    if not json_files:
        print("⚠️ 未找到 JSON 文件，请检查路径")
        exit(0)

    # 自动生成类别映射
    label2id = build_label_map(json_files)
    print("类别映射表:", label2id)

    # labels 和 images 文件夹
    labels_dir = os.path.join(folder, "labels")
    images_dir = os.path.join(folder, "images")

    # 批量转换
    for jf in json_files:
        convert_json_to_yolo(jf, label2id, images_dir, labels_dir)

    # 生成 classes.txt
    save_classes_txt(label2id, folder)
    print("\n🎉 全部转换完成！")

