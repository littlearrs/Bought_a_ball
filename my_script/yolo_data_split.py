import os
import shutil
from tqdm import tqdm


def split_img(img_path, label_path, save_root, split_list, mode="cluster"):
    """
    将图像和标签按比例划分为 train / val

    Args:
        img_path: 图片目录
        label_path: 标签目录
        save_root: 数据保存根目录 (比如 E:/dataset/well_split)
        split_list: [train比例, val比例]  
        mode: 划分方式 ("random" 随机 / "sequential" 顺序 / "cluster" 簇划分)
    """
    # 输出目录
    print("mode:", mode)
    train_img_dir = os.path.join(save_root, 'images/train')
    val_img_dir = os.path.join(save_root, 'images/val')
    train_label_dir = os.path.join(save_root, 'labels/train')
    val_label_dir = os.path.join(save_root, 'labels/val')

    os.makedirs(train_img_dir, exist_ok=True)
    os.makedirs(train_label_dir, exist_ok=True)
    os.makedirs(val_img_dir, exist_ok=True)
    os.makedirs(val_label_dir, exist_ok=True)

    all_img = [f for f in os.listdir(img_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    all_img.sort()  # 顺序保证一致
    all_img_path = [os.path.join(img_path, img) for img in all_img]
    total_num = len(all_img_path)

    train_ratio, val_ratio = split_list

    if mode == "random":
        import random
        train_num = int(train_ratio * total_num)
        train_img = random.sample(all_img_path, train_num)
        val_img = list(set(all_img_path) - set(train_img))

    elif mode == "sequential":
        train_num = int(train_ratio * total_num)
        train_img = all_img_path[:train_num]
        val_img = all_img_path[train_num:]

    elif mode == "cluster":
        cluster_size = 10  # 每簇固定大小
        train_img, val_img = [], []
        for i in range(0, total_num, cluster_size):
            cluster = all_img_path[i:i + cluster_size]
            if len(cluster) < cluster_size:  # 不够一簇 → 全部给训练集
                train_img.extend(cluster)
            else:
                k = int(train_ratio * cluster_size)
                train_img.extend(cluster[:k])
                val_img.extend(cluster[k:])
    else:
        raise ValueError("mode must be 'random', 'sequential' or 'cluster'")

    # ========= 拷贝 =========
    _copy_dataset(train_img, label_path, train_img_dir, train_label_dir, desc="train")
    _copy_dataset(val_img, label_path, val_img_dir, val_label_dir, desc="val")


def _copy_dataset(img_list, label_path, img_dir, label_dir, desc="train"):
    labels = [toLabelPath(img, label_path) for img in img_list]
    img_copy = [os.path.join(img_dir, os.path.basename(img)) for img in img_list]
    label_copy = [os.path.join(label_dir, os.path.basename(label)) for label in labels]

    for i in tqdm(range(len(img_list)), desc=desc, ncols=80, unit='img'):
        _copy(img_list[i], img_copy[i])
        _copy(labels[i], label_copy[i])


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
    img_path = r'D:\artifical\Baggages\images'
    label_path = r'D:\artifical\Baggages\labels'
    save_root = r'D:\artifical\Baggages\airport_xray'
    split_list = [0.8, 0.2]  # [train:val]
    split_img(img_path, label_path, save_root, split_list, mode="cluster")

