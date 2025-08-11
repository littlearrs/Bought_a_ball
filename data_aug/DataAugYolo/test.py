import os

# B 部分标签文件所在目录
wrong_label_dir = r'E:\object_detection_dataset\sv_data\labels\train/'  # ← 修改为你的实际路径

for file_name in os.listdir(wrong_label_dir):
    if not file_name.endswith('.txt'):
        continue
    file_path = os.path.join(wrong_label_dir, file_name)
    with open(file_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        parts = line.strip().split()
        if not parts:
            continue
        cls_id = parts[0]
        if cls_id == '0':
            parts[0] = '1'
        elif cls_id == '1':
            parts[0] = '0'
        new_lines.append(' '.join(parts))

    with open(file_path, 'w') as f:
        f.write('\n'.join(new_lines) + '\n')

print("✅ B 部分标签已统一为：0 = kiosk，1 = street_vendors")
