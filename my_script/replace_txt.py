import os
import shutil

def replace_files(folder1, folder2):
    """
    遍历文件夹2，若文件夹1中存在同名文件，则用文件夹2的文件替换文件夹1里的。
    """
    for file_name in os.listdir(folder2):
        file2_path = os.path.join(folder2, file_name)
        file1_path = os.path.join(folder1, file_name)

        # 只处理txt文件
        if file_name.endswith(".txt") and os.path.isfile(file2_path):
            if os.path.exists(file1_path):
                shutil.copy2(file2_path, file1_path)  # copy2 保留时间戳等信息
                print(f"已替换: {file1_path} <- {file2_path}")

if __name__ == "__main__":
    # 修改为你的文件夹路径
    folder1 = r"E:\object_detection_dataset\well_data\well_data4_yolo\well_4_2\labels\val"   # 目标目录（被替换）
    folder2 = r"E:\object_detection_dataset\well_data\well_data4_yolo\labels2"   # 来源目录（替换来源）
    replace_files(folder1, folder2)
