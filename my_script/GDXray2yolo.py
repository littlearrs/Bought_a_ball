import os
import cv2


def map_number_to_filename(dir_name, number):
    """
    将数字映射为特定的文件名格式
    """
    number_str = format(number, '.0f')
    number_str_padded = number_str.zfill(4)

    img_name = f"{dir_name}_{number_str_padded}.png"
    label_name = f"{dir_name}_{number_str_padded}.txt"

    return label_name, img_name


def get_image_dimensions(image_path, pos_list):
    """
    根据图片尺寸，将 bbox 转为 YOLO 格式
    pos_list: [xmin, xmax, ymin, ymax]
    """
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"❌ 无法读取图片: {image_path}")

    height, width = image.shape[:2]

    xmin = float(pos_list[0])
    xmax = float(pos_list[1])
    ymin = float(pos_list[2])
    ymax = float(pos_list[3])

    bw = xmax - xmin
    bh = ymax - ymin
    bx = (xmin + xmax) / 2.0
    by = (ymin + ymax) / 2.0

    x = bx / width
    y = by / height
    w = bw / width
    h = bh / height

    return [x, y, w, h]


if __name__ == "__main__":
    dir_path = r"D:\artifical\Baggages\Baggages\B0045"
    dir_basename = os.path.basename(dir_path)

    ground_truth_txt = os.path.join(dir_path, 'ground_truth.txt')
    save_txt_dir = os.path.join(os.path.dirname(dir_path), f"YOLO_{dir_basename}")
    os.makedirs(save_txt_dir, exist_ok=True)

    with open(ground_truth_txt, 'r', encoding='utf-8') as f:
        contents = f.readlines()

    for line in contents:
        # ✅ 自动处理任意空格 / Tab
        content = line.strip().split()
        if len(content) < 5:
            continue

        filename, img_name = map_number_to_filename(
            dir_name=dir_basename,
            number=float(content[0])
        )

        img_path = os.path.join(dir_path, img_name)
        yolo_pos_list = get_image_dimensions(img_path, pos_list=content[1:5])

        save_filename = os.path.join(save_txt_dir, filename)

        # ✅ labelImg / YOLO 标准写法
        with open(save_filename, 'a', encoding='utf-8') as f_s:
            f_s.write(
                "{} {:.6f} {:.6f} {:.6f} {:.6f}\n".format(
                    3,  # class id
                    yolo_pos_list[0],  # knife
                    yolo_pos_list[1],  # scissor
                    yolo_pos_list[2],  # gun
                    yolo_pos_list[3]   # blade
                )
            )

    print("✅ YOLO 标签转换完成（labelImg 可直接打开）")
