import os

def remove_empty_lines_from_txt(folder):
    for filename in os.listdir(folder):
        if filename.lower().endswith(".txt"):
            file_path = os.path.join(folder, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # 去掉空行：strip() 后为空串的行视为空行
            new_lines = [line for line in lines if line.strip() != ""]

            # 如果文件内容有变化则写回
            if new_lines != lines:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                print(f"✔ Cleaned empty lines: {filename}")
            else:
                print(f"✓ No empty lines: {filename}")

if __name__ == "__main__":
    folder_path = r"E:\roadbarries\labels\train"   # 修改为你的文件夹路径
    remove_empty_lines_from_txt(folder_path)



# import os

# # 指定你的文件夹路径
# folder = r"E:\object_detection_dataset\excavator_data\output\gen_photos\labels"

# # 遍历文件夹下所有txt文件
# for filename in os.listdir(folder):
#     if filename.lower().endswith(".txt"):
#         file_path = os.path.join(folder, filename)
        
#         # 读取原文件内容
#         with open(file_path, "r", encoding="utf-8") as f:
#             lines = f.readlines()
        
#         # 修改标签
#         new_lines = []
#         for line in lines:
#             parts = line.strip().split()
#             if parts and parts[0] == "0":
#                 parts[0] = "1"
#             new_lines.append(" ".join(parts))
        
#         # 写回文件
#         with open(file_path, "w", encoding="utf-8") as f:
#             f.write("\n".join(new_lines) + "\n")

# print("已将所有txt文件中的标签0改为1。")
