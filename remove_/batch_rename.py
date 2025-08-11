import os

def batch_rename(folder_path, prefix, start_num):
    exts = ('.jpg', '.jpeg', '.png')
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
    folder = r"D:\Vscode_Project\data"                  # 请输入要重命名的文件夹路径：
    prefix = "image_"                  # 请输入文件名前缀：
    start_num = int(input("请输入起始序号："))
    batch_rename(folder, prefix, start_num)