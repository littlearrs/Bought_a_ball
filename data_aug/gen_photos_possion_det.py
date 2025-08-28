
#  这个脚本有曝光

import os
# os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.dirname(PyQt5.__file__)
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

class ImagePasteApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图像贴图工具 - 泊松融合")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化变量
        self.image_folder = ""
        self.current_image_path = ""
        self.current_image_index = 0
        self.image_paths = []
        self.foreground_folders = {
            0: "",  # 映射到2 well
            1: ""   # 映射到3 no_well
        }
        self.rois = []  # 存储用户划定的ROI区域 (x1, y1, x2, y2)
        self.drawing = False
        self.start_point = QPoint()
        self.temp_roi = None
        self.output_folder = ""
        
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
        
        self.btn_load_foreground0 = QPushButton("加载前景文件夹")
        self.btn_load_foreground0.clicked.connect(lambda: self.load_foreground_folder(0))
        
        self.btn_load_foreground1 = QPushButton("加载前景文件夹")
        self.btn_load_foreground1.clicked.connect(lambda: self.load_foreground_folder(1))
        
        self.btn_set_output = QPushButton("设置输出文件夹")
        self.btn_set_output.clicked.connect(self.set_output_folder)
        
        self.class_combo = QComboBox()
        self.class_combo.addItems(["类别0", "类别1"])

        self.class_combo = QComboBox()
        self.class_combo.addItems(["类别0", "类别1"])
        
        
        self.btn_add_roi = QPushButton("添加ROI")
        self.btn_add_roi.clicked.connect(self.add_roi)
        
        self.btn_clear_rois = QPushButton("清除所有ROI")
        self.btn_clear_rois.clicked.connect(self.clear_rois)
        
        self.btn_paste = QPushButton("贴图")
        self.btn_paste.clicked.connect(self.paste_images)
        
        self.btn_save = QPushButton("保存")
        self.btn_save.clicked.connect(self.save_result)
        
        self.btn_next = QPushButton("下一张")
        self.btn_next.clicked.connect(self.next_image)
        
        # 添加到控制面板
        control_layout.addWidget(self.btn_load_folder)
        control_layout.addWidget(self.btn_load_foreground0)
        control_layout.addWidget(self.btn_load_foreground1)
        control_layout.addWidget(self.btn_set_output)
        control_layout.addWidget(self.class_combo)
        control_layout.addWidget(self.btn_add_roi)
        control_layout.addWidget(self.btn_clear_rois)
        control_layout.addWidget(self.btn_paste)
        control_layout.addWidget(self.btn_save)
        control_layout.addWidget(self.btn_next)
        
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
            self.current_image_index = 0
            if self.image_paths:
                self.load_current_image()
                self.statusBar().showMessage(f"已加载 {len(self.image_paths)} 张图片")
            else:
                self.statusBar().showMessage("文件夹中没有找到图片")
    
    def load_foreground_folder(self, class_id):
        folder = QFileDialog.getExistingDirectory(self, f"选择类别{class_id}前景文件夹")
        if folder:
            self.foreground_folders[class_id] = folder
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
            print("Mouse pressed!")
    
    def mouse_move(self, event):
        if self.drawing:
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
                x1 = max(0, (self.start_point.x() - offset_x) * self.original_image.shape[1] / pixmap_width)
                y1 = max(0, (self.start_point.y() - offset_y) * self.original_image.shape[0] / pixmap_height)
                x2 = max(0, (end_point.x() - offset_x) * self.original_image.shape[1] / pixmap_width)
                y2 = max(0, (end_point.y() - offset_y) * self.original_image.shape[0] / pixmap_height)
                # print(x1, y1, x2, y2)
                self.temp_roi = (int(x1), int(y1), int(x2), int(y2))
                self.display_image(self.original_image)  # 触发重绘
    
    def mouse_release(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            if self.temp_roi:  # 确保有临时ROI
                x1, y1, x2, y2 = self.temp_roi
                if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:  # 检查ROI有效性
                    self.rois.append((x1, y1, x2, y2))  # 保存到列表
                    print(f"ROI保存成功: {self.rois[-1]}")  # 调试输出
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
        self.display_image(self.original_image)
        self.statusBar().showMessage("已清除所有ROI")
    
    def paste_images(self):
        if not self.rois:
            QMessageBox.warning(self, "警告", "请先添加至少一个ROI区域")
            return
        
        if not all(self.foreground_folders.values()):
            QMessageBox.warning(self, "警告", "请先设置所有前景文件夹")
            return
        
        # 复制原始图像
        self.modified_image = self.original_image.copy()
        self.pasted_labels = []  # 存储贴图的标签信息
        
        # # 定义combo index -> YOLO class_id映射
        # combo_to_class_id = {0: 2, 1: 3}

        for roi in self.rois:
            x1, y1, x2, y2 = roi
            width, height = x2 - x1, y2 - y1
            
            # 获取选择的类别
            class_id = self.class_combo.currentIndex()
            # class_id = combo_to_class_id[combo_index]  # 映射到实际类别ID
            foreground_folder = self.foreground_folders[class_id]
            
            # 从前景文件夹随机选择一张图片
            foreground_files = [f for f in os.listdir(foreground_folder) 
                              if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if not foreground_files:
                QMessageBox.warning(self, "警告", f"类别{class_id}前景文件夹中没有图片")
                continue
            
            foreground_path = os.path.join(foreground_folder, random.choice(foreground_files))
            foreground = cv2.imread(foreground_path)
            
            if foreground is None:
                continue
            
            # 调整前景大小以适应ROI
            fg_height, fg_width = foreground.shape[:2]
            aspect_ratio = fg_width / fg_height
            
            # 保持宽高比调整大小
            if width/height > aspect_ratio:
                # 以高度为准
                new_height = height
                new_width = int(new_height * aspect_ratio)
            else:
                # 以宽度为准
                new_width = width
                new_height = int(new_width / aspect_ratio)
            
            # 调整前景大小
            resized_fg = cv2.resize(foreground, (new_width, new_height))
            
            # 计算中心位置
            center_x = x1 + width // 2
            center_y = y1 + height // 2
            x_offset = center_x - new_width // 2
            y_offset = center_y - new_height // 2
            
            # 确保不超出图像边界
            x_offset = max(0, x_offset)
            y_offset = max(0, y_offset)
            if x_offset + new_width > self.modified_image.shape[1]:
                x_offset = self.modified_image.shape[1] - new_width
            if y_offset + new_height > self.modified_image.shape[0]:
                y_offset = self.modified_image.shape[0] - new_height
            
            # 创建掩码
            mask = 255 * np.ones(resized_fg.shape, resized_fg.dtype)
            
            # 泊松融合
            try:
                self.modified_image = cv2.seamlessClone(
                    resized_fg, self.modified_image, mask, 
                    (center_x, center_y), cv2.NORMAL_CLONE
                )
                
                # 记录标签信息 (YOLO格式: class_id x_center y_center width height)
                img_height, img_width = self.modified_image.shape[:2]
                x_center = (x_offset + new_width/2) / img_width
                y_center = (y_offset + new_height/2) / img_height
                width_norm = new_width / img_width
                height_norm = new_height / img_height
                
                self.pasted_labels.append((class_id, x_center, y_center, width_norm, height_norm))
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"泊松融合失败: {str(e)}")
                continue
        
        self.display_image(self.modified_image)
        self.statusBar().showMessage("贴图完成")
    
    def save_result(self):
        if not hasattr(self, 'modified_image') or not self.output_folder:
            QMessageBox.warning(self, "警告", "请先完成贴图并设置输出文件夹")
            return
        
        # 生成唯一文件名
        base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
        # output_image_path = os.path.join(self.output_folder, "gen_photos", "images", f"{base_name}_aug.jpg")
        # output_label_path = os.path.join(self.output_folder, "gen_photos", "labels", f"{base_name}_aug.txt")

        # 无目标的原始图片贴图
        output_image_path = os.path.join(self.output_folder, "gen_photos", "images", f"{base_name}.jpg")
        output_label_path = os.path.join(self.output_folder, "gen_photos", "labels", f"{base_name}.txt")
        
        # 保存图像
        cv2.imwrite(output_image_path, self.modified_image)
        
        # 保存标签
        with open(output_label_path, 'w') as f:
            for label in self.pasted_labels:
                f.write(f"{label[0]} {label[1]:.6f} {label[2]:.6f} {label[3]:.6f} {label[4]:.6f}\n")
        
        self.statusBar().showMessage(f"结果已保存到 {output_image_path}")
    
    def next_image(self):
        if self.image_paths:
            self.current_image_index += 1
            if self.current_image_index >= len(self.image_paths):
                self.current_image_index = 0
                QMessageBox.information(self, "完成", "已处理完所有图片，将从头开始")
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