import os
import cv2 as cv
 
 
def split_string_2_imgname_class_x1_y1_x2_y2(str):
    str=str.replace("\n","").split(" ")
    return str
 
def get_imgs_h_w(img_name):
    img_dir=r"D:\artifical\OPIXray\test\test_image"  #修改为自己的图片路径目录
    img_path=os.path.join(img_dir,img_name)
    image = cv.imread(img_path)
    size = image.shape
    w = size[1]  # 宽度
    h = size[0]  # 高度
    return size
 
 
def voc_to_yolo(size, box):
    temp=[]
    dw = 1./float(size[1])
    dh = 1./float(size[0])
    box[0],box[1],box[2],box[3]=float(box[0]),float(box[1]),float(box[2]),float(box[3])
 
    x = (box[0] + box[2])/2.0
    y = (box[1] + box[3])/2.0
    w = box[2] - box[0]
    h = box[3] - box[1]
    x = x*dw
    w = w*dw
    y = y*dh
    h = h*dh
    temp.append(x)
    temp.append(y)
    temp.append(w)
    temp.append(h)
    return temp
 
def get_box(temp):
    box=[]
    for i in range(2,6):
        box.append(temp[i])
    return box
 
def get_class_index(class_name):
#OPIXray字典如下
    class_dict={'Straight_Knife': '0', 'Folding_Knife': '1', 'Scissor': '2', 'Utility_Knife': '3', 'Multi-tool_Knife': '4'}
 
 
#Hixray字典如下    class_dict={'Mobile_Phone': 0, 'Laptop': 1, 'Portable_Charger_2': 2, 'Portable_Charger_1': 3, 'Tablet': 4, 'Cosmetic': 5, 'Water': 6, 'Nonmetallic_Lighter': 7}
    return class_dict.get(class_name)
 
if __name__ == '__main__':
    txt_dir = r"D:\artifical\OPIXray\test\test_annotation"  #修改为自己的原始标签路径
    img_dir = r"D:\artifical\OPIXray\test\test_image"  #修改为自己的原始图片路径
    save_txt_dir = r"D:\artifical\OPIXray\test\labels"  #修改为自己的标签保存路径
    if not os.path.exists(save_txt_dir):
        os.mkdir(save_txt_dir)
 
    for txt_name in os.listdir(txt_dir):
        txt_path=os.path.join(txt_dir,txt_name)
        save_txt_path=os.path.join(save_txt_dir,txt_name)
        f = open(txt_path, 'r')
        contents=f.readlines()
        for annotation in contents:
            temp=split_string_2_imgname_class_x1_y1_x2_y2(annotation)
            size=get_imgs_h_w(temp[0])
            class_index=get_class_index(temp[1])
            box=get_box(temp)
            xywh=voc_to_yolo(size,box)
            f_save=open(save_txt_path,'a')
 
            f_save.write(class_index)
            f_save.write(" ")
            f_save.write(str(xywh[0]))
            f_save.write(" ")
            f_save.write(str(xywh[1]))
            f_save.write(" ")
            f_save.write(str(xywh[2]))
            f_save.write(" ")
            f_save.write(str(xywh[3]))
            f_save.write(" ")
            f_save.write("\n")
        f_save.close()
        f.close()