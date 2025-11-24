// 全局变量
let selectedImages = [];
let selectedLocation = null;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // 监听图片选择事件
    const imageInput = document.getElementById('imageInput');
    imageInput.addEventListener('change', handleImageSelection);
    
    // 初始化pywebview API
    initializePyWebViewAPI();
}

// 处理图片选择
function handleImageSelection(event) {
    const files = event.target.files;
    if (files.length === 0) return;
    
    const newImages = [];
    let processedCount = 0;
    const totalFiles = Array.from(files).length;
    
    Array.from(files).forEach(file => {
        if (!file.type.startsWith('image/')) {
            showMessage(`文件 ${file.name} 不是图片格式`, 'error');
            processedCount++;
            if (processedCount === totalFiles) {
                updateImageList();
                updateConfirmButton();
            }
            return;
        }
        
        // 检查是否已存在同名文件
        if (selectedImages.some(img => img.name === file.name)) {
            showMessage(`图片 "${file.name}" 已存在`, 'warning');
            processedCount++;
            if (processedCount === totalFiles) {
                updateImageList();
                updateConfirmButton();
            }
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            const imageData = {
                id: generateId(),
                name: file.name,
                size: file.size,
                type: file.type,
                dataUrl: e.target.result,
                location: null, // 初始位置信息为空
                timestamp: new Date().toISOString()
            };
            
            // 尝试读取图片的EXIF位置信息
            readImageLocation(file, imageData).then(() => {
                newImages.push(imageData);
                processedCount++;
                
                // 如果所有文件都处理完成，更新界面
                if (processedCount === totalFiles) {
                    selectedImages = [...selectedImages, ...newImages];
                    updateImageList();
                    updateConfirmButton();
                    showMessage(`成功添加 ${newImages.length} 张图片`, 'success');
                }
            }).catch(error => {
                console.error('处理图片时出错:', error);
                newImages.push(imageData);
                processedCount++;
                
                // 如果所有文件都处理完成，更新界面
                if (processedCount === totalFiles) {
                    selectedImages = [...selectedImages, ...newImages];
                    updateImageList();
                    updateConfirmButton();
                    showMessage(`成功添加 ${newImages.length} 张图片`, 'success');
                }
            });
        };
        reader.readAsDataURL(file);
    });
    
    // 清空输入框，允许重复选择相同文件
    event.target.value = '';
}

// 更新图片列表显示
function updateImageList() {
    const imageList = document.getElementById('imageList');
    const emptyMessage = document.getElementById('emptyMessage');
    const clearAllBtn = document.getElementById('clearAllBtn');
    
    // 更新清除所有按钮状态
    clearAllBtn.disabled = selectedImages.length === 0;
    
    if (selectedImages.length === 0) {
        imageList.innerHTML = '<p class="text-gray-500 text-center py-8" id="emptyMessage">暂无选择的图片</p>';
        return;
    }
    
    emptyMessage?.remove();
    
    const html = selectedImages.map(image => `
        <div class="selected-image bg-gray-50 rounded-lg p-3 flex items-center justify-between border border-gray-200">
            <div class="flex items-center space-x-3">
                <img src="${image.dataUrl}" alt="${image.name}" class="w-12 h-12 object-cover rounded">
                <div>
                    <p class="font-medium text-sm text-gray-800 truncate max-w-xs">${image.name}</p>
                    <p class="text-xs text-gray-500">${formatFileSize(image.size)}</p>
                    ${image.location ? 
                        `<p class="text-xs text-green-600">已设置位置: ${image.location.latitude.toFixed(6)}, ${image.location.longitude.toFixed(6)}</p>
                         ${image.location.altitude ? `<p class="text-xs text-blue-600">海拔: ${image.location.altitude}米</p>` : ''}
                         ${image.location.timestamp ? `<p class="text-xs text-gray-500">拍摄时间: ${image.location.timestamp}</p>` : ''}` : 
                        '<p class="text-xs text-yellow-600">未设置位置</p>'
                    }
                </div>
            </div>
            <div class="flex space-x-2">
                <button 
                    onclick="removeImage('${image.id}')" 
                    class="text-red-500 hover:text-red-700 p-1 rounded"
                    title="移除图片"
                >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                </button>
            </div>
        </div>
    `).join('');
    
    imageList.innerHTML = html;
}

// 移除图片
function removeImage(imageId) {
    selectedImages = selectedImages.filter(img => img.id !== imageId);
    updateImageList();
    updateConfirmButton();
    showMessage('图片已移除', 'info');
}

// 清除所有图片
function clearAllImages() {
    if (selectedImages.length === 0) {
        showMessage('没有图片可清除', 'warning');
        return;
    }
    
    if (confirm(`确定要清除所有 ${selectedImages.length} 张图片吗？`)) {
        selectedImages = [];
        updateImageList();
        updateConfirmButton();
        showMessage('所有图片已清除', 'info');
    }
}

// 选择地图位置
function selectLocation(event) {
    const mapContainer = document.getElementById('mapContainer');
    const marker = document.getElementById('locationMarker');
    const rect = mapContainer.getBoundingClientRect();
    
    // 计算点击位置相对于地图容器的坐标
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // 显示标记
    marker.style.left = x + 'px';
    marker.style.top = y + 'px';
    marker.classList.remove('hidden');
    
    // 模拟经纬度（实际应用中应该使用地图API转换）
    const latitude = 39.9042 + (y / rect.height - 0.5) * 0.1; // 北京附近
    const longitude = 116.4074 + (x / rect.width - 0.5) * 0.1; // 北京附近
    
    selectedLocation = {
        latitude: parseFloat(latitude.toFixed(6)),
        longitude: parseFloat(longitude.toFixed(6)),
        x: x,
        y: y
    };
    
    updateLocationDisplay();
    updateConfirmButton();
    
    showMessage('位置选择成功', 'success');
}



// 更新地图选择经纬度显示
function updateSelectedCoordinatesDisplay() {
    const selectedCoordinates = document.getElementById('selectedCoordinates');
    const locationInfo = document.getElementById('locationInfo');
    
    if (selectedLocation) {
        selectedCoordinates.textContent = `纬度: ${selectedLocation.latitude.toFixed(6)}, 经度: ${selectedLocation.longitude.toFixed(6)}`;
        selectedCoordinates.className = 'coordinates-display bg-green-100 p-3 rounded text-sm text-green-800 border border-green-300';
        
        // 模拟地理位置信息（实际应用中应该使用逆地理编码API）
        const locationText = getMockLocationInfo(selectedLocation.latitude, selectedLocation.longitude);
        locationInfo.textContent = locationText;
        locationInfo.className = 'bg-gray-100 p-3 rounded text-sm text-gray-800';
    } else {
        selectedCoordinates.textContent = '未选择位置';
        selectedCoordinates.className = 'coordinates-display bg-green-50 p-3 rounded text-sm text-gray-800 border border-green-200';
        locationInfo.textContent = '未选择位置';
        locationInfo.className = 'bg-gray-100 p-3 rounded text-sm text-gray-800';
    }
}

// 更新位置信息显示（兼容旧代码）
function updateLocationDisplay() {
    updateSelectedCoordinatesDisplay();
}

// 模拟地理位置信息
function getMockLocationInfo(lat, lng) {
    // 简单的模拟，实际应用中应该使用真实的地理编码服务
    if (lat > 39.8 && lat < 40.0 && lng > 116.3 && lng < 116.5) {
        return '北京市中心区域';
    } else if (lat > 31.1 && lat < 31.3 && lng > 121.4 && lng < 121.6) {
        return '上海市中心区域';
    } else {
        return '自定义位置';
    }
}

// 更新确认按钮状态
function updateConfirmButton() {
    const confirmBtn = document.getElementById('confirmBtn');
    const hasImages = selectedImages.length > 0;
    const hasLocation = selectedLocation !== null;
    
    confirmBtn.disabled = !(hasImages && hasLocation);
}

// 确认添加位置信息
function confirmLocation() {
    if (!selectedLocation || selectedImages.length === 0) {
        showMessage('请先选择图片和位置', 'error');
        return;
    }
    
    // 为所有选中的图片添加位置信息
    selectedImages.forEach(image => {
        image.location = { ...selectedLocation };
    });
    
    updateImageList();
    
    // 调用pywebview API保存数据
    saveGeoDataToBackend();
    
    showMessage('位置信息已成功添加到所有图片', 'success');
}

// 保存地理数据到后端
function saveGeoDataToBackend() {
    const geoData = {
        images: selectedImages.map(img => ({
            name: img.name,
            location: img.location,
            timestamp: img.timestamp
        })),
        timestamp: new Date().toISOString()
    };
    
    // 调用pywebview API
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.save_geo_data(geoData)
            .then(response => {
                console.log('数据保存成功:', response);
            })
            .catch(error => {
                console.error('数据保存失败:', error);
                showMessage('数据保存失败，请重试', 'error');
            });
    } else {
        // 开发环境下的模拟保存
        console.log('模拟保存地理数据:', geoData);
        showMessage('数据已保存（模拟）', 'info');
    }
}

// 初始化pywebview API
function initializePyWebViewAPI() {
    // 创建全局API对象供pywebview调用
    window.pywebviewAPI = {
        // 从后端加载图片数据
        load_images: function() {
            return new Promise((resolve) => {
                // 模拟从后端加载数据
                setTimeout(() => {
                    resolve({
                        success: true,
                        data: selectedImages
                    });
                }, 500);
            });
        },
        
        // 获取当前状态
        get_status: function() {
            return {
                images_count: selectedImages.length,
                has_location: selectedLocation !== null,
                selected_location: selectedLocation
            };
        },
        
        // 清除所有数据
        clear_all: function() {
            selectedImages = [];
            selectedLocation = null;
            updateImageList();
            updateLocationDisplay();
            updateConfirmButton();
            document.getElementById('locationMarker').classList.add('hidden');
            
            return { success: true, message: '所有数据已清除' };
        },
        
        // 导出数据
        export_data: function() {
            const exportData = {
                metadata: {
                    export_time: new Date().toISOString(),
                    version: '1.0'
                },
                images: selectedImages
            };
            
            return exportData;
        }
    };
    
    console.log('pywebview API 初始化完成');
}

// 读取图片位置信息（使用exifr库实现真实EXIF GPS读取）
async function readImageLocation(file, imageData) {
    try {
        // 使用exifr库读取EXIF数据
        const exifData = await exifr.parse(file);
        
        if (exifData && exifData.GPSLatitude && exifData.GPSLongitude) {
            // 获取GPS纬度信息
            let latitude = exifData.GPSLatitude;
            let longitude = exifData.GPSLongitude;
            
            // 处理GPS坐标格式（度分秒转换为十进制）
            if (typeof latitude === 'object' && latitude !== null) {
                latitude = latitude.degrees + latitude.minutes/60 + latitude.seconds/3600;
            }
            if (typeof longitude === 'object' && longitude !== null) {
                longitude = longitude.degrees + longitude.minutes/60 + longitude.seconds/3600;
            }
            
            // 处理GPS半球信息
            if (exifData.GPSLatitudeRef === 'S') {
                latitude = -latitude;
            }
            if (exifData.GPSLongitudeRef === 'W') {
                longitude = -longitude;
            }
            
            imageData.location = {
                latitude: parseFloat(latitude.toFixed(6)),
                longitude: parseFloat(longitude.toFixed(6)),
                altitude: exifData.GPSAltitude ? parseFloat(exifData.GPSAltitude.toFixed(2)) : null,
                timestamp: exifData.GPSDateStamp || exifData.DateTime || null
            };
            
            console.log(`图片 ${file.name} 包含GPS位置信息:`, imageData.location);
            console.log('完整的EXIF数据:', exifData);
            
        } else if (exifData && (exifData.latitude || exifData.longitude)) {
            // 处理其他格式的位置信息
            imageData.location = {
                latitude: parseFloat((exifData.latitude || 0).toFixed(6)),
                longitude: parseFloat((exifData.longitude || 0).toFixed(6))
            };
            
            console.log(`图片 ${file.name} 包含位置信息:`, imageData.location);
        } else {
            console.log(`图片 ${file.name} 不包含GPS位置信息`);
            console.log('可用的EXIF数据:', exifData);
        }
        
    } catch (error) {
        console.error(`读取图片 ${file.name} 的EXIF数据时出错:`, error);
        // 如果读取失败，可以尝试使用模拟数据作为备选
        // 这里我们保持imageData.location为null，表示没有位置信息
    }
}

// 工具函数
function generateId() {
    return 'img_' + Math.random().toString(36).substr(2, 9);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showMessage(message, type = 'info') {
    // 创建消息元素
    const messageEl = document.createElement('div');
    messageEl.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transform transition-transform duration-300 translate-x-full`;
    
    const colors = {
        success: 'bg-green-500 text-white',
        error: 'bg-red-500 text-white',
        warning: 'bg-yellow-500 text-white',
        info: 'bg-blue-500 text-white'
    };
    
    messageEl.className += ` ${colors[type] || colors.info}`;
    messageEl.innerHTML = `
        <div class="flex items-center">
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                ${getMessageIcon(type)}
            </svg>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(messageEl);
    
    // 显示动画
    setTimeout(() => {
        messageEl.classList.remove('translate-x-full');
    }, 10);
    
    // 自动隐藏
    setTimeout(() => {
        messageEl.classList.add('translate-x-full');
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.parentNode.removeChild(messageEl);
            }
        }, 300);
    }, 3000);
}

function getMessageIcon(type) {
    const icons = {
        success: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>',
        error: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>',
        warning: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z"></path>',
        info: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>'
    };
    return icons[type] || icons.info;
}

// 键盘快捷键支持
document.addEventListener('keydown', function(event) {
    // Ctrl+D: 清除所有数据
    if (event.ctrlKey && event.key === 'd') {
        event.preventDefault();
        if (window.pywebviewAPI) {
            window.pywebviewAPI.clear_all();
            showMessage('所有数据已清除', 'info');
        }
    }
    
    // Escape: 取消位置选择
    if (event.key === 'Escape') {
        selectedLocation = null;
        updateLocationDisplay();
        updateConfirmButton();
        document.getElementById('locationMarker').classList.add('hidden');
    }
});