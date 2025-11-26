import webview
from geo_picture.geo_processor import GeoProcessor
import os
from dotenv import load_dotenv
load_dotenv()  # 加载.env文件中的环境变量

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
            # 使用pywebview自带的文件选择功能
            import webview
            
            # 获取当前窗口对象
            window = webview.active_window()
            
            # 打开文件选择对话框 - pywebview 6.0 API
            file_paths = window.create_file_dialog(
                webview.FileDialog.OPEN,
                file_types=('Image Files (*.jpg;*.jpeg;*.avif;*.heic;*.heif)', ),
                allow_multiple=False
            )
            
            if file_paths and len(file_paths) > 0:
                return {
                    'success': True,
                    'file_path': file_paths[0]
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
            # 使用pywebview自带的文件选择功能，支持多选
            import webview
            
            # 获取当前窗口对象
            window = webview.active_window()
            
            # 打开文件选择对话框，支持多选 - pywebview 6.0 API
            file_paths = window.create_file_dialog(
                webview.FileDialog.OPEN,
                file_types=('Image Files (*.jpg;*.jpeg;*.avif;*.heic;*.heif)', ),
                allow_multiple=True
            )
            
            if file_paths and len(file_paths) > 0:
                return {
                    'success': True,
                    'file_paths': file_paths
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
    
    def search_address(self, address):
        """调用地址查询API获取经纬度"""
        try:
            import os
            import requests
            
            # 从环境变量获取API配置
            api_id = os.environ.get('API_ID', '')
            api_key = os.environ.get('API_KEY', '')
            
            if not api_id or not api_key:
                return {
                    'success': False,
                    'error': 'API配置未找到，请检查环境变量'
                }
            
            # 调用地址查询API
            api_url = 'https://cn.apihz.cn/api/other/jwjuhe.php'
            params = {
                'id': api_id,
                'key': api_key,
                'address': address
            }
            
            response = requests.get(api_url, params=params)
            data = response.json()
            
            if data.get('code') == 200:
                return {
                    'success': True,
                    'latitude': float(data.get('lat')),
                    'longitude': float(data.get('lng')),
                    'score': data.get('score'),
                    'level': data.get('level')
                }
            else:
                return {
                    'success': False,
                    'error': data.get('msg', '查询失败')
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
