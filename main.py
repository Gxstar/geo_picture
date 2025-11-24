import webview
import json
import os
from datetime import datetime
from pathlib import Path

class GeoPictureApp:
    def __init__(self):
        self.data_file = Path("geo_data.json")
        self.images_dir = Path("images")
        self.images_dir.mkdir(exist_ok=True)
        
        # 加载现有数据
        self.geo_data = self.load_geo_data()
    
    def load_geo_data(self):
        """加载地理数据"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载数据失败: {e}")
                return {"images": [], "metadata": {"created": datetime.now().isoformat()}}
        else:
            return {"images": [], "metadata": {"created": datetime.now().isoformat()}}
    
    def save_geo_data(self, data):
        """保存地理数据"""
        try:
            # 更新元数据
            data["metadata"] = {
                "last_modified": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 更新内存中的数据
            self.geo_data = data
            
            return {"success": True, "message": "数据保存成功"}
        except Exception as e:
            return {"success": False, "message": f"数据保存失败: {str(e)}"}
    
    def save_geo_data_api(self, geo_data):
        """API: 保存地理数据"""
        print(f"接收到地理数据: {len(geo_data.get('images', []))} 张图片")
        return self.save_geo_data(geo_data)
    
    def load_images_api(self):
        """API: 加载图片数据"""
        return {
            "success": True,
            "data": self.geo_data.get("images", []),
            "total": len(self.geo_data.get("images", []))
        }
    
    def export_data_api(self, format_type="json"):
        """API: 导出数据"""
        try:
            if format_type == "json":
                export_file = f"geo_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(self.geo_data, f, ensure_ascii=False, indent=2)
                
                return {
                    "success": True,
                    "message": f"数据已导出到 {export_file}",
                    "file": export_file
                }
            else:
                return {"success": False, "message": "不支持的导出格式"}
        except Exception as e:
            return {"success": False, "message": f"导出失败: {str(e)}"}
    
    def clear_data_api(self):
        """API: 清除所有数据"""
        try:
            self.geo_data = {"images": [], "metadata": {"created": datetime.now().isoformat()}}
            
            if self.data_file.exists():
                self.data_file.unlink()
            
            return {"success": True, "message": "所有数据已清除"}
        except Exception as e:
            return {"success": False, "message": f"清除失败: {str(e)}"}
    
    def get_status_api(self):
        """API: 获取应用状态"""
        return {
            "images_count": len(self.geo_data.get("images", [])),
            "last_modified": self.geo_data.get("metadata", {}).get("last_modified", "从未修改"),
            "data_file": str(self.data_file.absolute()) if self.data_file.exists() else None,
            "app_version": "1.0"
        }

def main():
    # 创建应用实例
    app = GeoPictureApp()
    
    # 创建API对象
    api = {
        "save_geo_data": app.save_geo_data_api,
        "load_images": app.load_images_api,
        "export_data": app.export_data_api,
        "clear_data": app.clear_data_api,
        "get_status": app.get_status_api
    }
    
    # 创建窗口
    window = webview.create_window(
        '图片地理位置信息编辑工具',
        'frontend/index.html',
        width=1200,
        height=800,
        resizable=True,
        text_select=False,
        js_api=api
    )
    
    # 窗口事件处理
    def on_loaded():
        print("应用已加载")
        # 可以在这里执行初始化操作
    
    window.events.loaded += on_loaded
    
    # 启动应用
    webview.start(debug=True)

if __name__ == "__main__":
    main()