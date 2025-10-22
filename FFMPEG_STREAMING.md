# FFmpeg 推流部署指南（推荐方案）

## 🎯 为什么选择 FFmpeg 而不是 GStreamer？

### ✅ 优势

1. **安装简单**

   ```bash
   sudo apt-get install ffmpeg  # 一条命令搞定
   ```

2. **无需 OpenCV GStreamer 支持**

   - 标准的 `opencv-python` 包即可
   - 不需要重新编译 OpenCV

3. **跨平台支持更好**

   - Ubuntu、CentOS、Debian 等都支持
   - 配置参数更直观

4. **性能相当**
   - 使用 libx264 编码器
   - 支持硬件加速

### ❌ GStreamer 的问题

- OpenCV 的 PyPI 包不包含 GStreamer 支持
- 需要从源码编译 OpenCV（30-60 分钟）
- 配置复杂，管道字符串难以调试

---

## 🚀 快速部署（x86_64 Ubuntu）

### 步骤 1：安装系统依赖

```bash
# 更新包列表
sudo apt-get update

# 安装 FFmpeg
sudo apt-get install -y ffmpeg

# 验证安装
ffmpeg -version
```

### 步骤 2：安装项目依赖

```bash
cd /path/to/yolo-detect

# 安装 Poetry（如果还没有）
curl -sSL https://install.python-poetry.org | python3 -

# 安装项目依赖
poetry install

# 验证依赖
poetry run python -c "import cv2, ultralytics; print('✅ 依赖安装成功')"
```

### 步骤 3：配置摄像头

```bash
# 查看可用摄像头
ls -l /dev/video*

# 测试摄像头
ffmpeg -f v4l2 -i /dev/video0 -frames 1 test.jpg

# 如果需要调整权限
sudo usermod -a -G video $USER
newgrp video
```

### 步骤 4：测试推流

```bash
# 运行 FFmpeg 推流测试
poetry run python test/test_push_ffmpeg.py
```

---

## 📋 配置说明

### 代码配置

编辑 `test/test_push_ffmpeg.py`：

```python
streamer = FFmpegPushStreamer(
    model_path="runs/train/person_detection/weights/best.pt",
    host="115.120.237.79",      # 👈 修改为您的服务器IP
    port=5004,                  # 👈 修改为您的端口
    video_width=640,            # 视频宽度
    video_height=480,           # 视频高度
    fps=15,                     # 帧率
    bitrate=400,                # 比特率 (kbps)
    camera_device=0,            # 👈 摄像头设备 (0 或 '/dev/video4')
    headless=True               # 无头模式
)
```

### FFmpeg 参数映射

我们的 FFmpeg 命令对应您的 GStreamer 命令：

| GStreamer 参数           | FFmpeg 参数           | 说明        |
| ------------------------ | --------------------- | ----------- |
| `width=640,height=480`   | `-s 640x480`          | 视频分辨率  |
| `framerate=15/1`         | `-r 15`               | 帧率        |
| `x264enc bitrate=400`    | `-b:v 400k`           | 比特率      |
| `speed-preset=ultrafast` | `-preset ultrafast`   | 编码速度    |
| `tune=zerolatency`       | `-tune zerolatency`   | 低延迟优化  |
| `profile=baseline`       | `-profile:v baseline` | H.264 配置  |
| `key-int-max=15`         | `-g 15`               | 关键帧间隔  |
| `ref=1`                  | `-refs 1`             | 参考帧数量  |
| `bframes=0`              | `-bf 0`               | B 帧数量    |
| `threads=2`              | `-threads 2`          | 编码线程    |
| `pt=96`                  | `-payload_type 96`    | RTP payload |
| `mtu=1200`               | `-pkt_size 1200`      | MTU 大小    |
| `udpsink host=X port=Y`  | `rtp://X:Y`           | 目标地址    |

---

## 🔧 接收端配置

### 使用 VLC 接收

```bash
# 创建 SDP 文件: stream.sdp
cat > stream.sdp << EOF
v=0
o=- 0 0 IN IP4 127.0.0.1
s=YOLO Detection Stream
c=IN IP4 115.120.237.79
t=0 0
m=video 5004 RTP/AVP 96
a=rtpmap:96 H264/90000
EOF

# 使用 VLC 播放
vlc stream.sdp
```

### 使用 FFplay 接收

```bash
# 创建 SDP 文件后
ffplay -protocol_whitelist file,rtp,udp stream.sdp
```

### 使用 GStreamer 接收（如果有）

```bash
gst-launch-1.0 udpsrc port=5004 \
  ! application/x-rtp,encoding-name=H264,payload=96 \
  ! rtph264depay \
  ! h264parse \
  ! avdec_h264 \
  ! videoconvert \
  ! autovideosink
```

---

## 🐛 常见问题

### Q1: FFmpeg 未找到

**错误**: `FFmpeg 未安装！`

**解决**:

```bash
sudo apt-get install -y ffmpeg
ffmpeg -version
```

### Q2: 摄像头无法打开

**错误**: `无法打开摄像头`

**解决**:

```bash
# 检查摄像头设备
ls -l /dev/video*

# 测试摄像头
ffmpeg -f v4l2 -list_formats all -i /dev/video0

# 修改代码中的 camera_device
camera_device='/dev/video4'  # 使用正确的设备路径
```

### Q3: 推流成功但接收端无画面

**可能原因**:

1. 防火墙阻止 UDP 端口 5004
2. 接收端 SDP 文件配置错误
3. 网络 MTU 问题

**解决**:

```bash
# 1. 检查防火墙
sudo ufw allow 5004/udp

# 2. 验证网络连通性
ping 115.120.237.79

# 3. 使用 tcpdump 检查数据包
sudo tcpdump -i any port 5004
```

### Q4: 延迟太高

**优化建议**:

```python
# 降低分辨率
video_width=320
video_height=240

# 降低比特率
bitrate=200

# 提高帧率（如果带宽允许）
fps=30
```

### Q5: CPU 占用过高

**优化建议**:

```python
# 使用更快的预设（牺牲质量）
# 修改 _init_ffmpeg 中的参数
'-preset', 'superfast',  # 或 'veryfast'

# 降低分辨率和帧率
video_width=320
video_height=240
fps=10
```

---

## 📊 性能对比

| 方案       | 安装难度        | 性能       | 延迟 | 推荐场景        |
| ---------- | --------------- | ---------- | ---- | --------------- |
| **FFmpeg** | ⭐ 简单         | ⭐⭐⭐⭐   | 低   | ✅ 推荐（通用） |
| GStreamer  | ⭐⭐⭐⭐⭐ 困难 | ⭐⭐⭐⭐⭐ | 最低 | 专业场景        |
| RTMP       | ⭐⭐ 一般       | ⭐⭐⭐     | 中   | 直播平台        |

---

## 🎬 完整示例

### 1. 基础推流

```python
from service.push_streamer_ffmpeg import FFmpegPushStreamer

streamer = FFmpegPushStreamer(
    model_path="models/yolo11n.pt",
    host="192.168.1.100",
    port=5004,
    camera_device=0
)

streamer.start_streaming()
```

### 2. 使用设备路径

```python
streamer = FFmpegPushStreamer(
    model_path="runs/train/person_detection/weights/best.pt",
    host="115.120.237.79",
    port=5004,
    camera_device="/dev/video4",  # Linux 设备路径
    fps=15,
    bitrate=400
)

streamer.start_streaming()
```

### 3. 高质量推流

```python
streamer = FFmpegPushStreamer(
    model_path="runs/train/person_detection/weights/best.pt",
    host="115.120.237.79",
    port=5004,
    video_width=1280,
    video_height=720,
    fps=30,
    bitrate=2000,  # 2Mbps
    camera_device=0
)

streamer.start_streaming()
```

---

## 🔄 从 GStreamer 迁移

如果您之前使用 GStreamer 版本：

```python
# 旧代码 (GStreamer)
from service.push_streamer import PushStreamer
streamer = PushStreamer(...)

# 新代码 (FFmpeg) - 只需更改导入
from service.push_streamer_ffmpeg import FFmpegPushStreamer
streamer = FFmpegPushStreamer(...)  # 参数相同

# 或者使用别名（向后兼容）
from service.push_streamer_ffmpeg import FFmpegPushStreamer as PushStreamer
```

---

## 📚 参考资源

- **FFmpeg 官方文档**: https://ffmpeg.org/documentation.html
- **H.264 编码指南**: https://trac.ffmpeg.org/wiki/Encode/H.264
- **RTP 流媒体**: https://trac.ffmpeg.org/wiki/StreamingGuide

---

## ✅ 一键部署脚本

创建并运行：

```bash
#!/bin/bash
# 一键部署 FFmpeg 推流

# 安装依赖
sudo apt-get update
sudo apt-get install -y ffmpeg

# 安装项目
cd /path/to/yolo-detect
poetry install

# 测试
poetry run python test/test_push_ffmpeg.py

echo "✅ 部署完成！"
```

保存为 `deploy_ffmpeg.sh`，然后运行：

```bash
chmod +x deploy_ffmpeg.sh
./deploy_ffmpeg.sh
```

---

**推荐**: 使用 FFmpeg 方案，部署更简单，维护更容易！🎉
