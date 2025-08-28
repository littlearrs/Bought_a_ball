import os
import cv2
import json

def parse_labelme_json(json_path):
    """解析 LabelMe JSON 标注为 (label, x1, y1, x2, y2)"""
    boxes = []
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for shape in data.get("shapes", []):
        label = shape["label"]
        points = shape["points"]

        # 转换为整数
        xs = [int(p[0]) for p in points]
        ys = [int(p[1]) for p in points]

        x1, y1 = min(xs), min(ys)
        x2, y2 = max(xs), max(ys)

        boxes.append((label, x1, y1, x2, y2))
    return boxes

def visualize(img_path, boxes, save_dir=None):
    img = cv2.imread(img_path)
    for label, x1, y1, x2, y2 in boxes:
        color = (0, 255, 0)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(img, label, (x1, max(y1 - 5, 0)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, os.path.basename(img_path))
        cv2.imwrite(save_path, img)
    else:
        cv2.imshow("result", img)
        cv2.waitKey(0)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, required=True, help="存放图片和json的文件夹")
    parser.add_argument("--save_dir", type=str, default=None, help="保存结果的文件夹（不指定则窗口显示）")
    args = parser.parse_args()

    for file in os.listdir(args.data_dir):
        if file.lower().endswith((".jpg", ".png", ".jpeg")):
            img_path = os.path.join(args.data_dir, file)
            json_path = os.path.splitext(img_path)[0] + ".json"
            if os.path.exists(json_path):
                boxes = parse_labelme_json(json_path)
                visualize(img_path, boxes, args.save_dir)


# # 仅显示（窗口中查看）
# python view_labels.py --data_dir ./dataset

# # 保存到 output 文件夹
# python view_labels.py --data_dir ./dataset --save_dir ./output


