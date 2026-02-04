# import os

# def modify_yolo_labels(label_dir, class_to_remove):
#     """
#     修改YOLO标签，删除某个类及其对应的检测框，并调整后续类编号
#     :param label_dir: 标签文件夹路径
#     :param class_to_remove: 要删除的类别序号 (int)
#     """
#     # 遍历所有标签文件
#     for label_file in os.listdir(label_dir):
#         if not label_file.endswith(".txt"):
#             continue

#         file_path = os.path.join(label_dir, label_file)

#         new_lines = []
#         with open(file_path, "r") as f:
#             lines = f.readlines()
#             for line in lines:
#                 parts = line.strip().split()
#                 if len(parts) < 5:  # YOLO格式至少5列: class x y w h
#                     continue
                
#                 cls = int(parts[0])

#                 if cls == class_to_remove:
#                     # 删除该类别
#                     continue
#                 elif cls > class_to_remove:
#                     # 类别编号减一
#                     cls -= 1

#                 # 更新类别编号并保存
#                 new_line = " ".join([str(cls)] + parts[1:])
#                 new_lines.append(new_line)

#         # 写回文件（覆盖原文件）
#         with open(file_path, "w") as f:
#             f.write("\n".join(new_lines) + ("\n" if new_lines else ""))

#     print(f"处理完成！类别 {class_to_remove} 已删除，后续类别编号已调整。")


# if __name__ == "__main__":
#     # 修改这里的路径和要删除的类别
#     label_dir = r"E:\object_detection_dataset\well_data\well_random\labels\val"  # 你的标签文件夹
#     class_to_remove = 3  # 要删除的类别ID
#     modify_yolo_labels(label_dir, class_to_remove)



import os

# --------------------------
# 配置
# --------------------------
images_folder = r"E:\object_detection_dataset\well_data\well_data2_yolo\well_dataset\images"  # 图片文件夹
labels_folder = r"E:\object_detection_dataset\well_data\well_data2_yolo\well_dataset\labels"  # 标签文件夹
image_exts = ['.jpg', '.jpeg', '.png']  # 图片后缀
recursive = False  # 是否递归子文件夹
# --------------------------

def delete_empty_labels(images_folder, labels_folder, image_exts, recursive=False):
    if recursive:
        for root, dirs, files in os.walk(labels_folder):
            _process_folder(root, files, images_folder, image_exts)
    else:
        files = os.listdir(labels_folder)
        _process_folder(labels_folder, files, images_folder, image_exts)

def _process_folder(labels_folder, files, images_folder, image_exts):
    for file in files:
        if file.endswith(".txt"):
            txt_path = os.path.join(labels_folder, file)
            # 检查文件是否为空
            if os.path.getsize(txt_path) == 0:
                # 删除 txt 文件
                os.remove(txt_path)
                print(f"删除空标签: {txt_path}")
                # 删除对应图片
                base_name = os.path.splitext(file)[0]
                deleted_image = False
                for ext in image_exts:
                    img_path = os.path.join(images_folder, base_name + ext)
                    if os.path.exists(img_path):
                        os.remove(img_path)
                        print(f"删除对应图片: {img_path}")
                        deleted_image = True
                        break
                if not deleted_image:
                    print(f"未找到对应图片: {base_name}.*")

if __name__ == "__main__":
    delete_empty_labels(images_folder, labels_folder, image_exts, recursive)
