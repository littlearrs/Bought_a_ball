import os
import shutil

# ===== 配置区 =====
ROOT_DIR = r"D:\artifical\Baggages\images"        # 原始数据根目录
OUT_LABEL_DIR = r"D:\artifical\Baggages\images"  # 合并后的 labels 目录
# ==================

os.makedirs(OUT_LABEL_DIR, exist_ok=True)

for root, dirs, files in os.walk(ROOT_DIR):
    # 跳过输出目录本身
    if os.path.abspath(root) == os.path.abspath(OUT_LABEL_DIR):
        continue

    folder_name = os.path.basename(root)

    for file in files:
        if not file.lower().endswith(".png"):
            continue

        src_path = os.path.join(root, file)

        # 防止重名：文件夹名_原文件名.txt
        new_name = f"{folder_name}_{file}"
        dst_path = os.path.join(OUT_LABEL_DIR, new_name)

        shutil.copy(src_path, dst_path)

print("✅ 所有标签已合并到 labels 文件夹")
