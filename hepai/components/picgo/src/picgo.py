import subprocess
import os
from colorama import init, Fore, Style

image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg'}

class Picgo:
    def __init__(self):
        pass
    
    def upload(self, image_path):
        print(Fore.YELLOW +"[Picgo img_path:]" + Style.RESET_ALL, image_path)
        
        if not isinstance(image_path, str) or not image_path.strip():
            return f"Not A Valid Path: {image_path}"

        # 检查路径是否存在
        if not os.path.exists(image_path):
            return f"Not Exists: {image_path}"
        
        # 检查是否为文件（即路径存在且是一个文件）
        if not os.path.isfile(image_path):
            return f"Not A File: {image_path}" 
        
        _, image_path_is_img = os.path.splitext(image_path)
        image_path_is_img = image_path_is_img.lower()
    
        # 检查文件扩展名是否在图片格式列表中
        if not image_path_is_img in image_extensions:
            return f"Not A Valid Image File: {image_path}"  
        
        result = subprocess.run(
            ['picgo', 'upload', image_path],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Error uploading image: {result.stderr}")
            return None
        # 提取输出中的URL信息
        output = result.stdout.strip()
        
        uploaded_urls = output.split('\n')
        if uploaded_urls:
            return uploaded_urls[-1] # 返回最后一行，假设它是URL
        else:
            return None
        
        # except Exception as e:
        # print(f"An exception occurred: {e}")