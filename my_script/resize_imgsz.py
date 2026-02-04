import os
import cv2
from tqdm import tqdm

def resize_images(input_dir, output_dir, target_size=(1920, 1080)):
    """
    批量调整图片分辨率，使用双三次插值（cv2.INTER_CUBIC）
    :param input_dir: 输入图片文件夹
    :param output_dir: 输出图片文件夹
    :param target_size: 目标分辨率 (宽, 高)，默认 (1920, 1080)
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 支持的图片格式
    img_exts = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]

    for file in tqdm(os.listdir(input_dir), desc="Processing images"):
        ext = os.path.splitext(file)[1].lower()
        if ext in img_exts:
            img_path = os.path.join(input_dir, file)
            img = cv2.imread(img_path)

            if img is None:
                print(f"⚠️ 无法读取 {img_path}")
                continue

            # 调整分辨率
            resized = cv2.resize(img, target_size, interpolation=cv2.INTER_CUBIC)

            # 输出路径（保持原格式）
            save_path = os.path.join(output_dir, file)

            # PNG 无损保存 / JPEG 最高质量保存
            if ext in [".jpg", ".jpeg"]:
                cv2.imwrite(save_path, resized, [cv2.IMWRITE_JPEG_QUALITY, 100])
            else:
                cv2.imwrite(save_path, resized, [cv2.IMWRITE_PNG_COMPRESSION, 0])

    print(f"✅ 所有图片已处理完成，保存在：{output_dir}")

if __name__ == "__main__":
    input_dir = r"C:\Users\liyang01\Desktop\i_data\2"     # 输入文件夹
    output_dir = r"C:\Users\liyang01\Desktop\i_data\2"   # 输出文件夹
    target_size = (640, 640)         # 目标分辨率
    resize_images(input_dir, output_dir, target_size)
