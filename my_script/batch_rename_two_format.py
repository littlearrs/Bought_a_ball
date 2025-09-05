import os

def batch_rename(img_dir, json_dir, mode="prefix", prefix="", suffix="", start_index=1, zfill_num=4, dry_run=False):
    """
    批量修改图片和对应json文件名
    :param img_dir: 图片文件夹路径
    :param json_dir: json文件夹路径
    :param mode: "prefix"（保留原名加前后缀） 或 "number"（按序号重命名，可带前后缀）
    :param prefix: 文件名前缀
    :param suffix: 文件名后缀
    :param start_index: 序号起始值（仅在 mode="number" 时使用）
    :param zfill_num: 序号位数，不足自动补0
    :param dry_run: True 表示只打印不改名
    """
    img_exts = [".jpg", ".png", ".jpeg", ".bmp"]

    files = sorted([f for f in os.listdir(img_dir) if os.path.splitext(f)[1].lower() in img_exts])

    for idx, filename in enumerate(files, start=start_index):
        name, ext = os.path.splitext(filename)

        old_img_path = os.path.join(img_dir, filename)
        old_json_path = os.path.join(json_dir, name + ".json")

        if not os.path.exists(old_json_path):
            print(f"⚠️ 没找到匹配的 JSON：{old_json_path}")
            continue

        if mode == "prefix":
            # 保留原文件名，加前后缀
            new_name = f"{prefix}{name}{suffix}"
        elif mode == "number":
            # 序号模式，可带前后缀
            number_part = str(idx).zfill(zfill_num)
            new_name = f"{prefix}{number_part}{suffix}"
        else:
            raise ValueError("mode 参数只能是 'prefix' 或 'number'")

        new_img_path = os.path.join(img_dir, new_name + ext)
        new_json_path = os.path.join(json_dir, new_name + ".json")

        if dry_run:
            print(f"预览: {filename} -> {os.path.basename(new_img_path)}")
            print(f"预览: {name}.json -> {os.path.basename(new_json_path)}")
        else:
            os.rename(old_img_path, new_img_path)
            os.rename(old_json_path, new_json_path)
            print(f"✅ {filename} -> {os.path.basename(new_img_path)}")
            print(f"✅ {name}.json -> {os.path.basename(new_json_path)}")


if __name__ == "__main__":
    img_dir = r"E:\object_detection_dataset\well_data\set_6_labels\images_ori"
    json_dir = r"E:\object_detection_dataset\well_data\set_6_labels\labels_json"

    # === 模式1：保留原名，加前后缀 ===
    # batch_rename(img_dir, json_dir, mode="prefix", prefix="well_", suffix="_v1")

    # === 模式2：按序号重命名，也能加前后缀 ===
    batch_rename(img_dir, json_dir, mode="number", prefix="well6_", start_index=1, zfill_num=4)
