# YOLO 检测推流服务 - Ubuntu 部署指南

适用于配置较低的 Ubuntu 服务器的自动部署方案。

## 系统要求

- Ubuntu 20.04 或更高版本
- Python 3.10+
- 至少 1GB 可用内存
- USB 摄像头 / RealSense 摄像头 / 网络摄像头 (RTSP)
- 网络连接

**支持的摄像头：**
- USB 摄像头 (UVC 兼容)
- Intel RealSense 系列 (通过 librealsense2 或 V4L2)
- 网络摄像头 (RTSP 协议)

## 快速部署

### 1. 上传项目到服务器

```bash
# 在本地打包项目
tar czf yolo-detect.tar.gz yolo-detect/

# 上传到服务器
scp yolo-detect.tar.gz user@server:/tmp/

# 在服务器上解压
ssh user@server
cd /tmp
tar xzf yolo-detect.tar.gz
```

### 2. 运行安装脚本

```bash
cd yolo-detect
sudo bash deploy/scripts/install.sh
```

安装脚本会自动：
- 安装系统依赖 (Python, FFmpeg, OpenCV 等)
- 配置 Python 环境
- 安装 Systemd 服务
- 检测摄像头设备

### 3. 配置推流地址和模型预设

编辑配置文件：

```bash
sudo nano /opt/yolo-detect/deploy/config/service.conf
```

推流目标已预配置为 `115.120.237.79:5004`，如需修改请更新：

```bash
# 推流目标服务器
PUSH_HOST="115.120.237.79"   # 推流服务器地址
PUSH_PORT=5004               # 推流端口

# 模型预设 (根据服务器性能选择)
MODEL_PRESET="standard"      # full/standard/performance/minimal

# 网络摄像头 (可选，如果有)
RTSP_URL="rtsp://admin:password@192.168.1.100:554/stream1"
```

**模型预设说明：**

| 预设 | 行人 | 人脸 | 表情 | 年龄 | 内存需求 | 适用场景 |
|------|------|------|------|------|----------|----------|
| `full` | ✅ | ✅ | ✅ | ✅ | >= 2GB | 高性能服务器 |
| `standard` | ✅ | ✅ | ✅ | ❌ | >= 1GB | **推荐默认** |
| `performance` | ✅ | ❌ | ❌ | ❌ | >= 512MB | 低配服务器 |
| `minimal` | ✅ | ❌ | ❌ | ❌ | >= 256MB | 最低配置 |

### 4. 重新检测摄像头

```bash
sudo bash /opt/yolo-detect/deploy/scripts/detect_camera.sh
```

脚本会自动选择：
- 优先使用网络摄像头 (RTSP)
- 如果无网络摄像头，使用 USB 摄像头

### 5. 启动服务

```bash
# 启动服务
sudo systemctl start yolo-streaming

# 设置开机自启
sudo systemctl enable yolo-streaming

# 查看状态
sudo systemctl status yolo-streaming
```

## 服务管理

### 常用命令

| 命令 | 说明 |
|------|------|
| `sudo systemctl start yolo-streaming` | 启动服务 |
| `sudo systemctl stop yolo-streaming` | 停止服务 |
| `sudo systemctl restart yolo-streaming` | 重启服务 |
| `sudo systemctl enable yolo-streaming` | 开机自启 |
| `sudo systemctl disable yolo-streaming` | 禁用自启 |
| `sudo systemctl status yolo-streaming` | 查看状态 |
| `sudo journalctl -u yolo-streaming -f` | 查看日志 |

### 快捷脚本

```bash
# 检查服务状态
bash /opt/yolo-detect/deploy/scripts/status.sh

# 重启服务（重新检测摄像头）
bash /opt/yolo-detect/deploy/scripts/restart.sh
```

## 配置文件

配置文件位置：`/opt/yolo-detect/deploy/config/service.conf`

### 摄像头配置

```bash
# 网络摄像头 RTSP 地址
RTSP_URL="rtsp://admin:password@192.168.1.100:554/stream1"

# USB 摄像头设备（自动检测）
# USB_CAMERA="/dev/video0"
```

### 推流配置

```bash
# 推流目标服务器
PUSH_HOST="115.120.237.79"
PUSH_PORT=5004
```

### 检测配置

```bash
# 模型路径
MODEL_PATH="models/person_detector.pt"

# 检测置信度 (0-1)
CONFIDENCE=0.5

# IOU 阈值 (0-1)
IOU=0.45

# 推理设备 (cpu/mps/cuda)
DEVICE="cpu"
```

### 视频配置

```bash
# 分辨率
VIDEO_WIDTH=640
VIDEO_HEIGHT=480

# 帧率 (低配置服务器建议 10-15)
FPS=15

# 比特率 kbps (低网络环境建议 300-500)
BITRATE=500
```

## 故障排查

### 1. 服务无法启动

```bash
# 查看详细日志
sudo journalctl -u yolo-streaming -n 50 --no-pager

# 查看应用日志
tail -f /opt/yolo-detect/logs/streaming.log
```

### 2. 摄像头无法检测

#### USB 摄像头

```bash
# 列出所有视频设备
ls -la /dev/video*

# 查看 USB 摄像头详情
v4l2-ctl --device=/dev/video0 --info
```

#### RealSense 摄像头

```bash
# 检测 RealSense USB 设备
lsusb | grep -i real

# 安装 RealSense 支持
sudo apt-get install librealsense2-utils librealsense2-dev

# 测试 RealSense 设备
realsense-viewer

# 检查 V4L2 兼容模式
v4l2-ctl --list-devices
```

**RealSense 注意事项：**
- RealSense 摄像头可能以深度相机或 RGB 相机模式运行
- 确保 udev 规则已正确配置（安装脚本会自动设置）
- 如果 V4L2 模式不工作，可能需要使用 librealsense2 Python API

```bash
# 列出所有视频设备
ls -la /dev/video*

# 查看 USB 摄像头详情
v4l2-ctl --device=/dev/video0 --info

# 测试 RTSP 连接
ffprobe rtsp://admin:password@192.168.1.100:554/stream1
```

### 3. 推流失败

```bash
# 检查网络连接
ping 192.168.1.100

# 检查端口是否开放
nc -zv 192.168.1.100 5004
```

### 4. 内存不足

```bash
# 降低分辨率和帧率
# 编辑 service.conf
VIDEO_WIDTH=480
VIDEO_HEIGHT=360
FPS=10
```

## 卸载

```bash
cd yolo-detect
sudo bash deploy/scripts/uninstall.sh
```

## 目录结构

```
/opt/yolo-detect/
├── deploy/
│   ├── scripts/
│   │   ├── install.sh         # 安装脚本
│   │   ├── uninstall.sh       # 卸载脚本
│   │   ├── detect_camera.sh   # 摄像头检测
│   │   ├── restart.sh         # 重启脚本
│   │   ├── status.sh          # 状态检查
│   │   └── start_service.py   # 服务启动
│   └── config/
│       └── service.conf       # 服务配置
├── src/
│   ├── pipeline.py
│   └── service/
│       └── push_streamer_ffmpeg.py
├── models/
│   └── person_detector.pt
└── logs/
    └── streaming.log
```

## 接收推流

在接收端使用 FFmpeg 播放：

```bash
ffplay -fflags nobuffer -flags low_delay -framedrop udp://@:5004
```

或使用 VLC 打开：`udp://@:5004`
