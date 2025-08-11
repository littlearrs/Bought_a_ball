import os
import shutil
import random
from tqdm import tqdm


def split_img(img_path, label_path, split_list):
    Data = r'E:\new_data'
    train_img_dir = os.path.join(Data, 'images/train')
    val_img_dir = os.path.join(Data, 'images/val')
    train_label_dir = os.path.join(Data, 'labels/train')
    val_label_dir = os.path.join(Data, 'labels/val')

    os.makedirs(train_img_dir, exist_ok=True)
    os.makedirs(train_label_dir, exist_ok=True)
    os.makedirs(val_img_dir, exist_ok=True)
    os.makedirs(val_label_dir, exist_ok=True)

    train, val = split_list
    all_img = os.listdir(img_path)
    all_img_path = [os.path.join(img_path, img) for img in all_img]

    train_img = random.sample(all_img_path, int(train * len(all_img_path)))
    train_label = [toLabelPath(img, label_path) for img in train_img]
    train_img_copy = [os.path.join(train_img_dir, os.path.basename(img)) for img in train_img]
    train_label_copy = [os.path.join(train_label_dir, os.path.basename(label)) for label in train_label]

    for i in tqdm(range(len(train_img)), desc='train ', ncols=80, unit='img'):
        _copy(train_img[i], train_img_copy[i])
        _copy(train_label[i], train_label_copy[i])
        all_img_path.remove(train_img[i])

    val_img = all_img_path
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
    img_path = r'E:\new_data\images'
    label_path = r'E:\new_data\labels'
    split_list = [0.8, 0.2]  # 数据集划分比例[train:val]
    split_img(img_path, label_path, split_list)
