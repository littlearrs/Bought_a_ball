import cv2
import numpy as np


# ===================== 1. 读取图像 =====================
img1_gray = cv2.imread(
    r'C:\Users\liyang01\Desktop\images_match\A\CD20251016_0047_001_x1280_y540.png',
    cv2.IMREAD_GRAYSCALE
)
img2_gray = cv2.imread(
    r'C:\Users\liyang01\Desktop\images_match\B\CD20251016_0047_001_x1280_y540.png',
    cv2.IMREAD_GRAYSCALE
)

if img1_gray is None or img2_gray is None:
    raise IOError("图像路径错误，无法读取图像")

# 转为彩色图（后面画线用）
img1_color = cv2.cvtColor(img1_gray, cv2.COLOR_GRAY2BGR)
img2_color = cv2.cvtColor(img2_gray, cv2.COLOR_GRAY2BGR)


# ===================== 2. SIFT 特征提取 =====================
sift = cv2.SIFT_create()

kp1, des1 = sift.detectAndCompute(img1_gray, None)
kp2, des2 = sift.detectAndCompute(img2_gray, None)

if des1 is None or des2 is None:
    raise RuntimeError("未检测到足够特征点")


# ===================== 3. FLANN 特征匹配 =====================
FLANN_INDEX_KDTREE = 1
index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
search_params = dict(checks=50)

flann = cv2.FlannBasedMatcher(index_params, search_params)
matches = flann.knnMatch(des1, des2, k=2)


# ===================== 4. Lowe Ratio Test =====================
good = []
ratio_thresh = 0.7

for m, n in matches:
    if m.distance < ratio_thresh * n.distance:
        good.append(m)

print(f"Good matches: {len(good)}")


# ===================== 5. 计算单应性矩阵 =====================
if len(good) >= 10:
    src_pts = np.float32(
        [kp1[m.queryIdx].pt for m in good]
    ).reshape(-1, 1, 2)

    dst_pts = np.float32(
        [kp2[m.trainIdx].pt for m in good]
    ).reshape(-1, 1, 2)

    H, mask = cv2.findHomography(
        src_pts,
        dst_pts,
        cv2.RANSAC,
        ransacReprojThreshold=5.0
    )

    if H is None:
        raise RuntimeError("Homography 计算失败")

    print("Homography Matrix:\n", H)

    # ===================== 6. 映射 img1 的四个角 =====================
    h, w = img1_gray.shape
    corners = np.float32([
        [0, 0],
        [0, h - 1],
        [w - 1, h - 1],
        [w - 1, 0]
    ]).reshape(-1, 1, 2)

    projected_corners = cv2.perspectiveTransform(corners, H)

    # 画多边形
    cv2.polylines(
        img2_color,
        [np.int32(projected_corners)],
        isClosed=True,
        color=(0, 255, 0),
        thickness=2
    )
else:
    raise RuntimeError("匹配点过少，无法计算单应性矩阵")


# ===================== 7. 显示单应性结果 =====================
while True:
    cv2.imshow("Homography Result", img2_color)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC 键退出
        break

cv2.destroyAllWindows()


# ===================== 8. 显示匹配结果 =====================
# drawMatchesKnn 需要 List[List[DMatch]]
draw_matches = [[m] for m in good[:20]]

img_matches = cv2.drawMatchesKnn(
    img1_color, kp1,
    img2_color, kp2,
    draw_matches,
    None,
    flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
)

while True:
    cv2.imshow("Feature Matches", img_matches)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()
