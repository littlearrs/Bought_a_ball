
import os
import json

# JSON 文件夹路径
json_dir = r"E:\object_detection_dataset\well_data\set_6_labels"

# 遍历文件夹下所有 JSON 文件
for fname in os.listdir(json_dir):
    if fname.endswith(".json"):
        json_path = os.path.join(json_dir, fname)
        base_name = os.path.splitext(fname)[0]
        img_file = base_name + ".jpg"  # 对应图片名

        # 打开 JSON 文件
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 修改 imagePath
        data["imagePath"] = img_file

        # 保存修改后的 JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ Updated {json_path} -> {img_file}")
