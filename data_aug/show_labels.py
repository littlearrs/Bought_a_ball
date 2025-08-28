import os
import cv2
import json
import xml.etree.ElementTree as ET

def load_classes(class_file=None):
    """加载类别名字"""
    if class_file and os.path.exists(class_file):
        with open(class_file, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines()]
    return None

def parse_txt(label_path, img_shape):
    """解析YOLO txt标注"""
    h, w = img_shape[:2]
    boxes = []
    with open(label_path, 'r') as f:
        for line in f.readlines():
            cls, x, y, bw, bh = map(float, line.strip().split())
            x1 = int((x - bw / 2) * w)
            y1 = int((y - bh / 2) * h)
            x2 = int((x + bw / 2) * w)
            y2 = int((y + bh / 2) * h)
            boxes.append((int(cls), x1, y1, x2, y2))
    return boxes

def parse_xml(label_path):
    """解析Pascal VOC xml标注"""
    boxes = []
    tree = ET.parse(label_path)
    root = tree.getroot()
    for obj in root.findall("object"):
        cls_name = obj.find("name").text
        bbox = obj.find("bndbox")
        x1 = int(bbox.find("xmin").text)
        y1 = int(bbox.find("ymin").text)
        x2 = int(bbox.find("xmax").text)
        y2 = int(bbox.find("ymax").text)
        boxes.append((cls_name, x1, y1, x2, y2))
    return boxes

def parse_json(label_path):
    """解析COCO json标注（只适合单文件json，非每图单json）"""
    with open(label_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # 建立 image_id -> file_name 映射
    images = {img['id']: img['file_name'] for img in data['images']}
    anns = {}
    for ann in data['annotations']:
        img_id = ann['image_id']
        cls_id = ann['category_id']
        x, y, w, h = ann['bbox']
        x1, y1, x2, y2 = int(x), int(y), int(x+w), int(y+h)
        anns.setdefault(images[img_id], []).append((cls_id, x1, y1, x2, y2))
    return anns, {c['id']: c['name'] for c in data['categories']}

def visualize(img_path, boxes, classes=None, is_coco=False):
    img = cv2.imread(img_path)
    for box in boxes:
        cls, x1, y1, x2, y2 = box
        color = (0, 255, 0)
        cls_name = str(cls)
        if classes:
            if is_coco:
                cls_name = classes.get(cls, str(cls))
            elif isinstance(cls, int) and cls < len(classes):
                cls_name = classes[cls]
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(img, cls_name, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.imshow("result", img)
    cv2.waitKey(0)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--img_dir", type=str, required=True, help="图片目录")
    parser.add_argument("--label_dir", type=str, required=True, help="标签目录/json文件路径")
    parser.add_argument("--format", type=str, choices=["txt", "xml", "json"], required=True, help="标注格式")
    parser.add_argument("--classes", type=str, default=None, help="类别文件(txt，每行一个类别)")
    args = parser.parse_args()

    classes = load_classes(args.classes)

    if args.format == "json":
        anns, coco_classes = parse_json(args.label_dir)
        for img_name, boxes in anns.items():
            img_path = os.path.join(args.img_dir, img_name)
            if os.path.exists(img_path):
                visualize(img_path, boxes, coco_classes, is_coco=True)
    else:
        for img_name in os.listdir(args.img_dir):
            img_path = os.path.join(args.img_dir, img_name)
            label_name = os.path.splitext(img_name)[0] + "." + args.format
            label_path = os.path.join(args.label_dir, label_name)
            if not os.path.exists(label_path):
                continue
            if args.format == "txt":
                boxes = parse_txt(label_path, cv2.imread(img_path).shape)
            elif args.format == "xml":
                boxes = parse_xml(label_path)
            visualize(img_path, boxes, classes)


# # 1. 查看YOLO txt标签
# python show_labels.py --img_dir ./images --label_dir ./labels --format txt --classes classes.txt

# # 2. 查看VOC xml标签
# python show_labels.py --img_dir ./images --label_dir ./Annotations --format xml

# # 3. 查看COCO json标签
# python show.py --img_dir ./images --label_dir ./annotations/instances_train.json --format json
