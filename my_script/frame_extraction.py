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

    basename = os.path.splitext(os.path.basename(video_path))[0] 

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            # filename = os.path.join(output_folder, f"custom_{saved_idx:03d}.jpg")
            filename = os.path.join(output_folder, f"{basename}_{saved_idx:03d}.jpg")
            cv2.imwrite(filename, frame)
            print(f"保存帧: {filename}")
            saved_idx += 1
        frame_idx += 1

    cap.release()
    print("抽帧完成。")

if __name__ == "__main__":
    video_path = r"E:\object_detection_dataset\roadbarriers\barrier3\videos\x10.mp4"  # 输入视频文件路径
    output_folder = r"E:\object_detection_dataset\roadbarriers\barrier3\img" # 输出文件夹路径
    interval_sec = float(input("请输入抽帧间隔（秒）："))
    extract_frames(video_path, output_folder, interval_sec)


# import cv2
# import os

# def extract_frames_from_videos(video_folder, output_folder, interval_sec):
#     if not os.path.exists(output_folder):
#         os.makedirs(output_folder)

#     # 扫描文件夹下所有视频文件
#     video_ext = ('.mp4', '.avi', '.mov', '.mkv')
#     videos = [f for f in os.listdir(video_folder) if f.lower().endswith(video_ext)]

#     if not videos:
#         print("❌ 文件夹中没有找到视频")
#         return

#     for video_name in videos:
#         video_path = os.path.join(video_folder, video_name)
#         print(f"\n===== 正在处理视频：{video_name} =====")

#         cap = cv2.VideoCapture(video_path)
#         if not cap.isOpened():
#             print(f"无法打开视频: {video_name}")
#             continue

#         fps = cap.get(cv2.CAP_PROP_FPS)
#         total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#         duration = total_frames / fps
#         print(f"视频时长: {duration:.2f} 秒, 帧率: {fps:.2f}")

#         # 抽帧间隔对应的帧数
#         frame_interval = int(fps * interval_sec)
#         frame_idx = 0
#         saved_idx = 1  # ⭐ 每个视频从 1 开始编号

#         basename = os.path.splitext(video_name)[0]

#         while True:
#             ret, frame = cap.read()
#             if not ret:
#                 break

#             if frame_idx % frame_interval == 0:
#                 filename = os.path.join(output_folder, f"{basename}_{saved_idx:04d}.jpg")
#                 cv2.imwrite(filename, frame)
#                 print(f"保存帧: {filename}")
#                 saved_idx += 1

#             frame_idx += 1

#         cap.release()

#     print("\n🎉 批量抽帧完成。")


# if __name__ == "__main__":
#     video_folder = r"E:\object_detection_dataset\roadbarries\data3\videos"   # 输入视频文件夹
#     output_folder = r"E:\object_detection_dataset\roadbarries\data3\images"  # 统一输出的文件夹
#     interval_sec = float(input("请输入抽帧间隔（秒）："))
#     extract_frames_from_videos(video_folder, output_folder, interval_sec)









