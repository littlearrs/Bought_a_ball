import cv2
import os

def extract_frames(video_path, output_folder, interval_sec):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("无法打开视频文件")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    print(f"视频时长: {duration:.2f} 秒, 帧率: {fps:.2f}")

    frame_interval = int(fps * interval_sec)
    frame_idx = 0
    saved_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            filename = os.path.join(output_folder, f"frame_{saved_idx:05d}.jpg")
            cv2.imwrite(filename, frame)
            print(f"保存帧: {filename}")
            saved_idx += 1
        frame_idx += 1

    cap.release()
    print("抽帧完成。")

if __name__ == "__main__":
    video_path = r"D:\Vscode_Project\data_aug\data\demo.mp4"  # 输入视频文件路径
    output_folder = r"D:\Vscode_Project\data_aug\output" # 输出文件夹路径
    interval_sec = float(input("请输入抽帧间隔（秒）："))
    extract_frames(video_path, output_folder, interval_sec)