"""
旋转目标检测-图像贴图工具 - 纯贴图

功能：在指定的ROI区域内贴图，支持多类前景图片，支持旋转和透明度处理

注意：可按照自己需求修改类别及对应的按钮

"""

import os
import random
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QWidget, QFileDialog,
                             QComboBox, QCheckBox, QMessageBox)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QPoint
from pathlib import Path
import shutil
from PyQt5.QtWidgets import QSlider
import time
import math

class ImagePasteApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图像贴图工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化变量
        self.image_folder = ""
        self.current_image_path = ""
        self.current_image_index = 0
        self.image_paths = []
        self.foreground_folders = {
            0: "",  # cone
        }
        self.rois = []  # 存储用户划定的ROI区域 (x1, y1, x2, y2)
        self.drawing = False
        self.start_point = QPoint()
        self.temp_roi = None
        self.output_folder = ""
        self.roi_foregrounds = []  # 新增：保存每个ROI对应的前景图片路径

        self.fg_indices = {0: 0, 1: 0, 2: 0, 3: 0} # 新增：每类前景图片索引

        # 创建UI
        self.init_ui()
        
    def init_ui(self):
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 图像显示区域
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: black;")
        self.image_label.mousePressEvent = self.mouse_press
        self.image_label.mouseMoveEvent = self.mouse_move
        self.image_label.mouseReleaseEvent = self.mouse_release
        
        # 控制面板
        control_panel = QWidget()
        control_layout = QHBoxLayout()
        control_panel.setLayout(control_layout)
        
        # 按钮和控件
        self.btn_load_folder = QPushButton("加载图片文件夹")
        self.btn_load_folder.clicked.connect(self.load_image_folder)
        
        self.btn_load_foreground0 = QPushButton("加载banner前景文件夹")
        self.btn_load_foreground0.clicked.connect(lambda: self.load_foreground_folder(0))
        
        self.btn_set_output = QPushButton("设置输出文件夹")
        self.btn_set_output.clicked.connect(self.set_output_folder)
        
        self.class_combo = QComboBox()
        self.class_combo.addItems(["banner (类别0)",
                                ])
        
        self.btn_add_roi = QPushButton("添加ROI")
        self.btn_add_roi.clicked.connect(self.add_roi)
        
        self.btn_clear_rois = QPushButton("清除所有ROI")
        self.btn_clear_rois.clicked.connect(self.clear_rois)
        
        self.btn_paste = QPushButton("贴图")
        self.btn_paste.clicked.connect(self.paste_images)
        
        self.btn_save = QPushButton("保存")
        self.btn_save.clicked.connect(self.save_result)

        self.btn_prev = QPushButton("上一张")
        self.btn_prev.clicked.connect(self.prev_image)
        
        self.btn_next = QPushButton("下一张")
        self.btn_next.clicked.connect(self.next_image)

        # 在init_ui的按钮和控件部分添加
        self.rotate_label = QLabel("旋转角度: 0°")
        self.rotate_slider = QSlider(Qt.Horizontal)
        self.rotate_slider.setMinimum(0)
        self.rotate_slider.setMaximum(359)
        self.rotate_slider.setValue(0)
        self.rotate_slider.setTickInterval(1)
        self.rotate_slider.valueChanged.connect(self.on_rotate_slider_changed)
                
        # 添加到控制面板
        control_layout.addWidget(self.btn_load_folder)
        control_layout.addWidget(self.btn_load_foreground0)
        control_layout.addWidget(self.btn_set_output)
        control_layout.addWidget(self.class_combo)
        control_layout.addWidget(self.btn_add_roi)
        control_layout.addWidget(self.btn_clear_rois)
        control_layout.addWidget(self.btn_paste)
        control_layout.addWidget(self.btn_save)
        control_layout.addWidget(self.btn_prev)
        control_layout.addWidget(self.btn_next)
        control_layout.addWidget(self.rotate_label)
        control_layout.addWidget(self.rotate_slider)
        
        # 添加到主布局
        main_layout.addWidget(self.image_label, stretch=8)
        main_layout.addWidget(control_panel, stretch=2)
        
        # 状态栏
        self.statusBar().showMessage("准备就绪")
        
    def load_image_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if folder:
            self.image_folder = folder
            self.image_paths = [os.path.join(folder, f) for f in os.listdir(folder) 
                               if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            random.shuffle(self.image_paths)  # 随机打乱图片顺序
            self.current_image_index = 0
            if self.image_paths:
                self.load_current_image()
                self.statusBar().showMessage(f"已加载 {len(self.image_paths)} 张图片")
            else:
                self.statusBar().showMessage("文件夹中没有找到图片")

    def on_rotate_slider_changed(self, v):
        self.rotate_label.setText(f"旋转角度: {v}°")
        # 只有已经贴过图才实时刷新
        if hasattr(self, 'original_image') and self.rois:
            self.paste_images(keep_foreground=True)

    def load_foreground_folder(self, class_id):
        folder = QFileDialog.getExistingDirectory(self, f"选择类别{class_id}前景文件夹")
        if folder:
            self.foreground_folders[class_id] = folder
            self.fg_indices[class_id] = 0  # 新增：重置索引
            self.statusBar().showMessage(f"类别{class_id}前景文件夹已设置: {folder}")
    
    def set_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_folder = folder
            # 创建必要的子文件夹
            Path(os.path.join(folder, "gen_photos", "images")).mkdir(parents=True, exist_ok=True)
            Path(os.path.join(folder, "gen_photos", "labels")).mkdir(parents=True, exist_ok=True)
            self.statusBar().showMessage(f"输出文件夹已设置: {folder}")
    
    def load_current_image(self):
        if 0 <= self.current_image_index < len(self.image_paths):
            self.current_image_path = self.image_paths[self.current_image_index]
            self.original_image = cv2.imread(self.current_image_path)
            self.display_image(self.original_image)
            self.rois = []  # 清除之前的ROI
            self.roi_foregrounds = []  # 清除前景选择记录
            self.statusBar().showMessage(f"当前图片: {os.path.basename(self.current_image_path)} ({self.current_image_index+1}/{len(self.image_paths)})")
    
    def display_image(self, image):
        if image is not None:
            # 将OpenCV图像转换为Qt图像
            height, width, channel = image.shape
            bytes_per_line = 3 * width
            q_img = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            
            # 创建QPixmap并绘制ROI
            pixmap = QPixmap.fromImage(q_img)
            painter = QPainter(pixmap)
            painter.setPen(QPen(QColor(0, 255, 0), 2))
            
            # 绘制已确定的ROI
            for roi in self.rois:
                x1, y1, x2, y2 = roi
                painter.drawRect(x1, y1, x2-x1, y2-y1)
            
            # 绘制正在划定的ROI
            if self.temp_roi:
                x1, y1, x2, y2 = self.temp_roi
                painter.drawRect(x1, y1, x2-x1, y2-y1)
            
            painter.end()
            
            # 缩放显示
            scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
    
    def mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_point = event.pos()
            self.temp_roi = None
    
    def mouse_move(self, event):
        if self.drawing and hasattr(self, 'original_image'):
            end_point = event.pos()
            # 确保坐标转换正确（从屏幕坐标到图像坐标）
            if self.image_label.pixmap():
                # 获取缩放后的图像实际显示区域
                pixmap = self.image_label.pixmap()
                label_width = self.image_label.width()
                label_height = self.image_label.height()
                pixmap_width = pixmap.width()
                pixmap_height = pixmap.height()
                
                # 计算偏移量（图像在QLabel中的起始位置）
                offset_x = (label_width - pixmap_width) // 2
                offset_y = (label_height - pixmap_height) // 2
                
                # 转换为图像坐标（避免越界）
                x1 = max(0, min(self.original_image.shape[1], (self.start_point.x() - offset_x) * self.original_image.shape[1] / pixmap_width))
                y1 = max(0, min(self.original_image.shape[0], (self.start_point.y() - offset_y) * self.original_image.shape[0] / pixmap_height))
                x2 = max(0, min(self.original_image.shape[1], (end_point.x() - offset_x) * self.original_image.shape[1] / pixmap_width))
                y2 = max(0, min(self.original_image.shape[0], (end_point.y() - offset_y) * self.original_image.shape[0] / pixmap_height))
                
                self.temp_roi = (int(min(x1,x2)), int(min(y1,y2)), int(max(x1,x2)), int(max(y1,y2)))
                self.display_image(self.original_image)  # 触发重绘
    
    def mouse_release(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            if self.temp_roi:  # 确保有临时ROI
                x1, y1, x2, y2 = self.temp_roi
                if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:  # 检查ROI有效性
                    self.rois.append((x1, y1, x2, y2))  # 保存到列表
                    print(f"ROI保存成功: {self.rois[-1]}")  # 调试输出
                    self.statusBar().showMessage(f"已添加ROI，当前有 {len(self.rois)} 个ROI")
            self.temp_roi = None  # 清除临时ROI
            self.display_image(self.original_image)  # 刷新界面
    
    def add_roi(self):
        if self.temp_roi:
            self.rois.append(self.temp_roi)
            self.temp_roi = None
            self.display_image(self.original_image)
            self.statusBar().showMessage(f"已添加ROI，当前有 {len(self.rois)} 个ROI")
    
    def clear_rois(self):
        self.rois = []
        self.temp_roi = None
        self.roi_foregrounds = []
        if hasattr(self, 'original_image'):
            self.display_image(self.original_image)
        self.statusBar().showMessage("已清除所有ROI")
    
    def rotate_image_with_padding(self, image, angle):
        """
        旋转图像，保持所有内容可见，使用透明背景填充
        """
        if angle == 0:
            return image
            
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        
        # 计算旋转矩阵
        M = cv2.getRotationMatrix2D(center, -angle, 1.0)  # 修正：直接使用角度，不取负值
        
        # 计算旋转后的边界框
        cos = abs(M[0, 0])
        sin = abs(M[0, 1])
        new_w = int(h * sin + w * cos)
        new_h = int(h * cos + w * sin)
        
        # 调整旋转矩阵以保持图像居中
        M[0, 2] += (new_w / 2) - center[0]
        M[1, 2] += (new_h / 2) - center[1]
        
        # 根据图像通道数设置边界值
        if image.shape[2] == 4:  # RGBA图像
            border_value = (0, 0, 0, 0)  # 透明
        else:  # RGB图像
            border_value = (255, 255, 255)  # 白色
            
        # 应用旋转
        rotated = cv2.warpAffine(image, M, (new_w, new_h), 
                                flags=cv2.INTER_LINEAR, 
                                borderValue=border_value)
        
        return rotated
    
    def get_obb_corners(self, center_x, center_y, width, height, angle_deg):
        """
        计算有向边界框(OBB)的四个角点坐标
        返回格式符合YOLO OBB要求: 左上, 右上, 右下, 左下 (顺时针)
        """
        # 转换为弧度
        angle_rad = math.radians(angle_deg)
        
        # 计算半宽和半高
        half_w = width / 2.0
        half_h = height / 2.0
        
        # 定义四个角点相对于中心的坐标 (未旋转前)
        # 顺序: 左上, 右上, 右下, 左下 (顺时针)
        corners = [
            (-half_w, -half_h),  # 左上
            (half_w, -half_h),   # 右上  
            (half_w, half_h),    # 右下
            (-half_w, half_h)    # 左下
        ]
        
        # 旋转变换矩阵
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        # 应用旋转并转换到世界坐标系
        rotated_corners = []
        for x, y in corners:
            # 应用旋转变换
            rotated_x = x * cos_a - y * sin_a + center_x
            rotated_y = x * sin_a + y * cos_a + center_y
            rotated_corners.append((rotated_x, rotated_y))
        
        return rotated_corners
    

    def paste_images(self, keep_foreground=False):
        if not self.rois:
            QMessageBox.warning(self, "警告", "请先添加至少一个ROI区域")
            return

        if not all(self.foreground_folders.values()):
            QMessageBox.warning(self, "警告", "请先设置所有前景文件夹")
            return

        self.modified_image = self.original_image.copy()
        self.pasted_labels = []

        # 如果不是保持前景，则重新随机选择前景图片
        if not keep_foreground or len(self.roi_foregrounds) != len(self.rois):
            self.roi_foregrounds = []
            for roi in self.rois:
                class_id = self.class_combo.currentIndex()
                foreground_folder = self.foreground_folders[class_id]
                foreground_files = [f for f in os.listdir(foreground_folder)
                                    if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if not foreground_files:
                    self.roi_foregrounds.append(None)
                else:
                    idx = self.fg_indices[class_id] % len(foreground_files)
                    foreground_path = os.path.join(foreground_folder, foreground_files[idx])
                    self.fg_indices[class_id] += 1  # 顺序递增
                    self.roi_foregrounds.append(foreground_path)

        for idx, roi in enumerate(self.rois):
            x1, y1, x2, y2 = roi
            roi_width, roi_height = x2 - x1, y2 - y1

            class_id = self.class_combo.currentIndex()
            foreground_path = self.roi_foregrounds[idx]
            if not foreground_path or not os.path.exists(foreground_path):
                continue
                
            # 读取原始前景图像
            original_foreground = cv2.imread(foreground_path, cv2.IMREAD_UNCHANGED)
            if original_foreground is None:
                continue
                
            # 获取滑块的旋转角度
            angle = self.rotate_slider.value()
            
            # 获取原始前景图像尺寸和宽高比
            orig_h, orig_w = original_foreground.shape[:2]
            original_aspect_ratio = orig_w / orig_h

            # 旋转前景图像（用于实际贴图）
            if angle != 0:
                rotated_foreground = self.rotate_image_with_padding(original_foreground, angle)
            else:
                rotated_foreground = original_foreground

            # 计算旋转后图像的缩放和贴图参数
            fg_height, fg_width = rotated_foreground.shape[:2]
            aspect_ratio = fg_width / fg_height

            # 计算旋转后图像的缩放尺寸（用于实际贴图）
            if roi_width / roi_height > aspect_ratio:
                new_height = roi_height
                new_width = int(new_height * aspect_ratio)
            else:
                new_width = roi_width
                new_height = int(new_width / aspect_ratio)

            # 处理透明通道和创建掩码
            if rotated_foreground.shape[2] == 4:  # RGBA图像
                bgr_fg = rotated_foreground[:, :, :3]
                alpha = rotated_foreground[:, :, 3]
                resized_fg = cv2.resize(bgr_fg, (new_width, new_height))
                mask = cv2.resize(alpha, (new_width, new_height))
            else:  # RGB图像
                resized_fg = cv2.resize(rotated_foreground, (new_width, new_height))
                # 创建基于白色的掩码
                lower_white = np.array([240, 240, 240], dtype=np.uint8)
                upper_white = np.array([255, 255, 255], dtype=np.uint8)
                white_mask = cv2.inRange(resized_fg, lower_white, upper_white)
                mask = 255 * np.ones(resized_fg.shape[:2], np.uint8)
                mask[white_mask == 255] = 0

            # 计算居中位置
            center_x = x1 + roi_width // 2
            center_y = y1 + roi_height // 2
            x_offset = center_x - new_width // 2
            y_offset = center_y - new_height // 2

            # 确保不超出图像边界
            x_offset = max(0, min(x_offset, self.modified_image.shape[1] - new_width))
            y_offset = max(0, min(y_offset, self.modified_image.shape[0] - new_height))

            try:
                # 获取ROI区域
                roi_img = self.modified_image[y_offset:y_offset+new_height, x_offset:x_offset+new_width].copy()
                
                # 应用alpha融合
                alpha_mask = mask.astype(float) / 255.0
                if len(alpha_mask.shape) == 2:
                    alpha_mask = alpha_mask[..., np.newaxis]
                
                # 融合图像
                blended = roi_img * (1 - alpha_mask) + resized_fg * alpha_mask
                self.modified_image[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = blended.astype(np.uint8)

                # === 关键修复：基于实际贴图区域计算OBB ===
                # 计算实际贴图区域的中心点
                actual_center_x = x_offset + new_width / 2
                actual_center_y = y_offset + new_height / 2
                
                # === 重新计算OBB尺寸：基于原始图像在贴图区域中的实际占用 ===
                # 计算原始图像在旋转后贴图中的实际占用尺寸
                
                # 方法：计算缩放比例
                # 旋转后的图像被缩放到 new_width x new_height
                # 需要找出原始内容在其中的实际尺寸
                
                # 计算旋转引起的尺寸变化
                angle_rad = math.radians(angle)
                cos_a = abs(math.cos(angle_rad))
                sin_a = abs(math.sin(angle_rad))
                
                # 原始图像旋转后的边界框尺寸
                rotated_bound_w = orig_w * cos_a + orig_h * sin_a
                rotated_bound_h = orig_w * sin_a + orig_h * cos_a
                
                # 计算从旋转边界框到实际贴图尺寸的缩放比例
                if rotated_bound_w > 0 and rotated_bound_h > 0:
                    scale_x = new_width / rotated_bound_w
                    scale_y = new_height / rotated_bound_h
                    # 使用较小的缩放比例保持宽高比
                    scale = min(scale_x, scale_y)
                    
                    # 计算原始对象在贴图中的实际尺寸
                    obb_width = orig_w * scale
                    obb_height = orig_h * scale
                else:
                    # 降级方案：直接使用ROI尺寸按原始宽高比
                    if roi_width / roi_height > original_aspect_ratio:
                        obb_height = roi_height
                        obb_width = obb_height * original_aspect_ratio
                    else:
                        obb_width = roi_width
                        obb_height = obb_width / original_aspect_ratio
                
                # 获取OBB角点
                corners = self.get_obb_corners(actual_center_x, actual_center_y, 
                                            obb_width, obb_height, angle)
                
                # 转换为归一化坐标并确保在[0,1]范围内
                img_height, img_width = self.modified_image.shape[:2]
                normalized_corners = []
                for x, y in corners:
                    norm_x = max(0.0, min(1.0, x / img_width))
                    norm_y = max(0.0, min(1.0, y / img_height))
                    normalized_corners.extend([norm_x, norm_y])
                
                # 保存YOLO OBB格式标签: class_id x1 y1 x2 y2 x3 y3 x4 y4
                self.pasted_labels.append([class_id] + normalized_corners)
                
                print(f"贴图成功 - ROI: {roi}")
                print(f"原始对象尺寸: {orig_w}x{orig_h}")
                print(f"旋转后边界框: {rotated_bound_w:.1f}x{rotated_bound_h:.1f}")
                print(f"实际贴图尺寸: {new_width}x{new_height}")
                print(f"计算得出的OBB尺寸: {obb_width:.1f}x{obb_height:.1f}")
                print(f"缩放比例: {scale:.3f}")
                print(f"OBB中心: ({actual_center_x:.1f}, {actual_center_y:.1f}), 角度: {angle}°")

            except Exception as e:
                print(f"贴图失败: {str(e)}")
                QMessageBox.warning(self, "错误", f"贴图失败: {str(e)}")
                continue

        self.display_image(self.modified_image)
        self.statusBar().showMessage("贴图完成")
    
    def save_result(self):
        if not hasattr(self, 'modified_image') or not self.output_folder:
            QMessageBox.warning(self, "警告", "请先完成贴图并设置输出文件夹")
            return
        
        # 生成唯一文件名
        base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_image_path = os.path.join(self.output_folder, "gen_photos", "images", f"{base_name}_{timestamp}_aug.jpg")
        output_label_path = os.path.join(self.output_folder, "gen_photos", "labels", f"{base_name}_{timestamp}_aug.txt")
        
        # 保存图像
        cv2.imwrite(output_image_path, self.modified_image)
        
        # 保存YOLO OBB格式标签
        with open(output_label_path, 'w') as f:
            for label in self.pasted_labels:
                # 格式: class_id x1 y1 x2 y2 x3 y3 x4 y4
                line = f"{label[0]}"
                for coord in label[1:]:
                    line += f" {coord:.6f}"
                f.write(line + "\n")
        
        print(f"保存标签: {self.pasted_labels}")
        self.statusBar().showMessage(f"结果已保存到 {output_image_path}")
    
    def next_image(self):
        if self.image_paths:
            self.current_image_index += 1
            if self.current_image_index >= len(self.image_paths):
                self.current_image_index = 0
                QMessageBox.information(self, "完成", "已处理完所有图片，将从头开始")
            self.load_current_image()

    def prev_image(self):
        if self.image_paths:
            self.current_image_index -= 1
            if self.current_image_index < 0:
                self.current_image_index = len(self.image_paths) - 1
                QMessageBox.information(self, "提示", "已到第一张，将跳转到最后一张")
            self.load_current_image()
    
    def resizeEvent(self, event):
        if hasattr(self, 'original_image'):
            self.display_image(self.original_image)
        super().resizeEvent(event)

if __name__ == "__main__":
    app = QApplication([])
    window = ImagePasteApp()
    window.show()
    app.exec_()