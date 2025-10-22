# GStreamer 推流问题修复指南

## 问题症状

```
[推流模块] | WARNING | GStreamer 推流初始化失败，将使用替代方案
```

或者 GStreamer 命令报错：

```
警告: 错误管道: 无组件"x264enc"
```

## 原因

硬件设备上缺少 GStreamer 的视频编码器插件（特别是 `x264enc`）。

## 解决方案

### 方法 1：安装 GStreamer 插件（推荐）

在硬件设备（Ubuntu/树莓派）上运行：

```bash
# 更新包列表
sudo apt-get update

# 安装 GStreamer 插件（包含 x264enc）
sudo apt-get install -y gstreamer1.0-plugins-ugly

# 安装其他有用的编码器
sudo apt-get install -y gstreamer1.0-plugins-bad gstreamer1.0-libav

# 验证安装
gst-inspect-1.0 x264enc
```

如果看到 x264enc 的详细信息，说明安装成功。

### 方法 2：测试推流

安装完成后，测试 GStreamer 推流：

```bash
# 测试视频推流（发送端）
gst-launch-1.0 videotestsrc ! videoconvert ! x264enc ! rtph264pay ! udpsink host=127.0.0.1 port=5004

# 在另一个终端接收（接收端）
gst-launch-1.0 udpsrc port=5004 ! application/x-rtp,encoding-name=H264 ! rtph264depay ! avdec_h264 ! videoconvert ! autovideosink
```

### 方法 3：运行项目诊断工具

```bash
cd /path/to/yolo-detect
poetry run python test/test_gstreamer_debug.py
```

诊断工具会：

- ✅ 检查所有可用的 GStreamer 编码器
- ✅ 测试 OpenCV 的 GStreamer 支持
- ✅ 测试多种推流管道
- ✅ 提供详细的错误信息和解决方案

### 方法 4：重新测试项目推流

```bash
poetry run python test/test_push.py
```

现在应该看到：

```
[推流模块] | SUCCESS | GStreamer 推流初始化成功！使用编码器: x264enc
```

## 可用的编码器

项目会按优先级自动尝试以下编码器：

1. **x264enc** - H.264 编码器（最佳质量，推荐）

   - 安装：`sudo apt-get install gstreamer1.0-plugins-ugly`

2. **openh264enc** - OpenH264 编码器

   - 安装：`sudo apt-get install gstreamer1.0-plugins-bad`

3. **avenc_h264** - FFmpeg H.264 编码器

   - 安装：`sudo apt-get install gstreamer1.0-libav`

4. **omxh264enc** - 硬件 H.264 编码器（仅树莓派）

   - 树莓派自带

5. **jpegenc** - JPEG 编码器（质量较低，备选）
   - 通常已安装

## 验证编码器

检查哪些编码器可用：

```bash
# 检查 x264enc
gst-inspect-1.0 x264enc

# 检查 openh264enc
gst-inspect-1.0 openh264enc

# 检查 avenc_h264
gst-inspect-1.0 avenc_h264

# 检查 jpegenc
gst-inspect-1.0 jpegenc
```

## 常见问题

### Q1: 安装后仍然失败？

**A:** 重启终端或重新登录，确保环境变量生效：

```bash
# 退出并重新进入 Poetry shell
exit
poetry shell
```

### Q2: 在树莓派上推荐使用哪个编码器？

**A:** 树莓派建议使用硬件编码器 `omxh264enc`，性能最好：

```bash
gst-inspect-1.0 omxh264enc
```

项目会自动检测并使用可用的最佳编码器。

### Q3: 如何查看详细的推流日志？

**A:** 设置 GStreamer 调试级别：

```bash
export GST_DEBUG=3
poetry run python test/test_push.py
```

### Q4: 推流成功但无法接收？

**A:** 检查：

1. 防火墙设置（开放 UDP 端口 5004）
2. 网络连接（ping 目标主机）
3. 接收端使用正确的命令

## 接收推流

### 使用 GStreamer 接收

```bash
gst-launch-1.0 -v udpsrc port=5004 ! \
    application/x-rtp,encoding-name=H264,payload=96 ! \
    rtph264depay ! h264parse ! avdec_h264 ! \
    videoconvert ! autovideosink
```

### 使用 VLC 播放器

```bash
vlc udp://@:5004
```

### 使用 FFmpeg 接收

```bash
ffmpeg -i udp://127.0.0.1:5004 -c copy output.mp4
```

## 项目代码改进

本次更新已自动支持多种编码器：

- ✅ 自动检测可用编码器
- ✅ 按优先级尝试不同编码器
- ✅ 详细的调试日志
- ✅ 优雅的降级方案

无需修改代码，只需安装插件即可。

## 完整的安装命令（一键复制）

```bash
# 一键安装所有需要的 GStreamer 插件
sudo apt-get update && \
sudo apt-get install -y \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev && \
echo "✅ GStreamer 插件安装完成！" && \
gst-inspect-1.0 x264enc | head -n 5
```

安装完成后运行：

```bash
cd /path/to/yolo-detect
poetry run python test/test_gstreamer_debug.py
poetry run python test/test_push.py
```

---

**提示**：如果问题仍然存在，请运行诊断工具并查看详细输出：

```bash
poetry run python test/test_gstreamer_debug.py
```
