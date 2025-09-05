import os
import shutil
import random
from tqdm import tqdm


def split_img(img_path, label_path, save_root, split_list, mode="random"):
    """
    将图像和标签按比例划分为 train / val

    Args:
        img_path: 图片目录
        label_path: 标签目录
        save_root: 数据保存根目录 (比如 E:/dataset/well_split)
        split_list: [train比例, val比例]
        mode: 划分方式 ("random" 随机 / "sequential" 顺序)
    """
    # 输出目录
    train_img_dir = os.path.join(save_root, 'images/train')
    val_img_dir = os.path.join(save_root, 'images/val')
    train_label_dir = os.path.join(save_root, 'labels/train')
    val_label_dir = os.path.join(save_root, 'labels/val')

    os.makedirs(train_img_dir, exist_ok=True)
    os.makedirs(train_label_dir, exist_ok=True)
    os.makedirs(val_img_dir, exist_ok=True)
    os.makedirs(val_label_dir, exist_ok=True)

    train_ratio, val_ratio = split_list
    all_img = [f for f in os.listdir(img_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    all_img.sort()  # 顺序保证一致

    all_img_path = [os.path.join(img_path, img) for img in all_img]
    total_num = len(all_img_path)
    train_num = int(train_ratio * total_num)

    # 选择划分方式
    if mode == "random":
        train_img = random.sample(all_img_path, train_num)
    elif mode == "sequential":
        train_img = all_img_path[:train_num]
    else:
        raise ValueError("mode must be 'random' or 'sequential'")

    # 训练集
    train_label = [toLabelPath(img, label_path) for img in train_img]
    train_img_copy = [os.path.join(train_img_dir, os.path.basename(img)) for img in train_img]
    train_label_copy = [os.path.join(train_label_dir, os.path.basename(label)) for label in train_label]

    for i in tqdm(range(len(train_img)), desc='train ', ncols=80, unit='img'):
        _copy(train_img[i], train_img_copy[i])
        _copy(train_label[i], train_label_copy[i])

    # 验证集
    if mode == "random":
        val_img = list(set(all_img_path) - set(train_img))
    else:  # sequential
        val_img = all_img_path[train_num:]

    val_label = [toLabelPath(img, label_path) for img in val_img]
    val_img_copy = [os.path.join(val_img_dir, os.path.basename(img)) for img in val_img]
    val_label_copy = [os.path.join(val_label_dir, os.path.basename(label)) for label in val_label]

    for i in tqdm(range(len(val_img)), desc='val ', ncols=80, unit='img'):
        _copy(val_img[i], val_img_copy[i])
        _copy(val_label[i], val_label_copy[i])


def _copy(from_path, to_path):
    try:
        shutil.copy(from_path, to_path)
    except Exception as e:
        print(f"[ERROR] Failed to copy {from_path} ➜ {to_path}: {e}")


def toLabelPath(img_path, label_path):
    name, _ = os.path.splitext(os.path.basename(img_path))
    label = name + '.txt'
    return os.path.join(label_path, label)


if __name__ == '__main__':
    img_path = r'E:\object_detection_dataset\well_data\well_data2_yolo\set_7_labels_yolo\images'
    label_path = r'E:\object_detection_dataset\well_data\well_data2_yolo\set_7_labels_yolo\labels'
    save_root = r'E:\object_detection_dataset\well_data\well_data2_yolo\well_random2'  # 输出路径可以自定义
    split_list = [0.9, 0.1]  # [train:val]
    split_img(img_path, label_path, save_root, split_list, mode="random")
