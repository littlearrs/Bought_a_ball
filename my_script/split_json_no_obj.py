import os
import json
import shutil
import argparse

def move_unlabeled_images(base_dir, output_subdir="no_label"):
    """
    遍历 base_dir 下的图片与 json 标注文件，如果 json 文件没有目标标签，
    则将该 json 与对应的图片一起剪切到 base_dir/no_label 文件夹下
    """
    # 创建目标子文件夹
    output_dir = os.path.join(base_dir, output_subdir)
    os.makedirs(output_dir, exist_ok=True)

    # 支持的图片后缀
    img_exts = {".jpg", ".jpeg", ".png", ".bmp"}

    count_labeled = 0
    count_unlabeled = 0

    # 遍历文件夹
    for file in os.listdir(base_dir):
        file_path = os.path.join(base_dir, file)
        name, ext = os.path.splitext(file)

        # 只处理图片
        if ext.lower() in img_exts:
            json_path = os.path.join(base_dir, name + ".json")
            if not os.path.exists(json_path):
                print(f"⚠️ 没找到 JSON: {json_path}")
                continue

            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 判断是否有标注
                has_labels = len(data.get("shapes", [])) > 0

                if has_labels:
                    count_labeled += 1
                else:
                    count_unlabeled += 1
                    # 剪切文件
                    shutil.move(file_path, os.path.join(output_dir, file))
                    shutil.move(json_path, os.path.join(output_dir, os.path.basename(json_path)))
                    print(f"➡️ 已移动无标签文件: {file}, {os.path.basename(json_path)}")

            except Exception as e:
                print(f"❌ 解析 {json_path} 失败: {e}")

    print("\n📊 统计结果：")
    print(f"   有标注图片数: {count_labeled}")
    print(f"   无标注图片数: {count_unlabeled}")
    print(f"   已移动到: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="移动没有标签的图片和对应 JSON 文件")
    parser.add_argument("folder", type=str, help="要处理的文件夹路径")
    parser.add_argument("--out", type=str, default="no_label", help="存放无标签文件的子文件夹名称")
    args = parser.parse_args()

    move_unlabeled_images(args.folder, args.out)
