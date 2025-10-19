# 网络摄像头实时检测使用指南

## 📹 训练完成后使用网络摄像头进行实时检测

### 一、快速开始

训练完成后，最简单的使用方式：

```bash
poetry run python scripts/webcam_detect.py
```

这将：

- 自动加载训练好的最佳模型 (`runs/train/person_detection/weights/best.pt`)
- 打开默认摄像头
- 实时显示检测结果
- 按 `q` 键退出

---

### 二、命令行参数

#### 1. 基本检测

```bash
# 使用默认设置
poetry run python scripts/webcam_detect.py

# 指定模型路径
poetry run python scripts/webcam_detect.py --model runs/train/person_detection/weights/best.pt

# 调整置信度阈值（0-1之间，越高越严格）
poetry run python scripts/webcam_detect.py --conf 0.5

# 指定设备（mps for Mac, cuda for GPU, cpu for CPU）
poetry run python scripts/webcam_detect.py --device mps
```

#### 2. 保存检测视频

```bash
# 保存检测结果视频
poetry run python scripts/webcam_detect.py --save
```

#### 3. 启用目标跟踪

```bash
# 启用目标跟踪（给每个检测对象分配ID）
poetry run python scripts/webcam_detect.py --track
```

#### 4. 完整参数示例

```bash
poetry run python scripts/webcam_detect.py \
  --model runs/train/person_detection/weights/best.pt \
  --conf 0.5 \
  --iou 0.45 \
  --device mps \
  --save \
  --track
```

---

### 三、Python 代码调用

如果你想在自己的代码中使用：

#### 方式 1: 导入函数

```python
from scripts.webcam_detect import webcam_detect

# 基本检测
webcam_detect(
    model_path="runs/train/person_detection/weights/best.pt",
    conf=0.5,
    device="mps"
)

# 带目标跟踪
from scripts.webcam_detect import webcam_detect_with_tracking

webcam_detect_with_tracking(
    model_path="runs/train/person_detection/weights/best.pt",
    conf=0.5,
    device="mps"
)
```

#### 方式 2: 直接使用 Ultralytics API

```python
from ultralytics import YOLO
import cv2

# 加载训练好的模型
model = YOLO("runs/train/person_detection/weights/best.pt")

# 网络摄像头检测
results = model.predict(
    source=0,      # 0表示默认摄像头
    conf=0.5,      # 置信度阈值
    show=True,     # 显示结果
    stream=True,   # 流式处理
    device="mps"   # Mac GPU加速
)

# 逐帧处理
for result in results:
    # 在这里可以添加自定义处理逻辑
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
```

---

### 四、参数说明

| 参数       | 说明             | 默认值                                        | 示例                              |
| ---------- | ---------------- | --------------------------------------------- | --------------------------------- |
| `--model`  | 模型路径         | `runs/train/person_detection/weights/best.pt` | `--model models/yolo11n.pt`       |
| `--conf`   | 置信度阈值 (0-1) | `0.25`                                        | `--conf 0.5`                      |
| `--iou`    | IOU 阈值 (0-1)   | `0.45`                                        | `--iou 0.5`                       |
| `--device` | 推理设备         | `mps`                                         | `--device cuda` 或 `--device cpu` |
| `--save`   | 保存检测视频     | `False`                                       | `--save`                          |
| `--track`  | 启用目标跟踪     | `False`                                       | `--track`                         |

---

### 五、常见问题

#### 1. 如何选择使用哪个模型？

训练完成后会生成两个模型：

- **`best.pt`**: 验证集上表现最好的模型（推荐使用）
- **`last.pt`**: 最后一轮训练的模型

```bash
# 使用最佳模型（推荐）
poetry run python scripts/webcam_detect.py --model runs/train/person_detection/weights/best.pt

# 使用最后一轮模型
poetry run python scripts/webcam_detect.py --model runs/train/person_detection/weights/last.pt
```

#### 2. 置信度阈值如何设置？

- **0.25-0.3**: 检测更多目标，但可能有误检
- **0.5**: 平衡检测数量和准确性（推荐）
- **0.7-0.9**: 只检测高置信度目标，可能漏检

```bash
# 严格检测（减少误检）
poetry run python scripts/webcam_detect.py --conf 0.7

# 宽松检测（检测更多目标）
poetry run python scripts/webcam_detect.py --conf 0.3
```

#### 3. 如何使用其他摄像头？

默认使用摄像头 0，如果有多个摄像头，需要修改代码：

```python
# 在 webcam_detect.py 中修改
results = model.predict(
    source=1,  # 改为 1、2 等来使用其他摄像头
    ...
)
```

#### 4. 检测速度太慢怎么办？

1. **确保使用 GPU 加速**:

   ```bash
   poetry run python scripts/webcam_detect.py --device mps  # Mac
   poetry run python scripts/webcam_detect.py --device cuda # NVIDIA GPU
   ```

2. **使用更小的模型**:
   如果训练时使用的是 `yolo11m` 或 `yolo11l`，可以重新用 `yolo11n` 或 `yolo11s` 训练

3. **降低置信度阈值以减少后处理**:
   ```bash
   poetry run python scripts/webcam_detect.py --conf 0.5
   ```

#### 5. 如何保存检测结果？

```bash
# 保存检测视频
poetry run python scripts/webcam_detect.py --save
```

保存位置会在控制台输出，通常在 `runs/detect/predict/` 目录下。

---

### 六、进阶使用

#### 1. 同时检测多个视频源

```python
from ultralytics import YOLO
from threading import Thread

def detect_camera(camera_id, model_path):
    model = YOLO(model_path)
    results = model.predict(source=camera_id, show=True, stream=True)
    for r in results:
        pass

# 启动多个摄像头检测
model_path = "runs/train/person_detection/weights/best.pt"
Thread(target=detect_camera, args=(0, model_path)).start()
Thread(target=detect_camera, args=(1, model_path)).start()
```

#### 2. 添加自定义处理逻辑

```python
from ultralytics import YOLO
import cv2

model = YOLO("runs/train/person_detection/weights/best.pt")
results = model.predict(source=0, stream=True, device="mps")

for result in results:
    boxes = result.boxes

    # 自定义处理
    if len(boxes) > 0:
        print(f"检测到 {len(boxes)} 个目标")

        # 获取检测框信息
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            xyxy = box.xyxy[0].cpu().numpy()

            print(f"类别: {model.names[cls]}, 置信度: {conf:.2f}")

            # 在这里添加你的逻辑
            # 例如：触发警报、保存截图、发送通知等

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
```

#### 3. 检测特定类别

如果你只想检测特定类别（例如只检测人）：

```python
from ultralytics import YOLO

model = YOLO("runs/train/person_detection/weights/best.pt")

# 只检测类别 0（假设 0 是 person）
results = model.predict(
    source=0,
    classes=[0],  # 只检测类别 0
    show=True,
    stream=True
)

for result in results:
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
```

---

### 七、性能优化建议

1. **使用 GPU 加速** (Mac: MPS, Windows/Linux: CUDA)
2. **选择合适大小的模型** (nano < small < medium < large)
3. **调整输入图像大小** (默认 640，可以降低到 320 以提升速度)
4. **使用 FP16 半精度推理** (需要 GPU 支持)
5. **关闭不需要的功能** (如不需要保存视频就不要开启 `--save`)

---

## 🎉 总结

训练完成后使用网络摄像头检测非常简单：

```bash
# 最简单的方式
poetry run python scripts/webcam_detect.py

# 推荐配置
poetry run python scripts/webcam_detect.py --model runs/train/person_detection/weights/best.pt --conf 0.5 --device mps
```

按 `q` 键退出检测，祝你使用愉快！🚀
