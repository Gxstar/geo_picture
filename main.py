import webview
from geo_picture.geo_processor import GeoProcessor
import os

class Api:
    """提供给前端调用的API类"""
    
    def get_gps_info(self, file_path):
        """获取图片的GPS信息"""
        try:
            gps_info = GeoProcessor.get_gps_info(file_path)
            if gps_info:
                return {
                    'success': True,
                    'latitude': gps_info[0],
                    'longitude': gps_info[1]
                }
            else:
                return {
                    'success': True,
                    'latitude': None,
                    'longitude': None
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def select_file(self):
        """打开文件选择对话框，选择单个图片文件"""
        try:
            # 使用pywebview的window.create_file_dialog方法选择文件
            # 注意：在pywebview中，create_file_dialog是window对象的方法
            # 我们需要获取当前窗口对象
            import tkinter as tk
            from tkinter import filedialog
            
            # 创建一个隐藏的Tkinter根窗口
            root = tk.Tk()
            root.withdraw()
            
            # 打开文件选择对话框
            file_path = filedialog.askopenfilename(
                title="选择图片文件",
                filetypes=[("Image Files", "*.jpg;*.jpeg;*.avif;*.heic;*.heif")]
            )
            
            # 销毁Tkinter根窗口
            root.destroy()
            
            if file_path:
                return {
                    'success': True,
                    'file_path': file_path
                }
            else:
                return {
                    'success': False,
                    'error': '未选择文件'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def select_multiple_files(self):
        """打开文件选择对话框，选择多个图片文件"""
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            # 创建一个隐藏的Tkinter根窗口
            root = tk.Tk()
            root.withdraw()
            
            # 打开文件选择对话框，支持多选
            file_paths = filedialog.askopenfilenames(
                title="选择图片文件",
                filetypes=[("Image Files", "*.jpg;*.jpeg;*.avif;*.heic;*.heif")]
            )
            
            # 销毁Tkinter根窗口
            root.destroy()
            
            if file_paths:
                return {
                    'success': True,
                    'file_paths': list(file_paths)
                }
            else:
                return {
                    'success': False,
                    'error': '未选择文件'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_image_data(self, file_path):
        """读取图片数据并转换为base64格式"""
        try:
            import base64
            from PIL import Image
            import io
            
            # 打开图片
            image = Image.open(file_path)
            
            # 将图片转换为base64格式
            buffered = io.BytesIO()
            image.save(buffered, format=image.format or 'JPEG')
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # 返回base64数据
            return {
                'success': True,
                'image_data': f'data:image/{image.format.lower() or "jpeg"};base64,{img_str}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_image(self, file_path, latitude, longitude, overwrite=False):
        """处理单个图片，添加GPS信息"""
        try:
            # 调用GeoProcessor处理图片
            success = GeoProcessor.process_image(file_path, latitude, longitude, overwrite=overwrite)
            
            if success:
                # 生成输出文件路径
                if overwrite:
                    output_path = file_path
                else:
                    dirname, basename = os.path.split(file_path)
                    name, ext = os.path.splitext(basename)
                    output_path = os.path.join(dirname, f"{name}_geo{ext}")
                
                return {
                    'success': True,
                    'output_path': output_path
                }
            else:
                return {
                    'success': False,
                    'error': '处理图片失败'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_multiple_images(self, file_paths, latitude, longitude, overwrite=False):
        """批量处理图片，添加GPS信息"""
        try:
            results = []
            for file_path in file_paths:
                # 调用process_image处理单个图片
                result = self.process_image(file_path, latitude, longitude, overwrite)
                results.append({
                    'file_path': file_path,
                    'success': result['success'],
                    'output_path': result.get('output_path'),
                    'error': result.get('error')
                })
            
            return {
                'success': True,
                'results': results
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

def main():
    """应用入口"""
    # 创建API实例
    api = Api()
    
    # 获取当前目录下的index.html路径
    html_path = os.path.join(os.path.dirname(__file__), 'index.html')
    
    # 创建webview窗口
    window = webview.create_window(
        title='图片GPS信息添加工具',
        url=html_path,
        width=1200,
        height=980,
        resizable=True,
        js_api=api
    )
    
    # 启动应用
    webview.start(debug=True)

if __name__ == '__main__':
    main()
