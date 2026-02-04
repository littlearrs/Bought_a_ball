import os
import shutil

def filter_labels_with_class2(root_dir):
    labels_dir = os.path.join(root_dir, "labels")
    images_dir = os.path.join(root_dir, "images")

    # 目标输出目录
    labels2_dir = os.path.join(root_dir, "labels2")
    images2_dir = os.path.join(root_dir, "images2")
    os.makedirs(labels2_dir, exist_ok=True)
    os.makedirs(images2_dir, exist_ok=True)

    # 遍历 labels 文件夹
    for label_file in os.listdir(labels_dir):
        if not label_file.endswith(".txt"):
            continue

        label_path = os.path.join(labels_dir, label_file)

        # 检查 txt 文件里是否有类别号 2
        with open(label_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        has_class2 = any(line.strip().startswith("2 ") or line.strip() == "2" for line in lines)

        if has_class2:
            # 复制 label 文件
            shutil.copy(label_path, os.path.join(labels2_dir, label_file))

            # 对应的图片名（去掉后缀换成图片后缀）
            img_name = os.path.splitext(label_file)[0]

            # 找可能的图片格式
            for ext in [".jpg", ".jpeg", ".png", ".bmp"]:
                img_path = os.path.join(images_dir, img_name + ext)
                if os.path.exists(img_path):
                    shutil.copy(img_path, os.path.join(images2_dir, img_name + ext))
                    print(f"复制: {label_file} 和 {img_name+ext}")
                    break

if __name__ == "__main__":
    # 修改为你的数据集根目录路径
    dataset_root = r"E:\object_detection_dataset\well_data\well_data4_yolo\set_10_labels_yolo"
    filter_labels_with_class2(dataset_root)
