import os
import shutil

def move_json_files(source_folder, target_folder):
    # 创建目标文件夹（如果不存在）
    os.makedirs(target_folder, exist_ok=True)

    # 遍历源文件夹所有文件
    for filename in os.listdir(source_folder):
        if filename.lower().endswith(".json"):
            src_path = os.path.join(source_folder, filename)
            dst_path = os.path.join(target_folder, filename)

            # 剪切文件
            shutil.move(src_path, dst_path)
            print(f"Moved: {filename}")

    print("Done! All json files have been moved.")

if __name__ == "__main__":
    source = r"E:\object_detection_dataset\vehicle_data\excavator2\images"   # 修改为你的json源文件夹
    target = r"E:\object_detection_dataset\vehicle_data\excavator2\jsons"   # 修改为你要剪切到的目标文件夹
    move_json_files(source, target)
