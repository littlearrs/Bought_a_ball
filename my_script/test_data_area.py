import os
import glob
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

def analyze_target_area(img_dir, label_dir, percentile=5):
    """
    分析训练集目标面积分布，输出直方图并给出 min_area 建议

    Args:
        img_dir (str): 图片路径
        label_dir (str): 标签路径（YOLO txt）
        percentile (float): 去掉最小多少百分比目标（默认5%）
    Returns:
        min_area (int): 建议的最小面积阈值
    """
    areas = []

    label_files = glob.glob(os.path.join(label_dir, "*.txt"))
    if not label_files:
        raise FileNotFoundError("标签文件夹为空或路径错误")

    for label_file in label_files:
        # 对应图片路径
        img_name = os.path.basename(label_file).replace(".txt", ".jpg")
        img_path = os.path.join(img_dir, img_name)
        if not os.path.exists(img_path):
            continue  # 忽略缺失图片
        
        img_w, img_h = Image.open(img_path).size
        
        with open(label_file, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                cls, x_center, y_center, w, h = map(float, parts)
                box_w = w * img_w
                box_h = h * img_h
                areas.append(box_w * box_h)
    
    areas = np.array(areas)
    
    # 绘制面积直方图
    plt.figure(figsize=(8,5))
    plt.hist(areas, bins=50, color='skyblue', edgecolor='black')
    plt.xlabel("Bounding Box Area (pixels²)")
    plt.ylabel("Number of Targets")
    plt.title("Training Target Area Distribution")
    plt.grid(True)
    plt.show()
    
    # 建议 min_area
    min_area = int(np.percentile(areas, percentile))
    print(f"建议 min_area 阈值（去掉最小 {percentile}%）：{min_area}")
    return min_area

# 示例使用
img_dir = r"E:\object_detection_dataset\well_data\well_data4_yolo\well_4\images\train"
label_dir = r"E:\object_detection_dataset\well_data\well_data4_yolo\well_4\labels\train"

min_area = analyze_target_area(img_dir, label_dir, percentile=5)
