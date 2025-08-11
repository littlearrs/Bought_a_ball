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
from PyQt5.QtWidgets import QSlider
import time

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
            0: "",  # cone
            1: "",  # box 
            2: "",  # bucket 
            3: ""   # rock
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
        
        self.btn_load_foreground0 = QPushButton("加载cone前景文件夹")
        self.btn_load_foreground0.clicked.connect(lambda: self.load_foreground_folder(0))

        self.btn_load_foreground1 = QPushButton("加载box前景文件夹")
        self.btn_load_foreground1.clicked.connect(lambda: self.load_foreground_folder(1))

        self.btn_load_foreground2 = QPushButton("加载bucket前景文件夹")
        self.btn_load_foreground2.clicked.connect(lambda: self.load_foreground_folder(2))

        self.btn_load_foreground3 = QPushButton("加载rock前景文件夹")
        self.btn_load_foreground3.clicked.connect(lambda: self.load_foreground_folder(3))
        
        self.btn_set_output = QPushButton("设置输出文件夹")
        self.btn_set_output.clicked.connect(self.set_output_folder)
        
        self.class_combo = QComboBox()
        self.class_combo.addItems(["cone (类别0)",
                                "box (类别1)",
                                "bucket (类别2)",
                                "rock (类别3)"])
        
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
        #self.rotate_slider.valueChanged.connect(lambda v: self.rotate_label.setText(f"旋转角度: {v}°"))
        self.rotate_slider.valueChanged.connect(self.on_rotate_slider_changed)
        # 添加到控制面板
        control_layout.addWidget(self.rotate_label)
        control_layout.addWidget(self.rotate_slider)
                
        # 添加到控制面板
        control_layout.addWidget(self.btn_load_folder)
        control_layout.addWidget(self.btn_load_foreground0)
        control_layout.addWidget(self.btn_load_foreground1)
        control_layout.addWidget(self.btn_load_foreground2)
        control_layout.addWidget(self.btn_load_foreground3)
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
    
    # def load_foreground_folder(self, class_id):
    #     folder = QFileDialog.getExistingDirectory(self, f"选择类别{class_id}前景文件夹")
    #     if folder:
    #         self.foreground_folders[class_id] = folder
    #         self.statusBar().showMessage(f"类别{class_id}前景文件夹已设置: {folder}")

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
            width, height = x2 - x1, y2 - y1

            class_id = self.class_combo.currentIndex()
            foreground_path = self.roi_foregrounds[idx]
            if not foreground_path or not os.path.exists(foreground_path):
                continue
            foreground = cv2.imread(foreground_path, cv2.IMREAD_UNCHANGED)
            if foreground is None:
                continue

            # 获取滑块的旋转角度
            angle = self.rotate_slider.value()
            if angle != 0:
                (h, w) = foreground.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                cos = np.abs(M[0, 0])
                sin = np.abs(M[0, 1])
                nW = int((h * sin) + (w * cos))
                nH = int((h * cos) + (w * sin))
                M[0, 2] += (nW / 2) - center[0]
                M[1, 2] += (nH / 2) - center[1]
                border = (0,0,0,0) if foreground.shape[2]==4 else (255,255,255)
                foreground = cv2.warpAffine(foreground, M, (nW, nH), flags=cv2.INTER_LINEAR, borderValue=border)

            fg_height, fg_width = foreground.shape[:2]
            aspect_ratio = fg_width / fg_height

            if width/height > aspect_ratio:
                new_height = height
                new_width = int(new_height * aspect_ratio)
            else:
                new_width = width
                new_height = int(new_width / aspect_ratio)

            if foreground.shape[2] == 4:
                bgr_fg = foreground[:, :, :3]
                alpha = foreground[:, :, 3]
                mask = alpha
                resized_fg = cv2.resize(bgr_fg, (new_width, new_height))
                mask = cv2.resize(mask, (new_width, new_height))
            else:
                resized_fg = cv2.resize(foreground, (new_width, new_height))
                lower_white = np.array([240, 240, 240], dtype=np.uint8)
                upper_white = np.array([255, 255, 255], dtype=np.uint8)
                white_mask = cv2.inRange(resized_fg, lower_white, upper_white)
                mask = 255 * np.ones(resized_fg.shape[:2], np.uint8)
                mask[white_mask == 255] = 0

            center_x = x1 + width // 2
            center_y = y1 + height // 2
            x_offset = center_x - new_width // 2
            y_offset = center_y - new_height // 2

            x_offset = max(0, x_offset)
            y_offset = max(0, y_offset)
            if x_offset + new_width > self.modified_image.shape[1]:
                x_offset = self.modified_image.shape[1] - new_width
            if y_offset + new_height > self.modified_image.shape[0]:
                y_offset = self.modified_image.shape[0] - new_height

            try:
                roi_img = self.modified_image[y_offset:y_offset+new_height, x_offset:x_offset+new_width]
                if mask.ndim == 2:
                    alpha_mask = mask.astype(float) / 255.0
                    if resized_fg.shape[2] == 3:
                        for c in range(3):
                            roi_img[..., c] = roi_img[..., c] * (1 - alpha_mask) + resized_fg[..., c] * alpha_mask
                    else:
                        roi_img[...] = roi_img[...] * (1 - alpha_mask) + resized_fg[...] * alpha_mask
                else:
                    alpha_mask = mask[..., 0].astype(float) / 255.0
                    for c in range(3):
                        roi_img[..., c] = roi_img[..., c] * (1 - alpha_mask) + resized_fg[..., c] * alpha_mask
                self.modified_image[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = roi_img

                img_height, img_width = self.modified_image.shape[:2]
                x_center = (x_offset + new_width/2) / img_width
                y_center = (y_offset + new_height/2) / img_height
                width_norm = new_width / img_width
                height_norm = new_height / img_height

                self.pasted_labels.append((class_id, x_center, y_center, width_norm, height_norm))

            except Exception as e:
                QMessageBox.warning(self, "错误", f"普通贴图失败: {str(e)}")
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