import os
import cv2
from tqdm import tqdm

def split_image(image, tile_size, overlap_w=0.0, overlap_h=0.0, crop_w=192):
    """
    切分单张图片为多个小块（横向可裁剪、纵向不允许不足 tile_h）
    """
    h, w = image.shape[:2]
    tile_w, tile_h = tile_size

    # 横向裁剪
    left_crop = crop_w // 2
    right_crop = crop_w - left_crop
    x_start_limit = left_crop
    x_end_limit = w - right_crop

    stride_w = int(tile_w * (1 - overlap_w))
    stride_h = int(tile_h * (1 - overlap_h))

    tiles = []
    # 纵向切分：仅保留完整 tile_h 的块
    for y in range(0, h - tile_h + 1, stride_h):
        for x in range(x_start_limit, x_end_limit, stride_w):
            x_end = min(x + tile_w, x_end_limit)
            x_start = max(x_end - tile_w, x_start_limit)
            tile = image[y:y + tile_h, x_start:x_end]
            tiles.append((x_start, y, tile))

    return tiles


def batch_split_images(input_dir, output_dir, tile_size=(1920, 1080),
                       overlap_w=0.0, overlap_h=0.0, crop_w=192):
    os.makedirs(output_dir, exist_ok=True)

    images = [f for f in os.listdir(input_dir)
              if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    print(f"发现 {len(images)} 张图片，开始切分...")

    for img_name in tqdm(images):
        img_path = os.path.join(input_dir, img_name)
        image = cv2.imread(img_path)
        if image is None:
            print(f"⚠️ 无法读取图片: {img_name}")
            continue

        tiles = split_image(image, tile_size, overlap_w, overlap_h, crop_w)
        base_name = os.path.splitext(img_name)[0]

        for i, (x, y, tile) in enumerate(tiles):
            save_path = os.path.join(output_dir, f"{base_name}_x{x}_y{y}.png")
            cv2.imwrite(save_path, tile)


if __name__ == "__main__":
    input_folder = r"E:\object_detection_dataset\change_detection\data2\CD20251015_0033\B"
    output_folder = r"E:\object_detection_dataset\change_detection\data2\CD20251015_0033\B"
    tile_size = (1920, 1080)  # 切块尺寸 w h
    overlap_w = 0.0           # 横向不重叠
    overlap_h = 0.1           # 纵向不重叠
    crop_w = 192              # 横向左右共裁剪像素数

    batch_split_images(input_folder, output_folder, tile_size,
                       overlap_w, overlap_h, crop_w)


