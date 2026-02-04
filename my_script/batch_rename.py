import os

def batch_rename(folder_path, prefix, start_num):
    exts = ('.jpg', '.jpeg', '.png', '.txt', 'Mp4', 'mp4')  # 支持的文件扩展名
    # exts = ('mp4')  # 支持的文件扩展名
    files = [f for f in os.listdir(folder_path)
             if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith(exts)]
    files.sort()
    num_len = max(4, len(str(start_num + len(files) - 1)))  # 自动补零，至少4位
    for idx, filename in enumerate(files):
        ext = os.path.splitext(filename)[1]
        num_str = str(start_num + idx).zfill(num_len)
        new_name = f"{prefix}{num_str}{ext}"
        src = os.path.join(folder_path, filename)
        dst = os.path.join(folder_path, new_name)
        os.rename(src, dst)
        print(f"重命名: {filename} -> {new_name}")

if __name__ == "__main__":
    folder = r"E:\object_detection_dataset\roadbarriers\barrier3\img"                  # 请输入要重命名的文件夹路径：
    prefix = "barrier3_"                  # 请输入文件名前缀：
    start_num = int(input("请输入起始序号："))
    batch_rename(folder, prefix, start_num)



# import os

# def batch_rename_replace(folder_path, old_text, new_text):
#     """
#     在文件名中查找并替换指定字符串（仅修改文件名，不改扩展名）

#     :param folder_path: 要处理的文件夹路径
#     :param old_text: 要被替换的旧字符串
#     :param new_text: 替换后的新字符串
#     """
#     exts = ('.jpg', '.jpeg', '.png', '.txt', '.mp4')  # 支持的扩展名
#     files = [f for f in os.listdir(folder_path)
#              if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith(exts)]
#     files.sort()

#     for filename in files:
#         name, ext = os.path.splitext(filename)

#         # 只处理包含 old_text 的文件
#         if old_text in name:
#             new_name = name.replace(old_text, new_text) + ext
#             src = os.path.join(folder_path, filename)
#             dst = os.path.join(folder_path, new_name)

#             if not os.path.exists(dst):
#                 os.rename(src, dst)
#                 print(f"重命名: {filename} -> {new_name}")
#             else:
#                 print(f"⚠️ 跳过（目标已存在）: {new_name}")
#         else:
#             print(f"跳过（未包含目标字符串）: {filename}")

# if __name__ == "__main__":
#     # ====== 参数配置 ======
#     folder = r"E:\object_detection_dataset\change_detection\building-cd\CD20251016_0001\output\B"
#     old_text = "_0001_001"   # 文件名中要被替换的部分
#     new_text = "_0001_000"          # 替换成的新内容
#     # ======================

#     batch_rename_replace(folder, old_text, new_text)


