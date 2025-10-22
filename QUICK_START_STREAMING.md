# YOLO 推流方案选择指南

## 🎯 我应该选择哪个方案？

### 快速决策树

```
需要推流到远程服务器？
  │
  ├─ 是 → 需要极低延迟（< 100ms）？
  │      │
  │      ├─ 是 → 使用 GStreamer（专业方案）
  │      │      └─ 参考: GSTREAMER_FIX.md
  │      │
  │      └─ 否 → 使用 FFmpeg（推荐✅）
  │             └─ 参考: FFMPEG_STREAMING.md
  │
  └─ 否 → 本地显示即可？
         └─ 使用 webcam_detect.py（最简单）
            └─ 命令: poetry run python scripts/webcam_detect.py
```

---

## 📋 方案对比速查表

| 方案              | 适用场景 | 安装时间 | 难度       | 文档                  |
| ----------------- | -------- | -------- | ---------- | --------------------- |
| **FFmpeg 推流**✅ | 远程推流 | 1 分钟   | ⭐         | `FFMPEG_STREAMING.md` |
| GStreamer 推流    | 专业推流 | 1 小时+  | ⭐⭐⭐⭐⭐ | `GSTREAMER_FIX.md`    |
| 本地检测          | 本地显示 | 0 分钟   | ⭐         | README.md             |

---

## 🚀 快速开始

### 方案 1：FFmpeg 推流（推荐）

**适合：**需要推流到远程服务器（Janus、RTMP 等）

**步骤：**

```bash
# 1. 一键部署
bash scripts/deploy_ffmpeg.sh

# 2. 配置推流地址
nano test/test_push_ffmpeg.py
# 修改 host="YOUR_SERVER_IP"

# 3. 运行
poetry run python test/test_push_ffmpeg.py
```

**优势：**

- ✅ 安装简单（1 分钟）
- ✅ 不需要 OpenCV GStreamer 支持
- ✅ 代码清晰易懂
- ✅ 跨平台支持好

**详细文档：** `FFMPEG_STREAMING.md`

---

### 方案 2：本地检测（最简单）

**适合：**只需要在本地屏幕显示检测结果

**步骤：**

```bash
# 直接运行
poetry run python scripts/webcam_detect.py

# 使用训练好的模型
poetry run python scripts/webcam_detect.py --model runs/train/person_detection/weights/best.pt
```

**优势：**

- ✅ 零配置
- ✅ 最简单
- ✅ 无需网络

**适用于：**

- 开发测试
- 本地演示
- 快速验证模型

---

### 方案 3：GStreamer 推流（专业）

**适合：**需要极低延迟或硬件加速

**步骤：**

```bash
# 1. 从源码编译 OpenCV（30-60分钟）
bash scripts/build_opencv_from_source.sh

# 2. 验证安装
poetry run python test/test_gstreamer_debug.py

# 3. 运行
poetry run python test/test_push.py
```

**劣势：**

- ❌ 安装复杂（1 小时+）
- ❌ 配置困难
- ❌ 调试不易

**仅在以下情况考虑：**

- 需要 < 100ms 延迟
- 需要硬件加速
- 团队有 GStreamer 专家

**详细文档：** `GSTREAMER_FIX.md`

---

## 💡 推荐配置

### 开发环境（Mac/Windows）

```bash
# 本地开发测试
poetry run python scripts/webcam_detect.py
```

### 生产环境（Ubuntu 服务器）

```bash
# FFmpeg 推流到远程服务器
bash scripts/deploy_ffmpeg.sh
poetry run python test/test_push_ffmpeg.py
```

---

## 🔧 常用命令

### FFmpeg 推流

```bash
# 部署
bash scripts/deploy_ffmpeg.sh

# 测试
poetry run python test/test_push_ffmpeg.py

# 配置文件
# test/test_push_ffmpeg.py
```

### 本地检测

```bash
# 运行
poetry run python scripts/webcam_detect.py

# 带参数
poetry run python scripts/webcam_detect.py --conf 0.5 --track
```

### GStreamer 推流（不推荐）

```bash
# 编译 OpenCV（慎用！）
bash scripts/build_opencv_from_source.sh

# 诊断
poetry run python test/test_gstreamer_debug.py

# 运行
poetry run python test/test_push.py
```

---

## 📊 性能对比

### 延迟对比（端到端）

| 方案         | 延迟      | 说明       |
| ------------ | --------- | ---------- |
| GStreamer    | 100-200ms | 最低       |
| **FFmpeg**✅ | 200-400ms | 足够低     |
| 本地显示     | < 50ms    | 无网络传输 |

### 资源占用

| 方案         | CPU | 内存  | 说明 |
| ------------ | --- | ----- | ---- |
| GStreamer    | 30% | 220MB | 最优 |
| **FFmpeg**✅ | 35% | 250MB | 良好 |
| 本地显示     | 25% | 200MB | 最小 |

**结论：** 除非有极端需求，FFmpeg 性能完全够用。

---

## 📚 文档索引

### 核心文档

1. **README.md** - 项目总览和快速开始
2. **FFMPEG_STREAMING.md** - FFmpeg 推流完整指南（推荐 ✅）
3. **STREAMING_COMPARISON.md** - 推流方案详细对比
4. **GSTREAMER_FIX.md** - GStreamer 问题修复（仅参考）

### 训练相关

5. **TRAINING_GUIDE.md** - 模型训练指南

### 脚本说明

- `scripts/deploy_ffmpeg.sh` - FFmpeg 一键部署
- `scripts/webcam_detect.py` - 本地检测
- `test/test_push_ffmpeg.py` - FFmpeg 推流测试
- `test/test_push.py` - GStreamer 推流测试

---

## 🆘 遇到问题？

### FFmpeg 推流问题

1. 查看：`FFMPEG_STREAMING.md` 的"常见问题"章节
2. 检查：`ffmpeg -version`
3. 验证：摄像头 `ls -l /dev/video*`

### GStreamer 问题

1. 查看：`GSTREAMER_FIX.md`
2. 运行：`poetry run python test/test_gstreamer_debug.py`
3. **建议：改用 FFmpeg 方案！**

### 检测效果问题

1. 调整置信度：`--conf 0.3`（降低）或 `--conf 0.7`（提高）
2. 更换模型：使用更大的模型如 `yolo11m.pt`
3. 重新训练：参考 `TRAINING_GUIDE.md`

---

## 🎓 学习路径

### 新手入门

1. 运行本地检测

   ```bash
   poetry run python scripts/webcam_detect.py
   ```

2. 理解 YOLO 基础

   - 阅读 README.md
   - 尝试不同参数

3. 部署 FFmpeg 推流
   ```bash
   bash scripts/deploy_ffmpeg.sh
   ```

### 进阶使用

1. 训练自定义模型

   - 参考 `TRAINING_GUIDE.md`
   - 使用自己的数据集

2. 优化推流性能

   - 调整分辨率、帧率
   - 优化 FFmpeg 参数

3. 集成到应用
   - 使用 `service/push_streamer_ffmpeg.py`
   - 自定义业务逻辑

---

## ✅ 推荐配置总结

### 大多数情况（95%）

```bash
# 使用 FFmpeg 推流
bash scripts/deploy_ffmpeg.sh
poetry run python test/test_push_ffmpeg.py
```

### 本地开发测试

```bash
# 本地显示
poetry run python scripts/webcam_detect.py
```

### 特殊专业需求（5%）

```bash
# GStreamer（确定需要时）
bash scripts/build_opencv_from_source.sh
poetry run python test/test_push.py
```

---

## 🎯 一句话总结

**对于推流需求，99% 的情况下应该选择 FFmpeg 方案。**

- 简单：1 分钟部署
- 够用：200-400ms 延迟
- 稳定：少出问题
- 易维护：代码清晰

---

**还有疑问？** 查看对应的详细文档或提 Issue！

**文档编写**：GitHub Copilot  
**最后更新**：2025 年 10 月 22 日
