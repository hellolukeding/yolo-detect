# 📹 macOS 摄像头权限问题解决方案

## 问题说明

错误信息：

```
OpenCV: not authorized to capture video (status 0), requesting...
OpenCV: camera failed to properly initialize!
ConnectionError: 1/1: 0... Failed to open 0
```

这是因为 **macOS 需要授予 Python/终端访问摄像头的权限**。

---

## 🔧 解决方案

### 方案 1：授予终端摄像头权限（推荐）⭐

#### 步骤：

1. **打开系统设置**

   - 点击左上角的 图标
   - 选择 "系统设置" (System Settings)

2. **进入隐私与安全**

   - 点击 "隐私与安全性" (Privacy & Security)
   - 在左侧找到 "摄像头" (Camera)

3. **授予终端权限**

   - 在右侧列表中找到你使用的终端应用：
     - **Terminal** (系统自带终端)
     - **iTerm2** (如果你使用 iTerm)
     - **VS Code** (如果从 VS Code 终端运行)
   - 勾选对应的应用以授予摄像头权限

4. **重启终端**
   - 完全关闭终端应用
   - 重新打开终端
   - 再次运行检测脚本

---

### 方案 2：使用 Python 直接运行（而不是通过 VS Code）

有时从 VS Code 内置终端运行会有权限问题，可以尝试：

```bash
# 在系统终端（Terminal.app 或 iTerm2）中运行
cd /Users/lukeding/Desktop/playground/2025/yolo-detect
poetry run python scripts/webcam_detect.py
```

---

### 方案 3：测试摄像头是否可用

创建一个简单的测试脚本来检查摄像头：

```python
import cv2

cap = cv2.VideoCapture(0)
if cap.isOpened():
    print("✅ 摄像头打开成功！")
    ret, frame = cap.read()
    if ret:
        print("✅ 可以读取摄像头画面！")
        cv2.imshow('Test', frame)
        cv2.waitKey(2000)
    else:
        print("❌ 无法读取摄像头画面")
else:
    print("❌ 无法打开摄像头")

cap.release()
cv2.destroyAllWindows()
```

---

### 方案 4：使用视频文件代替摄像头（临时方案）

如果暂时无法解决摄像头权限问题，可以先用视频文件测试：

```bash
# 下载测试视频
curl -o test_video.mp4 "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4"

# 使用视频文件进行检测
poetry run python scripts/detect_video.py
```

或者修改 `webcam_detect.py`，将 `source=0` 改为视频文件路径：

```python
results = model.predict(
    source="test_video.mp4",  # 使用视频文件
    conf=conf,
    ...
)
```

---

## 🎯 推荐操作步骤

### 第一步：检查当前权限状态

```bash
# 运行测试脚本检查摄像头
poetry run python scripts/test_camera.py
```

### 第二步：授予权限

1. 打开 **系统设置** > **隐私与安全性** > **摄像头**
2. 找到并勾选你使用的终端应用
3. **重启终端应用**

### 第三步：重新运行

```bash
poetry run python scripts/webcam_detect.py
```

---

## 📝 macOS 权限位置（不同版本）

### macOS Ventura (13.x) 及更新版本：

```
系统设置 → 隐私与安全性 → 摄像头
System Settings → Privacy & Security → Camera
```

### macOS Monterey (12.x) 及更早版本：

```
系统偏好设置 → 安全性与隐私 → 隐私 → 摄像头
System Preferences → Security & Privacy → Privacy → Camera
```

---

## ❓ 常见问题

### Q1: 授予权限后还是不行？

**A**: 确保完全关闭并重新打开终端应用（不只是关闭窗口）

### Q2: 找不到终端应用在列表中？

**A**: 尝试先运行一次脚本，系统会弹出权限请求对话框

### Q3: 使用的是 VS Code 内置终端？

**A**: 需要授予 **"Visual Studio Code"** 或 **"Code"** 应用摄像头权限

### Q4: 弹出权限请求但点了拒绝？

**A**: 进入系统设置手动添加权限，或重置隐私设置：

```bash
tccutil reset Camera
```

然后重新运行脚本

---

## 🔍 其他可能的问题

### 1. 检查摄像头是否被其他应用占用

```bash
# 检查是否有其他应用在使用摄像头
lsof | grep -i camera
```

关闭所有可能使用摄像头的应用（如 Zoom、FaceTime 等）

### 2. 尝试使用不同的摄像头索引

如果有多个摄像头设备：

```bash
# 修改脚本中的 source 参数
source=0  # 默认摄像头
source=1  # 第二个摄像头
source=2  # 第三个摄像头
```

### 3. 检查 OpenCV 安装

```bash
# 重新安装 opencv-python
poetry remove opencv-python
poetry add opencv-python
```

---

## ✅ 验证权限已授予

授予权限后，系统设置中应该能看到：

```
摄像头 (Camera)
  ☑ Terminal (或 iTerm2 / VS Code)
```

重启终端后，再次运行：

```bash
poetry run python scripts/webcam_detect.py
```

应该能看到摄像头窗口打开！🎉

---

## 🆘 仍然无法解决？

1. **重启电脑** - 有时权限更改需要重启才能生效
2. **使用系统终端** - 不要使用 VS Code 内置终端
3. **使用视频文件** - 作为临时替代方案测试模型
4. **检查 macOS 版本** - 确保系统是最新版本

---

需要更多帮助？请查看 [Apple 官方文档](https://support.apple.com/zh-cn/guide/mac-help/mchlf6d108da/mac)
