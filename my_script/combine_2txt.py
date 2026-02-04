import os

def merge_txt_files(folder1, folder2):
    """
    将 folder2 中的同名 txt 文件内容追加写入 folder1 中对应的 txt 文件，
    并且严格去除所有多余空行。
    """
    if not os.path.isdir(folder1) or not os.path.isdir(folder2):
        print("❌ 输入路径无效")
        return

    for file in os.listdir(folder2):
        if file.lower().endswith(".txt"):
            file1_path = os.path.join(folder1, file)
            file2_path = os.path.join(folder2, file)

            if os.path.exists(file1_path):
                # 读取 file2 内容并清除空行
                with open(file2_path, "r", encoding="utf-8") as f2:
                    lines = [line.strip() for line in f2.readlines() if line.strip()]

                if not lines:
                    continue  # file2 可能全是空行

                with open(file1_path, "a", encoding="utf-8") as f1:
                    for line in lines:
                        f1.write(f"\n{line}")

                print(f"✅ 已合并: {file2_path} ➜ {file1_path}")
            else:
                print(f"⚠️ {file} 在 folder1 中不存在，跳过")

if __name__ == "__main__":
    folder1 = r"E:\object_detection_dataset\excavator_data\excavator1\labels\val"
    folder2 = r"E:\object_detection_dataset\excavator_data\output\gen_photos\labels"
    merge_txt_files(folder1, folder2)
