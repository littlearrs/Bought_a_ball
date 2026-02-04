# import os

# # ====== 配置区 ======
# LABEL_DIR = r"D:\artifical\OPIXray\test\labels"  # 改成你的 labels 路径
# TARGET_CLASSES = {2}             # 要合并的类别
# NEW_CLASS = 1                          # 统一变成的类别
# # ===================

# for file in os.listdir(LABEL_DIR):
#     if not file.endswith(".txt"):
#         continue

#     path = os.path.join(LABEL_DIR, file)
#     new_lines = []

#     with open(path, "r") as f:
#         for line in f:
#             line = line.strip()
#             if not line:
#                 continue

#             parts = line.split()
#             cls_id = int(parts[0])

#             # 核心逻辑：1 / 3 / 4 → 4
#             if cls_id in TARGET_CLASSES:
#                 parts[0] = str(NEW_CLASS)

#             new_lines.append(" ".join(parts) + "\n")

#     with open(path, "w") as f:
#         f.writelines(new_lines)

# print("✅ 已完成")


# import os

# LABEL_DIR = r"D:\artifical\Baggages\airport_xray\labels\train"  # 你的 YOLO txt 标签目录

# for file in os.listdir(LABEL_DIR):
#     if not file.endswith(".txt"):
#         continue

#     path = os.path.join(LABEL_DIR, file)
#     new_lines = []

#     with open(path, "r") as f:
#         for line in f:
#             parts = line.strip().split()
#             if len(parts) != 5:
#                 # 过滤掉空行或错误行
#                 continue
#             new_lines.append(" ".join(parts) + "\n")

#     with open(path, "w") as f:
#         f.writelines(new_lines)

# print("✅ 已清理所有非法行（空行/列数不为5）")


# import os

# # =======================
# # 配置区
# LABEL_DIR = r"D:\artifical\Baggages\airport_xray\labels\val"  # 改成你的 YOLO 标签文件夹
# MAX_CLASS_ID = 4                        # 合法最大 class_id
# # =======================

# illegal = set()       # 用于存放非法 class_id
# illegal_files = {}    # 记录哪些文件有非法 class_id

# for file in os.listdir(LABEL_DIR):
#     if not file.endswith(".txt"):
#         continue

#     path = os.path.join(LABEL_DIR, file)
#     with open(path, "r") as f:
#         for line_num, line in enumerate(f, start=1):
#             line = line.strip()
#             if not line:
#                 continue  # 跳过空行
#             parts = line.split()
#             if len(parts) != 5:
#                 print(f"⚠️ 文件 {file} 第 {line_num} 行格式不正确: {line}")
#                 continue
#             try:
#                 cls = int(parts[0])
#                 if cls > MAX_CLASS_ID:
#                     illegal.add(cls)
#                     if file not in illegal_files:
#                         illegal_files[file] = []
#                     illegal_files[file].append((line_num, cls))
#             except ValueError:
#                 print(f"⚠️ 文件 {file} 第 {line_num} 行 class_id 无法转换为整数: {line}")

# # 输出结果
# if not illegal:
#     print("✅ 所有 class_id 都合法，没有超过最大值。")
# else:
#     print(f"❌ 出现非法 class_id: {illegal}")
#     for file, entries in illegal_files.items():
#         for line_num, cls in entries:
#             print(f" - 文件 {file} 第 {line_num} 行 class_id = {cls}")



import os

# ================= 配置区 =================
LABEL_DIR = r"D:\artifical\Baggages\airport_xray\labels\val"  # 改成你的 labels 目录
VALID_CLASSES = {0, 1, 2, 3, 4}
CLASS_NAME_MAP = {
    0: "straight_knife",
    1: "scissor",
    2: "gun",
    3: "blade",
    4: "folding_knife"
}
# =========================================


def check_yolo_labels(label_dir):
    error_files = []

    for file in os.listdir(label_dir):
        if not file.endswith(".txt"):
            continue

        file_path = os.path.join(label_dir, file)

        with open(file_path, "r") as f:
            lines = f.readlines()

        for idx, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue

            parts = line.split()

            # 1️⃣ 检查字段数量
            if len(parts) != 5:
                error_files.append(
                    (file, idx, "字段数量错误", line)
                )
                continue

            # 2️⃣ 检查类别是否合法
            try:
                cls_id = int(parts[0])
            except ValueError:
                error_files.append(
                    (file, idx, "类别不是整数", line)
                )
                continue

            if cls_id not in VALID_CLASSES:
                error_files.append(
                    (file, idx, f"非法类别 {cls_id}", line)
                )

    # ================= 输出结果 =================
    if not error_files:
        print("✅ 所有 YOLO 标注文件均合法，类别符合 0~4")
    else:
        print(f"❌ 共发现 {len(error_files)} 处错误：\n")
        for file, line_no, reason, content in error_files:
            print(f"[文件] {file}")
            print(f"[行号] {line_no}")
            print(f"[原因] {reason}")
            print(f"[内容] {content}")
            print("-" * 50)


if __name__ == "__main__":
    check_yolo_labels(LABEL_DIR)
