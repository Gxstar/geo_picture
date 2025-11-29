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
    
    def _select_files(self, allow_multiple=False):
        """打开文件选择对话框，选择图片文件"""
        try:
            import webview
            
            # 获取当前窗口对象
            window = webview.active_window()
            
            # 打开文件选择对话框 - pywebview 6.0 API
            file_paths = window.create_file_dialog(
                webview.FileDialog.OPEN,
                file_types=('Image Files (*.jpg;*.jpeg;*.avif;*.heic;*.heif)', ),
                allow_multiple=allow_multiple
            )
            
            if file_paths and len(file_paths) > 0:
                result = {'success': True}
                if allow_multiple:
                    result['file_paths'] = file_paths
                else:
                    result['file_path'] = file_paths[0]
                return result
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
    
    def select_file(self):
        """打开文件选择对话框，选择单个图片文件"""
        return self._select_files(allow_multiple=False)
    
    def select_multiple_files(self):
        """打开文件选择对话框，选择多个图片文件"""
        return self._select_files(allow_multiple=True)
    
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
    
    def get_settings(self):
        """获取当前API设置"""
        try:
            import os
            
            # 从环境变量获取当前设置
            api_id = os.environ.get('API_ID', '')
            api_key = os.environ.get('API_KEY', '')
            
            return {
                'success': True,
                'api_id': api_id,
                'api_key': api_key
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_settings(self, api_id, api_key):
        """保存API设置到.env文件"""
        try:
            import os
            
            # 获取.env文件路径
            env_path = os.path.join(os.path.dirname(__file__), '.env')
            
            # 读取现有.env文件内容
            env_content = ''
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    env_content = f.read()
            
            # 更新API_ID和API_KEY
            import re
            
            # 替换或添加API_ID
            if re.search(r'^API_ID=.*$', env_content, re.MULTILINE):
                env_content = re.sub(r'^API_ID=.*$', f'API_ID={api_id}', env_content, flags=re.MULTILINE)
            else:
                env_content += f'\nAPI_ID={api_id}'
            
            # 替换或添加API_KEY
            if re.search(r'^API_KEY=.*$', env_content, re.MULTILINE):
                env_content = re.sub(r'^API_KEY=.*$', f'API_KEY={api_key}', env_content, flags=re.MULTILINE)
            else:
                env_content += f'\nAPI_KEY={api_key}'
            
            # 保存到.env文件
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            # 更新环境变量
            os.environ['API_ID'] = api_id
            os.environ['API_KEY'] = api_key
            
            return {
                'success': True
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
