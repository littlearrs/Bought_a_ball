import os
from PIL import Image

def make_collage(image_paths, save_path, output_size=(1920, 1080)):
    """
    image_paths: 4张图片的路径
    save_path: 保存路径
    output_size: 最终拼接图尺寸 (宽, 高)
    """
    w, h = output_size
    collage = Image.new('RGB', (w, h), (0, 0, 0))

    # 每个小图的尺寸（均分）
    small_w = w // 2
    small_h = h // 2

    positions = [
        (0, 0),               # 左上
        (small_w, 0),         # 右上
        (0, small_h),         # 左下
        (small_w, small_h)    # 右下
    ]

    for img_path, pos in zip(image_paths, positions):
        img = Image.open(img_path).convert('RGB')
        img = img.resize((small_w, small_h))  # 缩放
        collage.paste(img, pos)

    collage.save(save_path)
    print(f"Saved collage: {save_path}")

def process_folder(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    # 获取所有图片文件
    exts = ('.jpg', '.jpeg', '.png', '.bmp')
    images = [os.path.join(input_folder, f) for f in sorted(os.listdir(input_folder))
              if f.lower().endswith(exts)]

    # 每4张为一组
    for i in range(0, len(images), 4):
        batch = images[i:i+4]

        # 不足4张的部分跳过
        if len(batch) < 4:
            break

        save_path = os.path.join(output_folder, f"collage_{i//4:04d}.jpg")
        make_collage(batch, save_path)


if __name__ == "__main__":
    input_folder = r"E:\object_detection_dataset\vehicle_data\drilling_rig\images2"    # 修改你的图片路径
    output_folder = r"E:\object_detection_dataset\vehicle_data\drilling_rig\images3"   # 修改输出路径

    process_folder(input_folder, output_folder)
