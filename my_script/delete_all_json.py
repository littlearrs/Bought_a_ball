import os

def delete_json_files(folder_path):
    # 遍历文件夹下的所有文件
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".json"):  # 判断是否为 json 文件
            file_path = os.path.join(folder_path, filename)
            try:
                os.remove(file_path)  # 删除文件
                print(f"已删除: {file_path}")
            except Exception as e:
                print(f"删除失败: {file_path}, 错误信息: {e}")

# 使用示例
folder = r"D:\artifical\Baggages\airport_xray\images\train"  # 修改为目标文件夹路径
delete_json_files(folder)
