# YOLO 使用指南

## 🎯 项目概述

这是一个完整的 YOLO (You Only Look Once) 目标检测项目，支持：

- ✅ 图像/视频检测
- ✅ 模型训练（支持 Mac GPU 加速）
- ✅ 批量检测
- ✅ 实时摄像头检测

## 🚀 快速开始

### 1. 安装依赖

```bash
poetry install
```

### 2. 下载预训练模型

```bash
poetry run python scripts/download_models.py
```

### 3. 运行检测示例

```bash
# 运行快速入门示例
poetry run python scripts/quickstart.py
```

这个脚本会：

1. 自动下载 YOLO11n 模型
2. 检测一张示例图像
3. 显示检测结果
4. 保存带标注的图像

### 4. 开始训练（支持 Mac GPU）

```bash
# 使用默认配置训练（自动检测 GPU）
poetry run python scripts/start_training.py

# 快速测试（3 轮）
poetry run python scripts/start_training.py --epochs 3 --name quick_test

# 查看所有参数
poetry run python scripts/start_training.py --help
```

详细训练指南请查看 [TRAINING_GUIDE.md](TRAINING_GUIDE.md)

## 📚 可用的示例脚本

### 1. 快速入门 (quickstart.py)

最简单的使用示例，适合初学者。

```bash
poetry run python scripts/quickstart.py
```

### 2. 图像检测 (detect_image.py)

检测单张或多张图像。

```bash
poetry run python scripts/detect_image.py
```

功能：

- 使用预训练模型检测图像
- 显示检测到的目标类别、置信度和位置
- 自动保存带标注的结果图像

### 3. 视频检测 (detect_video.py)

检测视频文件或实时摄像头。

```bash
poetry run python scripts/detect_video.py
```

功能：

- 视频文件检测
- 摄像头实时检测
- YouTube 视频检测
- 目标跟踪

### 3.5 网络摄像头实时检测 (webcam_detect.py) 🆕

使用训练好的模型进行网络摄像头实时检测。

```bash
# 使用训练好的模型
poetry run python scripts/webcam_detect.py

# 使用命令行参数
poetry run python scripts/webcam_detect.py --model runs/train/person_detection/weights/best.pt --conf 0.5

# 启用目标跟踪
poetry run python scripts/webcam_detect.py --track

# 保存检测视频
poetry run python scripts/webcam_detect.py --save
```

功能：

- ✅ 使用训练完成的模型进行实时检测
- ✅ 支持目标跟踪功能
- ✅ 可调节置信度阈值
- ✅ 支持 Mac GPU (MPS) 加速
- ✅ 按 'q' 键退出检测

### 3.6 FFmpeg 推流检测 (test_push_ffmpeg.py) 🆕✨

使用 FFmpeg 进行实时检测推流到远程服务器（推荐方案）。

```bash
# 快速部署（仅需 FFmpeg，不需要 GStreamer）
bash scripts/deploy_ffmpeg.sh

# 运行推流
poetry run python test/test_push_ffmpeg.py
```

功能：

- ✅ 实时 YOLO 检测 + 远程推流
- ✅ 使用 FFmpeg（安装简单，无需 GStreamer）
- ✅ 支持 RTP/UDP 推流到 Janus 等服务器
- ✅ 自动适配摄像头设备
- ✅ 低延迟、高性能

**对比 GStreamer 方案：**

- 安装时间：1 分钟 vs 1 小时
- 配置难度：简单 vs 复杂
- 推荐指数：⭐⭐⭐⭐⭐

查看详细文档：

- `FFMPEG_STREAMING.md` - FFmpeg 推流完整指南
- `STREAMING_COMPARISON.md` - FFmpeg vs GStreamer 对比

### 4. 批量检测 (batch_detect.py)

批量处理多张图像。

```bash
poetry run python scripts/batch_detect.py
```

功能：

- 批量处理文件夹中的所有图像
- 导出 JSON 格式的检测结果
- 统计信息

### 5. 高级示例 (advanced_examples.py)

展示更多高级用法。

```bash
poetry run python scripts/advanced_examples.py
```

功能：

- 自定义结果处理
- 模型对比
- 类别过滤
- 性能基准测试

### 6. 模型训练 (train_model.py)

训练自定义 YOLO 模型。

```bash
poetry run python scripts/train_model.py
```

功能：

- 训练自定义数据集
- 模型验证
- 模型导出

## 🎯 常用命令

### 使用命令行工具

YOLO 提供了便捷的命令行接口：

```bash
# 检测图像
poetry run yolo predict model=yolo11n.pt source=image.jpg

# 检测视频
poetry run yolo predict model=yolo11n.pt source=video.mp4

# 使用摄像头
poetry run yolo predict model=yolo11n.pt source=0 show=True

# 训练模型
poetry run yolo train data=dataset.yaml model=yolo11n.pt epochs=100

# 验证模型
poetry run yolo val model=best.pt data=dataset.yaml

# 导出模型
poetry run yolo export model=yolo11n.pt format=onnx
```

### 使用 Python API

更灵活的 Python 代码方式：

```python
from ultralytics import YOLO

# 加载模型
model = YOLO('yolo11n.pt')

# 检测
results = model('image.jpg')

# 处理结果
for result in results:
    boxes = result.boxes
    for box in boxes:
        print(f"类别: {model.names[int(box.cls)]}")
        print(f"置信度: {box.conf[0]:.2f}")
```

## 🔧 自定义参数

### 调整置信度阈值

```python
# 只显示高置信度的检测结果
results = model('image.jpg', conf=0.5)  # 默认是0.25
```

### 只检测特定类别

```python
# 只检测人和车（COCO类别ID: 0=person, 2=car）
results = model('image.jpg', classes=[0, 2])
```

### 调整图像大小

```python
# 使用更大的图像尺寸可以提高准确度（但速度会变慢）
results = model('image.jpg', imgsz=1280)  # 默认是640
```

### 使用 GPU 加速

```python
# 使用GPU 0
results = model('image.jpg', device='0')

# 使用多个GPU
results = model('image.jpg', device='0,1')

# 使用CPU
results = model('image.jpg', device='cpu')
```

## 📊 YOLO 模型选择

| 模型       | 大小  | 速度      | 精度               | 适用场景           |
| ---------- | ----- | --------- | ------------------ | ------------------ |
| yolo11n.pt | 2.6MB | ⚡️⚡️⚡️ | ⭐️⭐️⭐️          | 实时应用、移动设备 |
| yolo11s.pt | 9.4MB | ⚡️⚡️    | ⭐️⭐️⭐️⭐️       | 平衡性能和速度     |
| yolo11m.pt | 20MB  | ⚡️       | ⭐️⭐️⭐️⭐️⭐️    | 高精度应用         |
| yolo11l.pt | 25MB  | 🐌        | ⭐️⭐️⭐️⭐️⭐️    | 服务器端部署       |
| yolo11x.pt | 57MB  | 🐌🐌      | ⭐️⭐️⭐️⭐️⭐️⭐️ | 最高精度要求       |

更换模型只需修改模型名称：

```python
model = YOLO('yolo11s.pt')  # 使用small模型
```

## 📁 结果保存位置

默认情况下，检测结果会保存在：

```
runs/
├── detect/
│   ├── predict/      # 预测结果
│   ├── predict2/     # 第二次预测
│   └── ...
└── train/
    ├── exp/          # 训练结果
    └── ...
```

## 🎨 结果可视化

检测结果会自动保存带标注的图像，包括：

- 边界框（bounding box）
- 类别标签
- 置信度分数

你可以在 `runs/detect/predict/` 文件夹中找到这些图像。

## 💡 使用技巧

### 1. 提高检测准确度

- 使用更大的模型（如 yolo11m.pt）
- 增加图像尺寸（imgsz=1280）
- 提高置信度阈值（conf=0.5）

### 2. 提高检测速度

- 使用更小的模型（如 yolo11n.pt）
- 减小图像尺寸（imgsz=320）
- 使用 GPU 加速

### 3. 减少误检

- 提高置信度阈值
- 调整 IOU 阈值（iou=0.5）
- 只检测需要的类别

### 4. 处理大量图像

- 使用批处理（batch=16）
- 使用流式处理（stream=True）

## 🔗 更多资源

- **详细使用说明**: 查看 `USAGE.md`
- **官方文档**: https://docs.ultralytics.com/
- **示例脚本**: `scripts/` 文件夹
- **社区支持**: https://community.ultralytics.com/

## ❓ 常见问题

### Q: 如何检测我自己的图像？

```python
# 方法1: 使用脚本（推荐）
poetry run python scripts/detect_image.py

# 方法2: 使用命令行
poetry run yolo predict model=yolo11n.pt source=/path/to/your/image.jpg

# 方法3: 修改脚本
# 编辑 scripts/quickstart.py，将图像路径改为你的图像
```

### Q: 如何使用摄像头？

```bash
poetry run yolo predict model=yolo11n.pt source=0 show=True
```

### Q: 模型下载很慢怎么办？

首次运行时会自动下载模型（约 5-50MB），请耐心等待。下载后会缓存在本地，之后使用不需要再次下载。

### Q: 如何训练自己的模型？

参考 `scripts/train_model.py` 中的示例，需要准备 YOLO 格式的数据集。

## 🎓 学习路径

1. **初学者**: 从 `quickstart.py` 开始
2. **进阶**: 尝试 `detect_image.py` 和 `detect_video.py`
3. **高级**: 查看 `advanced_examples.py`
4. **专家**: 学习 `train_model.py` 训练自定义模型

开始你的 YOLO 之旅吧！🚀

# 使用 Apple Silicon GPU (MPS) 训练 YOLO 模型

## 系统要求

- ✅ Apple Silicon Mac (M1/M2/M3)
- ✅ PyTorch 2.8.0 (支持 MPS)
- ✅ macOS 12.3 或更高版本

## 设备检测状态

当前系统支持 **Apple Silicon GPU (MPS)** 🚀

## 训练脚本

### 1. 完整训练（100 epochs）

使用 `start_training.py` 进行完整训练：

```bash
# 自动使用 MPS GPU 训练
poetry run python scripts/start_training.py
```

**特点：**

- ✅ 自动检测并使用 MPS GPU
- ✅ 100 epochs 完整训练
- ✅ 训练集：25,703 张图片
- ✅ 验证集：6,425 张图片
- ✅ 批次大小：16
- ✅ 图像大小：640x640

### 2. 快速测试（3 epochs）

使用 `test_mps_training.py` 快速测试 GPU 是否正常：

```bash
# 测试 MPS GPU 训练（仅3轮）
poetry run python scripts/test_mps_training.py
```

**特点：**

- ✅ 快速验证 MPS 是否工作
- ✅ 仅训练 3 epochs
- ✅ 小批次：8
- ✅ 适合测试环境配置

## 设备自动检测逻辑

脚本会按以下优先级自动检测设备：

1. **MPS** (Apple Silicon GPU) - 🚀 最快
2. **CUDA** (NVIDIA GPU) - 🚀 次快
3. **CPU** - ⚠️ 最慢

## 训练性能对比

| 设备         | 预计训练时间 | 推荐批次大小 |
| ------------ | ------------ | ------------ |
| MPS (M1 Max) | ~8-12 小时   | 16-32        |
| CPU (M1 Max) | ~40-60 小时  | 8-16         |

## 训练输出

训练完成后，模型和日志保存在：

```
runs/train/person_detection/
├── weights/
│   ├── best.pt      # 最佳模型（验证集性能最好）
│   └── last.pt      # 最后一轮模型
├── results.png      # 训练曲线图
├── confusion_matrix.png  # 混淆矩阵
└── ...
```

## 使用训练好的模型

### 图片检测

```bash
poetry run python scripts/detect_image.py --source path/to/image.jpg
```

### 视频检测

```bash
poetry run python scripts/detect_video.py --source path/to/video.mp4
```

### 批量检测

```bash
poetry run python scripts/batch_detect.py --source path/to/images/
```

## 监控训练进度

训练过程中可以查看：

1. **终端输出**：实时显示 loss、mAP 等指标
2. **TensorBoard**（如果启用）：可视化训练过程
3. **results.png**：训练完成后查看完整训练曲线

## 常见问题

### Q: 如何确认正在使用 GPU？

A: 查看训练日志开头，会显示：

```
device: Apple Silicon GPU (MPS) - 🚀 GPU 加速
```

### Q: MPS 训练比 CPU 快多少？

A: 在 M1 Max 上，MPS 通常比 CPU 快 **4-6 倍**

### Q: 训练时内存不足怎么办？

A: 减小批次大小，例如：

- 将 `batch=16` 改为 `batch=8` 或 `batch=4`

### Q: 如何恢复中断的训练？

A: 修改 `start_training.py` 中的 `resume=True`

## 性能优化建议

1. **使用 MPS**：确保使用 GPU 而不是 CPU
2. **合适的批次大小**：M1 Max 建议 16-32
3. **关闭缓存**：`cache=False` 节省内存
4. **使用 AMP**：`amp=True` 自动混合精度训练
5. **多进程加载**：`workers=8` 加速数据加载

## 下一步

训练完成后：

1. 查看训练结果：`runs/train/person_detection/results.png`
2. 验证模型：`poetry run python scripts/validate_model.py`
3. 测试检测：`poetry run python scripts/detect_image.py`

---

**提示**：首次训练建议先运行 `test_mps_training.py` 验证环境配置正确。

## 🎥 硬件设备部署指南（GStreamer 推流）

### 系统要求

- ✅ Ubuntu 18.04 或更高版本（树莓派、Jetson Nano 等）
- ✅ Python 3.11+
- ✅ GStreamer 1.0+
- ✅ 摄像头设备

### 在硬件设备上的完整部署步骤

#### 1. 安装系统依赖

```bash
# 更新系统包列表
sudo apt-get update

# 安装 GStreamer 核心组件和插件
sudo apt-get install -y \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev

# 安装其他必要的库
sudo apt-get install -y \
    python3-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libatlas-base-dev \
    gfortran
```

#### 2. 验证 GStreamer 安装

```bash
# 检查 GStreamer 版本
gst-launch-1.0 --version

# 测试 GStreamer 是否正常工作
gst-launch-1.0 videotestsrc ! autovideosink
```

如果看到测试视频窗口，说明 GStreamer 安装成功。

#### 3. 安装支持 GStreamer 的 OpenCV

卸载标准的 opencv-python 并安装支持 GStreamer 的版本：

```bash
# 进入项目目录
cd /path/to/yolo-detect

# 激活 Poetry 虚拟环境
poetry shell

# 卸载标准的 opencv-python
pip uninstall opencv-python opencv-python-headless

# 安装支持 GStreamer 的 opencv-python（从源码编译）
# 注意：这个过程可能需要 30-60 分钟
pip install opencv-contrib-python

# 或者使用预编译的支持 GStreamer 的版本（推荐）
pip install opencv-python-headless --no-binary opencv-python-headless
```

**推荐方法**：使用 `opencv-contrib-python`，它通常包含 GStreamer 支持：

```bash
pip uninstall opencv-python
pip install opencv-contrib-python
```

#### 4. 验证 OpenCV 的 GStreamer 支持

```bash
# 在 Python 中检查
poetry run python -c "import cv2; print('GStreamer:', cv2.getBuildInformation().find('GStreamer') > 0)"
```

如果输出 `GStreamer: True`，说明 OpenCV 支持 GStreamer。

#### 5. 安装项目依赖

```bash
# 安装 Poetry（如果还没有）
curl -sSL https://install.python-poetry.org | python3 -

# 安装项目依赖
poetry install

# 验证所有依赖
poetry run python -c "import cv2, ultralytics, lap; print('✅ 所有依赖安装成功')"
```

#### 6. 配置摄像头权限

```bash
# 将当前用户添加到 video 组
sudo usermod -a -G video $USER

# 重新登录以使权限生效
# 或者运行: newgrp video
```

#### 7. 测试推流功能

```bash
# 运行推流测试
poetry run python test/test_push.py
```

### 常见问题排查

#### 问题 1: GStreamer 推流初始化失败

**错误信息：**

```
[推流模块] | WARNING | GStreamer 推流初始化失败，将使用替代方案
```

**解决方案：**

1. 检查 OpenCV 是否支持 GStreamer：

```bash
poetry run python -c "import cv2; print(cv2.getBuildInformation())" | grep -i gstreamer
```

2. 如果显示 `NO`，需要重新安装支持 GStreamer 的 OpenCV（参考步骤 3）

3. 验证 GStreamer 管道是否正确：

```bash
# 测试视频源到 UDP 推流
gst-launch-1.0 videotestsrc ! videoconvert ! x264enc ! rtph264pay ! udpsink host=127.0.0.1 port=5004
```

#### 问题 2: 模块 'cv2' 未找到

**错误信息：**

```
ModuleNotFoundError: No module named 'cv2'
```

**解决方案：**

```bash
poetry install
poetry run pip install opencv-contrib-python
```

#### 问题 3: 模块 'lap' 未找到

**解决方案：**

```bash
poetry install
```

确保 `pyproject.toml` 中包含 `lap>=0.5.12` 依赖。

#### 问题 4: 摄像头无法打开

**解决方案：**

1. 检查摄像头设备：

```bash
ls -l /dev/video*
```

2. 测试摄像头：

```bash
# 使用 GStreamer 测试
gst-launch-1.0 v4l2src device=/dev/video0 ! videoconvert ! autovideosink

# 使用 OpenCV 测试
poetry run python -c "import cv2; cap = cv2.VideoCapture(0); print('摄像头:', cap.isOpened())"
```

3. 检查权限：

```bash
sudo chmod 666 /dev/video0
```

### 性能优化建议

#### 1. 调整推流参数

编辑 `test/test_push.py` 或相应脚本：

```python
streamer = PushStreamer(
    model_path="runs/train/person_detection/weights/best.pt",
    host="your-server-ip",
    port=5004,
    video_width=640,      # 降低分辨率以提高性能
    video_height=480,
    fps=30,               # 调整帧率
    bitrate=500,          # 调整比特率（kbps）
    headless=True         # 无头模式（不显示窗口）
)
```

#### 2. 使用更小的 YOLO 模型

```python
# 使用 nano 模型以提高速度
model_path="models/yolo11n.pt"
```

#### 3. 降低检测频率

每隔几帧检测一次，而不是每帧都检测。

### 接收推流

在接收端（如服务器或另一台设备）：

```bash
# 使用 GStreamer 接收 UDP 流
gst-launch-1.0 -v udpsrc port=5004 ! \
    application/x-rtp,encoding-name=H264,payload=96 ! \
    rtph264depay ! h264parse ! avdec_h264 ! \
    videoconvert ! autovideosink

# 或使用 VLC 播放器
vlc udp://@:5004

# 或使用 FFmpeg 接收
ffmpeg -i udp://127.0.0.1:5004 -c copy output.mp4
```

### 系统服务配置（可选）

如果需要开机自启动推流服务：

```bash
# 创建 systemd 服务
sudo cp service/yolo-streaming.service /etc/systemd/system/

# 编辑服务文件，修改路径
sudo nano /etc/systemd/system/yolo-streaming.service

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable yolo-streaming.service
sudo systemctl start yolo-streaming.service

# 查看服务状态
sudo systemctl status yolo-streaming.service
```

### 参考资源

- **GStreamer 官方文档**: https://gstreamer.freedesktop.org/documentation/
- **OpenCV + GStreamer**: https://docs.opencv.org/master/d0/da7/videoio_overview.html
- **YOLO 实时推流**: 查看 `service/push_streamer.py` 源码

---

**提示**：在硬件设备上部署时，建议先在本地测试推流功能，确保所有依赖都正确安装后再部署到生产环境，
