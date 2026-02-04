import os
import math
import random
import time
import cv2
import numpy as np
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QFileDialog,
    QComboBox, QMessageBox, QListWidget, QListWidgetItem,
    QSlider, QShortcut
)
from PyQt5.QtGui import (
    QPixmap, QImage, QPainter, QPen, QColor, QKeySequence
)
from PyQt5.QtCore import Qt, QPoint


class ImagePasteApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图像贴图标注工具 - AABB")
        self.setGeometry(100, 100, 1200, 820)
        self.setFocusPolicy(Qt.StrongFocus)

        # ====== 数据状态 ======
        self.image_folder = ""
        self.current_image_path = ""
        self.current_image_index = 0
        self.image_paths = []

        # 两类：0=well, 1=no_well
        self.class_names = {0: "excavator", 1: "drilling_rig"}
        self.foreground_folders = {0: "", 1: ""}
        self.fg_indices = {0: 0, 1: 0}   # 每类顺序取图索引

        # # 单类，1=drilling_rig
        # self.class_names = {1: "drilling_rig"}
        # self.foreground_folders = {1: ""}
        # self.fg_indices = {1: 0}   # 每类顺序取图索引

        # ROI（轴对齐矩形）
        self.rois = []                # [(x1,y1,x2,y2), ...]
        self.roi_classes = []         # 与 rois 对齐
        self.roi_foregrounds = []     # 每 ROI 的前景 png 路径或 None
        self.roi_angles = []          # 每 ROI 的旋转角度（度，正=逆时针）
        self.selected_roi_idx = -1

        # 贴图后可视化的标签框（青色虚线）
        self.pasted_labels = []           # [(cls, xc, yc, w, h) 归一化]
        self.pasted_label_pixels = []     # [(x1,y1,x2,y2) 像素]

        # 交互状态
        self.drawing = False
        self.moving_roi = False
        self.move_start_xy = (0, 0)
        self.roi_move_origin = (0, 0, 0, 0)

        self.resizing_roi = False
        self.resize_handle = None         # 'nw','n','ne','e','se','s','sw','w'
        self.keep_aspect_on_resize = False
        self.handle_size = 10             # 把手像素尺寸
        self.min_roi_size = 10            # ROI 最小宽高

        self.start_point = QPoint()
        self.temp_roi = None

        self.output_folder = ""
        self.original_image = None
        self.modified_image = None

        # 掩膜阈值（处理 PNG 半透明边缘时更稳；>阈值视为可见）
        self.alpha_threshold = 10  # 0~255

        # UI
        self.init_ui()
        self.init_shortcuts()

    # ======================= UI =======================
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)

        # 图像显示
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: black;")
        self.image_label.mousePressEvent = self.mouse_press
        self.image_label.mouseMoveEvent = self.mouse_move
        self.image_label.mouseReleaseEvent = self.mouse_release

        # 顶部控制面板
        top_panel = QWidget()
        top_layout = QHBoxLayout()
        top_panel.setLayout(top_layout)

        self.btn_load_folder = QPushButton("加载图片文件夹")
        self.btn_load_folder.clicked.connect(self.load_image_folder)

        self.btn_load_fg_well = QPushButton("加载前景文件夹1")
        self.btn_load_fg_well.clicked.connect(lambda: self.load_foreground_folder(0))

        self.btn_load_fg_nowell = QPushButton("加载前景文件夹2")
        self.btn_load_fg_nowell.clicked.connect(lambda: self.load_foreground_folder(1))

        self.btn_set_output = QPushButton("设置输出文件夹")
        self.btn_set_output.clicked.connect(self.set_output_folder)

        self.class_combo = QComboBox()
        self.class_combo.addItems(["前景1(类0)", "前景2(类1)"])
        

        self.btn_clear_rois = QPushButton("清除所有ROI")
        self.btn_clear_rois.clicked.connect(self.clear_rois)

        self.btn_paste = QPushButton("贴图刷新")
        self.btn_paste.clicked.connect(lambda: self.paste_images(keep_assigned=True))

        self.btn_save = QPushButton("保存当前结果")
        self.btn_save.clicked.connect(self.save_result)

        self.btn_prev = QPushButton("上一张图片")
        self.btn_prev.clicked.connect(self.prev_image)
        self.btn_next = QPushButton("下一张图片")
        self.btn_next.clicked.connect(self.next_image)

        top_layout.addWidget(self.btn_load_folder)
        top_layout.addWidget(self.btn_load_fg_well)
        top_layout.addWidget(self.btn_load_fg_nowell)
        top_layout.addWidget(self.btn_set_output)
        top_layout.addWidget(self.class_combo)
        top_layout.addWidget(self.btn_clear_rois)
        top_layout.addWidget(self.btn_paste)
        top_layout.addWidget(self.btn_save)
        top_layout.addWidget(self.btn_prev)
        top_layout.addWidget(self.btn_next)

        # ROI 管理面板
        roi_panel = QWidget()
        roi_layout = QHBoxLayout()
        roi_panel.setLayout(roi_layout)

        # 左：旋转（只作用于选中的 ROI）
        rot_block = QWidget()
        rot_layout = QVBoxLayout()
        rot_block.setLayout(rot_layout)

        self.rotate_label = QLabel("旋转角度: 0°（作用于选中ROI，正=逆时针）")
        self.rotate_slider = QSlider(Qt.Horizontal)
        self.rotate_slider.setMinimum(0)
        self.rotate_slider.setMaximum(359)
        self.rotate_slider.setValue(0)
        self.rotate_slider.setTickInterval(1)
        self.rotate_slider.valueChanged.connect(self.on_rotate_slider_changed)

        rot_layout.addWidget(self.rotate_label)
        rot_layout.addWidget(self.rotate_slider)

        # 中：ROI 列表
        center_block = QWidget()
        center_layout = QVBoxLayout()
        center_block.setLayout(center_layout)

        self.roi_list = QListWidget()
        self.roi_list.setFocusPolicy(Qt.ClickFocus)  # 避免方向键被列表抢走
        self.roi_list.currentRowChanged.connect(self.on_roi_selected)

        center_layout.addWidget(QLabel("ROI 列表（右键选中；左键拖动内部可移动；拖把手可缩放，Shift保比例）"))
        center_layout.addWidget(self.roi_list)

        # 右：选中 ROI 的操作
        right_block = QWidget()
        right_layout = QVBoxLayout()
        right_block.setLayout(right_layout)

        self.btn_roi_pick_fg = QPushButton("为选中ROI选择前景图（文件选择）")
        self.btn_roi_pick_fg.clicked.connect(self.pick_foreground_for_selected_roi)

        self.btn_roi_clear_fg = QPushButton("清除选中ROI前景图")
        self.btn_roi_clear_fg.clicked.connect(self.clear_foreground_for_selected_roi)

        self.btn_roi_apply_class = QPushButton("将上方类别应用到选中ROI")
        self.btn_roi_apply_class.clicked.connect(self.apply_class_to_selected_roi)

        self.btn_roi_delete = QPushButton("删除选中ROI")
        self.btn_roi_delete.clicked.connect(self.delete_selected_roi)

        self.btn_roi_prev_fg = QPushButton("上一张前景（选中ROI）")
        self.btn_roi_prev_fg.clicked.connect(lambda: self.switch_fg_for_selected_roi(step=-1))

        self.btn_roi_next_fg = QPushButton("下一张前景（选中ROI）")
        self.btn_roi_next_fg.clicked.connect(lambda: self.switch_fg_for_selected_roi(step=+1))

        right_layout.addWidget(self.btn_roi_pick_fg)
        right_layout.addWidget(self.btn_roi_clear_fg)
        right_layout.addWidget(self.btn_roi_apply_class)
        right_layout.addWidget(self.btn_roi_delete)
        right_layout.addWidget(self.btn_roi_prev_fg)
        right_layout.addWidget(self.btn_roi_next_fg)
        right_layout.addStretch(1)

        roi_layout.addWidget(rot_block, 2)
        roi_layout.addWidget(center_block, 5)
        roi_layout.addWidget(right_block, 3)

        # 装配
        main_layout.addWidget(self.image_label, stretch=8)
        main_layout.addWidget(top_panel, stretch=0)
        main_layout.addWidget(roi_panel, stretch=0)

        self.statusBar().showMessage(
            "左键拖拽新建ROI；右键选中ROI；选中后左键拖动可移动；拖拽8个把手缩放（Shift保比例）；←/→切前景，↑/↓旋转；+/- 等比缩放。"
        )

    def init_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_Right), self, activated=lambda: self.switch_fg_for_selected_roi(+1))
        QShortcut(QKeySequence(Qt.Key_Left), self, activated=lambda: self.switch_fg_for_selected_roi(-1))
        QShortcut(QKeySequence(Qt.Key_Up), self, activated=self.rotate_selected_plus)
        QShortcut(QKeySequence(Qt.Key_Down), self, activated=self.rotate_selected_minus)
        # 等比缩放（以中心）
        QShortcut(QKeySequence("+"), self, activated=lambda: self.scale_selected_roi(1.10))
        QShortcut(QKeySequence("="), self, activated=lambda: self.scale_selected_roi(1.10))  # 备用
        QShortcut(QKeySequence("-"), self, activated=lambda: self.scale_selected_roi(0.90))

    # =================== 基本加载/显示 ===================
    def load_image_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if folder:
            self.image_folder = folder
            self.image_paths = [os.path.join(folder, f) for f in os.listdir(folder)
                                if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            # random.shuffle(self.image_paths)

            self.image_paths.sort()  # 保持顺序一致
            self.current_image_index = 0
            if self.image_paths:
                self.load_current_image()
                self.statusBar().showMessage(f"已加载 {len(self.image_paths)} 张图片")
            else:
                self.statusBar().showMessage("文件夹中没有找到图片")

    def set_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_folder = folder
            Path(os.path.join(folder, "gen_photos", "images")).mkdir(parents=True, exist_ok=True)
            Path(os.path.join(folder, "gen_photos", "labels")).mkdir(parents=True, exist_ok=True)
            self.statusBar().showMessage(f"输出文件夹已设置: {folder}")

    def load_foreground_folder(self, class_id):
        folder = QFileDialog.getExistingDirectory(self, f"选择 {self.class_names[class_id]} 前景文件夹")
        if folder:
            self.foreground_folders[class_id] = folder
            self.fg_indices[class_id] = 0
            self.statusBar().showMessage(f"{self.class_names[class_id]} 前景文件夹已设置: {folder}")

    def load_current_image(self):
        if 0 <= self.current_image_index < len(self.image_paths):
            # self.image_paths.sort()  # 保持顺序一致
            self.current_image_path = self.image_paths[self.current_image_index]
            self.original_image = cv2.imread(self.current_image_path, cv2.IMREAD_COLOR)
            if self.original_image is None:
                QMessageBox.warning(self, "错误", f"无法读取：{self.current_image_path}")
                return
            self.modified_image = self.original_image.copy()
            # 清空 ROI / 标签
            self.rois.clear()
            self.roi_classes.clear()
            self.roi_foregrounds.clear()
            self.roi_angles.clear()
            self.selected_roi_idx = -1
            self.pasted_labels = []
            self.pasted_label_pixels = []
            self.update_roi_list()
            self.display_image(self.modified_image)
            self.statusBar().showMessage(
                f"当前图片: {os.path.basename(self.current_image_path)} "
                f"({self.current_image_index+1}/{len(self.image_paths)})"
            )

    # =================== 绘制（AABB + 把手 + 标签框） ===================
    def display_image(self, image):
        if image is None:
            return
        h, w = image.shape[:2]
        q_img = QImage(image.data, w, h, 3*w, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        painter = QPainter(pixmap)

        # 画 ROI（绿/红）
        for i, (x1, y1, x2, y2) in enumerate(self.rois):
            color = QColor(255, 0, 0) if i == self.selected_roi_idx else QColor(0, 255, 0)
            painter.setPen(QPen(color, 2))
            painter.drawRect(int(x1), int(y1), int(x2 - x1), int(y2 - y1))

        # 画 label 的实际 AABB（青色虚线）
        pen = QPen(QColor(0, 255, 255), 2, Qt.DashLine)
        painter.setPen(pen)
        for (lx1, ly1, lx2, ly2) in self.pasted_label_pixels:
            painter.drawRect(int(lx1), int(ly1), int(lx2 - lx1), int(ly2 - ly1))

        # 选中 ROI 的把手（橙色）
        if 0 <= self.selected_roi_idx < len(self.rois):
            x1, y1, x2, y2 = self._normalize_roi(self.rois[self.selected_roi_idx])
            hs = self.handle_size
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 165, 0))
            for _, (cx, cy) in self._get_handle_centers((x1, y1, x2, y2)).items():
                painter.drawRect(int(cx - hs/2), int(cy - hs/2), hs, hs)

        # 临时 ROI（黄虚线）
        if self.temp_roi:
            painter.setPen(QPen(QColor(255, 255, 0), 2, Qt.DashLine))
            x1, y1, x2, y2 = self.temp_roi
            painter.drawRect(int(x1), int(y1), int(x2 - x1), int(y2 - y1))

        painter.end()
        scaled = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)

    # =================== ROI/把手辅助 ===================
    def _normalize_roi(self, roi):
        x1, y1, x2, y2 = roi
        if x1 > x2: x1, x2 = x2, x1
        if y1 > y2: y1, y2 = y2, y1
        return int(x1), int(y1), int(x2), int(y2)

    def _clamp_roi_to_image(self, roi):
        x1, y1, x2, y2 = self._normalize_roi(roi)
        H, W = self.original_image.shape[:2]
        x1 = max(0, min(W-1, x1)); x2 = max(0, min(W-1, x2))
        y1 = max(0, min(H-1, y1)); y2 = max(0, min(H-1, y2))
        return self._normalize_roi((x1, y1, x2, y2))

    def _get_handle_centers(self, roi):
        x1, y1, x2, y2 = self._normalize_roi(roi)
        xm = (x1 + x2) // 2
        ym = (y1 + y2) // 2
        return {
            'nw': (x1, y1), 'n': (xm, y1), 'ne': (x2, y1),
            'e':  (x2, ym), 'se': (x2, y2), 's': (xm, y2),
            'sw': (x1, y2), 'w':  (x1, ym)
        }

    def _hit_test_handle(self, x, y, roi):
        hs = self.handle_size
        half = hs / 2.0
        for name, (cx, cy) in self._get_handle_centers(roi).items():
            if (abs(x - cx) <= half) and (abs(y - cy) <= half):
                return name
        return None

    def _update_cursor_shape(self, x, y):
        if not (0 <= self.selected_roi_idx < len(self.rois)):
            self.image_label.setCursor(Qt.ArrowCursor); return
        roi = self.rois[self.selected_roi_idx]
        handle = self._hit_test_handle(x, y, roi)
        cursor = Qt.ArrowCursor
        if handle in ('n', 's'):
            cursor = Qt.SizeVerCursor
        elif handle in ('e', 'w'):
            cursor = Qt.SizeHorCursor
        elif handle in ('nw', 'se'):
            cursor = Qt.SizeFDiagCursor
        elif handle in ('ne', 'sw'):
            cursor = Qt.SizeBDiagCursor
        self.image_label.setCursor(cursor)

    def _resize_from_handle(self, roi0, handle, x, y, keep_aspect=False):
        x1, y1, x2, y2 = self._normalize_roi(roi0)
        w0 = max(1, x2 - x1); h0 = max(1, y2 - y1)
        aspect = w0 / h0

        if handle == 'nw':
            x1, y1 = x, y
        elif handle == 'n':
            y1 = y
        elif handle == 'ne':
            x2, y1 = x, y
        elif handle == 'e':
            x2 = x
        elif handle == 'se':
            x2, y2 = x, y
        elif handle == 's':
            y2 = y
        elif handle == 'sw':
            x1, y2 = x, y
        elif handle == 'w':
            x1 = x

        if keep_aspect:
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            ww = abs(x2 - x1); hh = abs(y2 - y1)
            if hh == 0: hh = 1
            if ww / hh > aspect:
                ww = hh * aspect
            else:
                hh = ww / aspect
            x1 = int(cx - ww/2); x2 = int(cx + ww/2)
            y1 = int(cy - hh/2); y2 = int(cy + hh/2)

        if abs(x2 - x1) < self.min_roi_size:
            cx = (x1 + x2)//2
            x1 = cx - self.min_roi_size//2
            x2 = cx + self.min_roi_size//2
        if abs(y2 - y1) < self.min_roi_size:
            cy = (y1 + y2)//2
            y1 = cy - self.min_roi_size//2
            y2 = cy + self.min_roi_size//2

        return self._clamp_roi_to_image((x1, y1, x2, y2))

    # =================== 坐标映射 ===================
    def _label_to_image_xy(self, pos: QPoint):
        if not self.image_label.pixmap():
            return 0, 0
        pixmap = self.image_label.pixmap()
        Lw, Lh = self.image_label.width(), self.image_label.height()
        Pw, Ph = pixmap.width(), pixmap.height()
        off_x = max(0, (Lw - Pw) // 2)
        off_y = max(0, (Lh - Ph) // 2)
        px = pos.x() - off_x
        py = pos.y() - off_y
        px = np.clip(px, 0, Pw - 1)
        py = np.clip(py, 0, Ph - 1)
        H, W = self.original_image.shape[:2]
        x = int(px * W / Pw)
        y = int(py * H / Ph)
        return x, y

    # =================== 鼠标事件 ===================
    def mouse_press(self, event):
        img_x, img_y = self._label_to_image_xy(event.pos())
        if event.button() == Qt.LeftButton:
            # 1) 把手命中 -> 缩放模式
            if 0 <= self.selected_roi_idx < len(self.rois):
                roi = self.rois[self.selected_roi_idx]
                handle = self._hit_test_handle(img_x, img_y, roi)
                if handle is not None:
                    self.resizing_roi = True
                    self.resize_handle = handle
                    self.keep_aspect_on_resize = bool(event.modifiers() & Qt.ShiftModifier)
                    self.roi_move_origin = roi  # 复用存原始 ROI
                    return

            # 2) ROI 内部 -> 移动模式
            if 0 <= self.selected_roi_idx < len(self.rois):
                x1, y1, x2, y2 = self.rois[self.selected_roi_idx]
                if x1 <= img_x <= x2 and y1 <= img_y <= y2:
                    self.moving_roi = True
                    self.move_start_xy = (img_x, img_y)
                    self.roi_move_origin = (x1, y1, x2, y2)
                    return

            # 3) 否则开始画新 ROI
            self.drawing = True
            self.start_point = event.pos()
            self.temp_roi = None

        elif event.button() == Qt.RightButton:
            # 右键：命中测试（轴对齐）
            idx = self._hit_test_roi_axis(img_x, img_y)
            if idx != -1:
                self.selected_roi_idx = idx
                self.rotate_slider.setValue(self.roi_angles[idx])
                self.rotate_label.setText(f"旋转角度: {self.roi_angles[idx]}°（作用于选中ROI，正=逆时针）")
                self.update_roi_list()
                self.roi_list.setCurrentRow(self.selected_roi_idx)
                self.display_image(self.modified_image)

    def mouse_move(self, event):
        img_x, img_y = self._label_to_image_xy(event.pos())

        # 缩放
        if self.resizing_roi and (0 <= self.selected_roi_idx < len(self.rois)):
            new_roi = self._resize_from_handle(
                self.roi_move_origin, self.resize_handle, img_x, img_y,
                keep_aspect=self.keep_aspect_on_resize
            )
            self.rois[self.selected_roi_idx] = new_roi
            self.redraw_single_roi(self.selected_roi_idx)
            return

        # 移动
        if self.moving_roi and (0 <= self.selected_roi_idx < len(self.rois)):
            sx, sy = self.move_start_xy
            dx, dy = (img_x - sx), (img_y - sy)
            x1, y1, x2, y2 = self.roi_move_origin
            w = x2 - x1; h = y2 - y1
            nx1, ny1 = x1 + dx, y1 + dy
            nx2, ny2 = nx1 + w, ny1 + h
            self.rois[self.selected_roi_idx] = self._clamp_roi_to_image((nx1, ny1, nx2, ny2))
            self.redraw_single_roi(self.selected_roi_idx)
            return

        # 画新框
        if self.drawing:
            end = event.pos()
            x1, y1 = self._label_to_image_xy(self.start_point)
            x2, y2 = self._label_to_image_xy(end)
            self.temp_roi = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            self.display_image(self.modified_image)
            return

        # 更新光标形状
        self._update_cursor_shape(img_x, img_y)

    def mouse_release(self, event):
        if event.button() == Qt.LeftButton:
            if self.resizing_roi:
                self.resizing_roi = False
                self.resize_handle = None
                self.display_image(self.modified_image)
                return

            if self.moving_roi:
                self.moving_roi = False
                self.display_image(self.modified_image)
                return

            if self.drawing:
                self.drawing = False
                if self.temp_roi:
                    x1, y1, x2, y2 = self.temp_roi
                    if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
                        self.rois.append((int(x1), int(y1), int(x2), int(y2)))
                        cls_id = self.class_combo.currentIndex()
                        self.roi_classes.append(cls_id)
                        self.roi_foregrounds.append(None)
                        self.roi_angles.append(0)
                        self.selected_roi_idx = len(self.rois) - 1
                        self.rotate_slider.setValue(0)
                        self.update_roi_list()
                        self.roi_list.setCurrentRow(self.selected_roi_idx)
                        self.paste_images(keep_assigned=True)
                self.temp_roi = None
                self.display_image(self.modified_image)

    def _hit_test_roi_axis(self, x, y):
        for i in reversed(range(len(self.rois))):  # 后加的优先
            x1, y1, x2, y2 = self.rois[i]
            if x1 <= x <= x2 and y1 <= y <= y2:
                return i
        return -1

    # =================== ROI 列表及操作 ===================
    def update_roi_list(self):
        current = self.selected_roi_idx
        self.roi_list.clear()
        for i, (x1, y1, x2, y2) in enumerate(self.rois):
            cls_id = self.roi_classes[i]
            fg = self.roi_foregrounds[i]
            ang = self.roi_angles[i]
            fg_short = "未指定" if not fg else os.path.basename(fg)
            item_str = f"#{i} [{self.class_names[cls_id]}] ({x1},{y1})→({x2},{y2}) | 图:{fg_short} | 角:{ang}°"
            self.roi_list.addItem(QListWidgetItem(item_str))
        if 0 <= current < len(self.rois):
            self.roi_list.setCurrentRow(current)
            self.selected_roi_idx = current
        else:
            self.roi_list.setCurrentRow(-1)

    def on_roi_selected(self, row):
        self.selected_roi_idx = row
        if 0 <= row < len(self.rois):
            self.rotate_slider.setValue(self.roi_angles[row])
            self.rotate_label.setText(f"旋转角度: {self.roi_angles[row]}°（作用于选中ROI，正=逆时针）")
        self.display_image(self.modified_image)

    def pick_foreground_for_selected_roi(self):
        if not (0 <= self.selected_roi_idx < len(self.rois)):
            QMessageBox.information(self, "提示", "请先选中一个 ROI（右键图像或列表中选择）。")
            return
        img_path, _ = QFileDialog.getOpenFileName(
            self, "选择前景图片（png/jpg/jpeg）", "",
            "Images (*.png *.jpg *.jpeg)"
        )
        if img_path:
            self.roi_foregrounds[self.selected_roi_idx] = img_path
            self.update_roi_list()
            self.roi_list.setCurrentRow(self.selected_roi_idx)
            self.redraw_single_roi(self.selected_roi_idx)

    def clear_foreground_for_selected_roi(self):
        if not (0 <= self.selected_roi_idx < len(self.rois)):
            return
        self.roi_foregrounds[self.selected_roi_idx] = None
        self.update_roi_list()
        self.roi_list.setCurrentRow(self.selected_roi_idx)
        self.redraw_single_roi(self.selected_roi_idx)

    def apply_class_to_selected_roi(self):
        if not (0 <= self.selected_roi_idx < len(self.rois)):
            return
        cls_id = self.class_combo.currentIndex()
        self.roi_classes[self.selected_roi_idx] = cls_id
        self.update_roi_list()
        self.roi_list.setCurrentRow(self.selected_roi_idx)
        self.redraw_single_roi(self.selected_roi_idx)

    def delete_selected_roi(self):
        if not (0 <= self.selected_roi_idx < len(self.rois)):
            return
        i = self.selected_roi_idx
        for lst in (self.rois, self.roi_classes, self.roi_foregrounds, self.roi_angles):
            del lst[i]
        if self.rois:
            self.selected_roi_idx = min(i, len(self.rois) - 1)
        else:
            self.selected_roi_idx = -1
        self.update_roi_list()
        self.redraw_all_rois()

    def clear_rois(self):
        self.rois.clear()
        self.roi_classes.clear()
        self.roi_foregrounds.clear()
        self.roi_angles.clear()
        self.selected_roi_idx = -1
        self.pasted_labels = []
        self.pasted_label_pixels = []
        if self.original_image is not None:
            self.modified_image = self.original_image.copy()
            self.display_image(self.modified_image)
        self.update_roi_list()
        self.statusBar().showMessage("已清除所有ROI")

    # =================== 旋转 & 缩放（键盘） ===================
    def on_rotate_slider_changed(self, v):
        self.rotate_label.setText(f"旋转角度: {v}°（作用于选中ROI，正=逆时针）")
        if 0 <= self.selected_roi_idx < len(self.rois):
            self.roi_angles[self.selected_roi_idx] = int(v)
            self.redraw_single_roi(self.selected_roi_idx)

    def rotate_selected_plus(self):
        if 0 <= self.selected_roi_idx < len(self.rois):
            v = (self.roi_angles[self.selected_roi_idx] + 5) % 360
            self.rotate_slider.setValue(v)

    def rotate_selected_minus(self):
        if 0 <= self.selected_roi_idx < len(self.rois):
            v = (self.roi_angles[self.selected_roi_idx] - 5) % 360
            self.rotate_slider.setValue(v)

    def scale_selected_roi(self, factor: float):
        """以中心等比缩放选中ROI；factor>1放大，<1缩小"""
        if not (0 <= self.selected_roi_idx < len(self.rois)): return
        x1, y1, x2, y2 = self._normalize_roi(self.rois[self.selected_roi_idx])
        cx = (x1 + x2) / 2.0; cy = (y1 + y2) / 2.0
        w = max(self.min_roi_size, int((x2 - x1) * factor))
        h = max(self.min_roi_size, int((y2 - y1) * factor))
        nx1 = int(cx - w/2); ny1 = int(cy - h/2)
        nx2 = nx1 + w;       ny2 = ny1 + h
        self.rois[self.selected_roi_idx] = self._clamp_roi_to_image((nx1, ny1, nx2, ny2))
        self.redraw_single_roi(self.selected_roi_idx)

    # =================== 贴图核心（AABB 来自 mask 的紧致包围框） ===================
    def paste_images(self, keep_assigned=True):
        if self.original_image is None:
            QMessageBox.warning(self, "警告", "请先加载图片。")
            return
        if not self.rois:
            QMessageBox.warning(self, "警告", "请先添加至少一个 ROI（左键拉框）。")
            return
        if not (self.foreground_folders[0] and self.foreground_folders[1]):
            QMessageBox.warning(self, "警告", "请先设置前景文件夹。")
            return

        base = self.original_image.copy()
        saved_labels = []
        saved_pixels = []
        H, W = base.shape[:2]

        for idx, (x1, y1, x2, y2) in enumerate(self.rois):
            width, height = x2 - x1, y2 - y1
            if width <= 0 or height <= 0:
                continue

            cls_id = self.roi_classes[idx]
            fg_path = self.roi_foregrounds[idx]

            # 未指定前景则顺序取
            if (not keep_assigned) or (fg_path is None):
                folder = self.foreground_folders[cls_id]
                files = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                files.sort()
                if not files:
                    continue
                choose_idx = self.fg_indices[cls_id] % len(files)
                fg_path = os.path.join(folder, files[choose_idx])
                self.fg_indices[cls_id] += 1
                self.roi_foregrounds[idx] = fg_path

            if not os.path.exists(fg_path):
                continue

            # 读取前景（保留 alpha）
            fg = cv2.imread(fg_path, cv2.IMREAD_UNCHANGED)
            if fg is None:
                continue

            # 旋转（正=逆时针）
            angle = int(self.roi_angles[idx]) if idx < len(self.roi_angles) else 0
            if angle != 0:
                (h, w) = fg.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                cos = abs(M[0, 0]); sin = abs(M[0, 1])
                nW = int(h * sin + w * cos)
                nH = int(h * cos + w * sin)
                M[0, 2] += (nW / 2) - center[0]
                M[1, 2] += (nH / 2) - center[1]
                border = (0, 0, 0, 0) if (fg.ndim == 3 and fg.shape[2] == 4) else (255, 255, 255)
                fg = cv2.warpAffine(fg, M, (nW, nH), flags=cv2.INTER_LINEAR, borderValue=border)

            # 缩放保持比例放入 ROI
            fg_h, fg_w = fg.shape[:2]
            aspect = fg_w / fg_h if fg_h != 0 else 1.0
            if width / height > aspect:
                new_h = height
                new_w = int(new_h * aspect)
            else:
                new_w = width
                new_h = int(new_w / aspect)

            # 分离/构造 mask
            if fg.ndim == 3 and fg.shape[2] == 4:
                bgr_fg = fg[:, :, :3]
                alpha = fg[:, :, 3]
                resized_fg = cv2.resize(bgr_fg, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                mask = cv2.resize(alpha, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                _, mask = cv2.threshold(mask, self.alpha_threshold, 255, cv2.THRESH_BINARY)
            else:
                resized_fg = cv2.resize(fg, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                # “抠白”为透明
                lower_white = np.array([240, 240, 240], dtype=np.uint8)
                upper_white = np.array([255, 255, 255], dtype=np.uint8)
                white_mask = cv2.inRange(resized_fg, lower_white, upper_white)
                mask = np.full(resized_fg.shape[:2], 255, np.uint8)
                mask[white_mask == 255] = 0

            # 放置位置（居中）
            cx = x1 + width // 2
            cy = y1 + height // 2
            x_off = max(0, cx - new_w // 2)
            y_off = max(0, cy - new_h // 2)
            if x_off + new_w > W: x_off = W - new_w
            if y_off + new_h > H: y_off = H - new_h

            # 合成（alpha 混合）
            roi_img = base[y_off:y_off + new_h, x_off:x_off + new_w]
            alpha_mask = (mask.astype(float) / 255.0)
            if resized_fg.ndim == 3:
                for c in range(3):
                    roi_img[..., c] = roi_img[..., c] * (1 - alpha_mask) + resized_fg[..., c] * alpha_mask
            else:
                roi_img[...] = roi_img[...] * (1 - alpha_mask) + resized_fg[...] * alpha_mask
            base[y_off:y_off + new_h, x_off:x_off + new_w] = roi_img

            # === 核心：用 mask 的紧致包围框 生成 AABB 标签 ===
            coords = cv2.findNonZero(mask)
            if coords is not None:
                mx, my, mw, mh = cv2.boundingRect(coords)
            else:
                mx, my, mw, mh = 0, 0, new_w, new_h  # 极端退化

            px1 = x_off + mx
            py1 = y_off + my
            px2 = px1 + mw
            py2 = py1 + mh
            saved_pixels.append((px1, py1, px2, py2))

            xc = (px1 + px2) / 2.0 / W
            yc = (py1 + py2) / 2.0 / H
            wn = (px2 - px1) / W
            hn = (py2 - py1) / H
            saved_labels.append((cls_id, xc, yc, wn, hn))

        self.modified_image = base
        self.pasted_labels = saved_labels
        self.pasted_label_pixels = saved_pixels

        # 维持选中
        self.update_roi_list()
        if 0 <= self.selected_roi_idx < len(self.rois):
            self.roi_list.setCurrentRow(self.selected_roi_idx)
        self.display_image(self.modified_image)
        self.statusBar().showMessage("贴图完成（label=AABB，来自前景可见区域；青色虚线为实际标签框）")

    def redraw_all_rois(self):
        self.paste_images(keep_assigned=True)

    def redraw_single_roi(self, idx):
        self.paste_images(keep_assigned=True)

    # =================== 保存 / 导航 ===================
    def save_result(self):
        if self.modified_image is None or not self.output_folder:
            QMessageBox.warning(self, "警告", "请先完成贴图并设置输出文件夹")
            return
        base = os.path.splitext(os.path.basename(self.current_image_path))[0]
        ts = time.strftime("%Y%m%d_%H%M%S")
        # out_img = os.path.join(self.output_folder, "gen_photos", "images", f"{base}_{ts}_aug.jpg")
        # out_lbl = os.path.join(self.output_folder, "gen_photos", "labels", f"{base}_{ts}_aug.txt")
        out_img = os.path.join(self.output_folder, "gen_photos", "images", f"{base}.jpg")
        out_lbl = os.path.join(self.output_folder, "gen_photos", "labels", f"{base}.txt")
        cv2.imwrite(out_img, self.modified_image)
        with open(out_lbl, 'w') as f:
            for c, xc, yc, w, h in self.pasted_labels:
                f.write(f"{c} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")
        self.statusBar().showMessage(f"结果已保存到 {out_img}")

    def next_image(self):
        if not self.image_paths:
            return
        self.current_image_index += 1
        if self.current_image_index >= len(self.image_paths):
            self.current_image_index = 0
            QMessageBox.information(self, "完成", "已处理完所有图片，将从头开始")
        self.load_current_image()

    def prev_image(self):
        if not self.image_paths:
            return
        self.current_image_index -= 1
        if self.current_image_index < 0:
            self.current_image_index = len(self.image_paths) - 1
            QMessageBox.information(self, "提示", "已到第一张，将跳转到最后一张")
        self.load_current_image()

    # =================== 前景切换 ===================
    def switch_fg_for_selected_roi(self, step=+1):
        if not (0 <= self.selected_roi_idx < len(self.rois)):
            QMessageBox.information(self, "提示", "请先选中一个 ROI（右键图像或在列表中选中）。")
            return
        i = self.selected_roi_idx
        cls_id = self.roi_classes[i]
        folder = self.foreground_folders[cls_id]
        if not folder:
            QMessageBox.warning(self, "警告", f"请先设置 {self.class_names[cls_id]} 的前景文件夹")
            return
        files = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        files.sort()
        if not files:
            QMessageBox.warning(self, "警告", f"{self.class_names[cls_id]} 文件夹内没有图片")
            return

        cur = self.roi_foregrounds[i]
        if cur and os.path.dirname(cur) == folder and os.path.basename(cur) in files:
            idx = files.index(os.path.basename(cur))
        else:
            idx = self.fg_indices[cls_id] % len(files)

        idx = (idx + step) % len(files)
        new_path = os.path.join(folder, files[idx])
        self.roi_foregrounds[i] = new_path
        self.fg_indices[cls_id] = (idx + 1) % len(files)

        self.update_roi_list()
        self.roi_list.setCurrentRow(self.selected_roi_idx)
        self.redraw_single_roi(i)


if __name__ == "__main__":
    app = QApplication([])
    w = ImagePasteApp()
    w.show()
    app.exec_()
