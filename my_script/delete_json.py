import os
import argparse

def remove_images_without_json(folder):
    removed_count = 0

    # 遍历文件夹里的所有文件
    for fname in os.listdir(folder):
        fpath = os.path.join(folder, fname)

        # 只处理图片
        if fname.lower().endswith((".jpg", ".jpeg", ".png")):
            # 构造对应 JSON 文件名
            json_name = os.path.splitext(fname)[0] + ".json"
            json_path = os.path.join(folder, json_name)

            # 如果没有对应 JSON，就删除图片
            if not os.path.exists(json_path):
                os.remove(fpath)
                removed_count += 1
                print(f"Removed: {fname}")

    print(f"\n✅ Done. Removed {removed_count} images without JSON files.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove images without corresponding JSON files in the same folder.")
    parser.add_argument("--folder", required=True, help="Path to folder containing images and JSON files")
    args = parser.parse_args()

    remove_images_without_json(args.folder)
