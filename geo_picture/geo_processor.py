from PIL import Image
import os
from typing import Tuple, Optional
import exifread
import piexif

# 注册HEIF/HEIC格式支持
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    print("HEIF/HEIC opener registered successfully")
except ImportError:
    print("pillow_heif not installed, HEIF/HEIC support disabled")
except Exception as e:
    print(f"Failed to register HEIF opener: {e}")

class GeoProcessor:
    """处理图片GPS信息的核心类"""
    
    @staticmethod
    def read_image(file_path: str) -> Optional[Image.Image]:
        """读取支持的图片格式"""
        if not file_path:
            print("Error: file_path is None")
            return None
            
        try:
            # 直接使用PIL打开，pillow_heif.register_heif_opener()已经注册了HEIF/HEIC格式支持
            # AVIF格式已被Pillow默认支持
            image = Image.open(file_path)
            return image
        except Exception as e:
            print(f"Failed to read image: {e}")
            return None
    
    @staticmethod
    def add_gps_to_image(image: Image.Image, lat: float, lon: float) -> Image.Image:
        """向图片添加GPS信息"""
        try:
            # 确保经纬度是浮点数
            lat = float(lat)
            lon = float(lon)
            
            # 使用piexif库来处理EXIF数据
            print("Using piexif to add GPS info")
            
            # 获取原始EXIF数据
            exif_dict = {}
            if 'exif' in image.info:
                try:
                    exif_dict = piexif.load(image.info['exif'])
                except Exception as e:
                    print(f"Failed to load existing EXIF: {e}")
            
            # 转换经纬度为piexif期望的格式
            def decimal_to_piexif_dms(decimal):
                """将十进制转换为piexif期望的度分秒格式"""
                degrees = int(decimal)
                minutes_decimal = (decimal - degrees) * 60
                minutes = int(minutes_decimal)
                seconds = (minutes_decimal - minutes) * 60
                
                # piexif期望的格式是 ((degrees, 1), (minutes, 1), (int(seconds * 100), 100))
                return ((degrees, 1), (minutes, 1), (int(seconds * 100), 100))
            
            # 确定方向
            lat_ref = 'N' if lat >= 0 else 'S'
            lon_ref = 'E' if lon >= 0 else 'W'
            
            # 转换为绝对值
            lat_abs = abs(lat)
            lon_abs = abs(lon)
            
            # 转换为piexif期望的度分秒格式
            lat_dms = decimal_to_piexif_dms(lat_abs)
            lon_dms = decimal_to_piexif_dms(lon_abs)
            
            print(f"GPS data: lat={lat_dms}, lat_ref={lat_ref}, lon={lon_dms}, lon_ref={lon_ref}")
            
            # 创建GPS EXIF数据
            gps_dict = {
                piexif.GPSIFD.GPSLatitudeRef: lat_ref,
                piexif.GPSIFD.GPSLatitude: lat_dms,
                piexif.GPSIFD.GPSLongitudeRef: lon_ref,
                piexif.GPSIFD.GPSLongitude: lon_dms,
                piexif.GPSIFD.GPSAltitudeRef: 0,  # 海拔参考（0=海平面以上）
                piexif.GPSIFD.GPSAltitude: (0, 1),  # 海拔
            }
            
            # 将GPS数据添加到EXIF字典
            exif_dict['GPS'] = gps_dict
            
            # 将EXIF字典转换为字节
            exif_bytes = piexif.dump(exif_dict)
            
            # 创建新的图片对象，确保EXIF数据被正确设置
            new_image = image.copy()
            new_image.info['exif'] = exif_bytes
            
            print(f"Successfully added GPS to image using piexif: lat={lat}, lon={lon}")
            return new_image
        except Exception as e:
            print(f"Failed to add GPS to image: {e}")
            import traceback
            traceback.print_exc()
            return image
    
    @staticmethod
    def save_image(image: Image.Image, input_path: str, output_path: Optional[str] = None, overwrite: bool = False) -> bool:
        """保存图片，保留原始格式
        
        Args:
            image: PIL Image对象
            input_path: 输入图片路径
            output_path: 输出图片路径，如果为None则根据overwrite参数决定
            overwrite: 是否覆盖原图，默认为False
        
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            if output_path is None:
                if overwrite:
                    # 覆盖原图
                    output_path = input_path
                else:
                    # 如果没有指定输出路径，在原文件名后添加"_geo"后缀
                    dirname, basename = os.path.split(input_path)
                    name, ext = os.path.splitext(basename)
                    output_path = os.path.join(dirname, f"{name}_geo{ext}")
            
            # 根据文件扩展名选择保存格式
            ext = os.path.splitext(output_path)[1].lower()
            
            # 获取原始图片的格式
            original_format = None
            try:
                with Image.open(input_path) as img:
                    original_format = img.format
            except Exception as e:
                print(f"Failed to get original image format: {e}")
            
            # 保存图片，确保保留EXIF数据
            save_kwargs = {}
            
            # 对于JPEG格式，确保EXIF数据被正确保存
            if ext in ['.jpg', '.jpeg']:
                if 'exif' in image.info:
                    save_kwargs['exif'] = image.info['exif']
                image.save(output_path, format='JPEG', quality=95, **save_kwargs)
            # 对于HEIC/HEIF格式
            elif ext in ['.heic', '.heif']:
                # HEIC/HEIF格式的EXIF处理可能需要特殊处理
                # 先尝试使用PIL直接保存
                try:
                    if 'exif' in image.info:
                        save_kwargs['exif'] = image.info['exif']
                    image.save(output_path, format='HEIC', **save_kwargs)
                except Exception as heic_error:
                    print(f"Failed to save HEIC with EXIF: {heic_error}")
                    # 尝试不传递EXIF数据，某些HEIC编码器可能不支持EXIF
                    image.save(output_path, format='HEIC')
            # 对于AVIF格式
            elif ext == '.avif':
                # AVIF格式的EXIF处理可能需要特殊处理
                try:
                    if 'exif' in image.info:
                        save_kwargs['exif'] = image.info['exif']
                    image.save(output_path, format='AVIF', **save_kwargs)
                except Exception as avif_error:
                    print(f"Failed to save AVIF with EXIF: {avif_error}")
                    # 尝试不传递EXIF数据
                    image.save(output_path, format='AVIF')
            # 对于其他格式
            else:
                # 使用原始格式或默认格式
                save_format = original_format or image.format or 'PNG'
                if 'exif' in image.info:
                    save_kwargs['exif'] = image.info['exif']
                image.save(output_path, format=save_format, **save_kwargs)
            
            # 验证保存的图片是否包含GPS信息
            try:
                with open(output_path, 'rb') as f:
                    tags = exifread.process_file(f)
                has_gps = any('GPS' in tag for tag in tags)
                print(f"Saved image has GPS info: {has_gps}")
                if has_gps:
                    for tag in tags:
                        if 'GPS' in tag:
                            print(f"  {tag}: {tags[tag]}")
            except Exception as verify_error:
                print(f"Failed to verify GPS info: {verify_error}")
            
            print(f"Successfully saved image: {output_path}")
            return True
        except Exception as e:
            print(f"Failed to save image: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def exifread_dms_to_decimal(dms: tuple, ref: str) -> float:
        """将exifread返回的度分秒格式转换为十进制"""
        # exifread返回的DMS格式是 (degrees, minutes, seconds)
        degrees = float(dms[0])
        minutes = float(dms[1])
        seconds = float(dms[2])
        
        decimal = degrees + minutes / 60 + seconds / 3600
        
        # 根据方向调整符号
        if ref in ['S', 'W']:
            decimal = -decimal
        
        return decimal
    
    @staticmethod
    def get_gps_info(file_path: str) -> Optional[Tuple[float, float]]:
        """从图片中读取GPS信息"""
        if not file_path:
            print("Error: file_path is None")
            return None
            
        try:
            # 使用exifread库读取EXIF数据
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f)
            
            # 打印所有GPS相关标签
            print("GPS tags found:")
            for tag in tags:
                if 'GPS' in tag:
                    print(f"  {tag}: {tags[tag]}")
            
            # 查找GPS相关标签
            gps_latitude = tags.get('GPS GPSLatitude')
            gps_latitude_ref = tags.get('GPS GPSLatitudeRef')
            gps_longitude = tags.get('GPS GPSLongitude')
            gps_longitude_ref = tags.get('GPS GPSLongitudeRef')
            
            # 检查是否获取到所有必要的GPS数据
            if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
                # 转换GPSLatitudeRef和GPSLongitudeRef为字符串
                lat_ref = str(gps_latitude_ref)
                lon_ref = str(gps_longitude_ref)
                
                # 转换GPSLatitude和GPSLongitude为元组
                # exifread返回的格式是 Ratio对象，需要转换为浮点数
                lat_dms = tuple(float(x.num) / float(x.den) for x in gps_latitude.values)
                lon_dms = tuple(float(x.num) / float(x.den) for x in gps_longitude.values)
                
                # 转换为十进制
                lat = GeoProcessor.exifread_dms_to_decimal(lat_dms, lat_ref)
                lon = GeoProcessor.exifread_dms_to_decimal(lon_dms, lon_ref)
                
                print(f"GPS data: lat={lat}, lon={lon}")
                return (lat, lon)
            else:
                print("No GPS data found in image")
                return None
        except Exception as e:
            print(f"Failed to get GPS info: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def process_image(file_path: str, lat: float, lon: float, output_path: Optional[str] = None, overwrite: bool = False) -> bool:
        """完整处理流程：读取图片 -> 添加GPS -> 保存"""
        try:
            # 确保经纬度是浮点数
            lat = float(lat)
            lon = float(lon)
            
            # 读取图片
            image = GeoProcessor.read_image(file_path)
            if image is None:
                print(f"Failed to read image: {file_path}")
                return False
            
            # 添加GPS信息
            image_with_gps = GeoProcessor.add_gps_to_image(image, lat, lon)
            
            # 保存图片
            success = GeoProcessor.save_image(image_with_gps, file_path, output_path, overwrite)
            if success:
                print(f"Successfully saved image with GPS: {output_path or file_path}")
            else:
                print(f"Failed to save image: {output_path or file_path}")
            
            return success
        except Exception as e:
            print(f"Failed to process image: {e}")
            import traceback
            traceback.print_exc()
            return False
