import os

def validate_pairs(img_dir, label_dir):
    # 获取所有 jpg 图片基名
    img_files = [os.path.splitext(f)[0] for f in os.listdir(img_dir) if f.endswith(".jpg")]
    # 获取所有 txt 标签基名
    label_files = [os.path.splitext(f)[0] for f in os.listdir(label_dir) if f.endswith(".txt")]

    img_set = set(img_files)
    label_set = set(label_files)

    print("=== 检查图片与标签的一一匹配情况 ===")

    # 图片没有对应的标签
    no_label = img_set - label_set
    # 标签没有对应的图片
    no_image = label_set - img_set

    if not no_label and not no_image:
        print("✔ 所有图片和标签完全匹配！")
    else:
        if no_label:
            print("❌ 以下图片没有对应的标签：")
            for name in sorted(no_label):
                print("   ", name + ".jpg")

        if no_image:
            print("❌ 以下标签没有对应的图片：")
            for name in sorted(no_image):
                print("   ", name + ".txt")


if __name__ == "__main__":
    # 你可以在这里改成自己的路径
    img_dir = r"E:\object_detection_dataset\vehicle_data\my_vehicle\images\train"
    label_dir = r"E:\object_detection_dataset\vehicle_data\my_vehicle\labels\train"

    validate_pairs(img_dir, label_dir)
