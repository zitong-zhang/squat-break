# Squat Break

macOS 久坐提醒工具。屏幕活跃时计时，到点弹出全屏窗口，用摄像头检测你完成蹲起后才让你继续工作。

## 功能

- 屏幕活跃时计时，锁屏自动暂停
- 到时间弹出全屏窗口，强制打断工作
- 自动打开 MacBook 摄像头，通过 MediaPipe 姿态检测识别蹲起动作
- 默认每 40 分钟提醒，每次 5 个蹲起，可自定义
- 支持自定义提醒间隔和蹲起数量（`hi 40 5`）
- 输入 `time` 查看已工作时长和下次蹲起倒计时
- 输入 `pause` 暂停计时，`resume` 恢复
- 输入 `end` 结束时显示本次工作总时长和蹲起次数
- 按 Esc 可随时跳过

## 环境要求

- macOS 12+
- Python 3.9+
- 摄像头权限

## 安装

```bash
git clone https://github.com/zz19941127/squat-break.git
cd squat-break
pip install -r requirements.txt
```

## 使用

```bash
# 默认每 40 分钟提醒，每次 5 个蹲起
python squat_break.py

# 自定义间隔，比如每 30 分钟
python squat_break.py 30

# 自定义间隔和蹲起数量，比如每 40 分钟 5 个蹲起
python squat_break.py 40 5
```

推荐配置 shell alias 一键启动：

```bash
# 添加到 ~/.zshrc
alias hi='python /path/to/squat-break/squat_break.py'
```

然后直接在终端输入 `hi` 即可启动。输入 `end` 结束并查看工作统计。

### 运行中命令

| 命令 | 说明 |
|------|------|
| `time` | 查看已工作时长和下次蹲起倒计时 |
| `pause` | 暂停计时 |
| `resume` | 恢复计时 |
| `end` | 结束并查看统计 |

## 摄像头权限

首次运行时 macOS 会请求摄像头权限，需要授权给运行 Python 的终端应用（如 Terminal.app、iTerm2 等）。

如果使用 Anaconda Python，权限需要在「系统设置 → 隐私与安全性 → 摄像头」中授权 `/opt/anaconda3/bin/python3`。

## 工作原理

1. 主进程每秒检测 stdin 命令，每 5 秒检测屏幕状态，活跃时累加计时
2. 计时到期后启动子进程显示全屏 UI
3. UI 通过 MediaPipe PoseLandmarker 实时检测人体姿态
4. 自动校准站立基线，检测身体下降或离开画面即判定为蹲下
5. 完成目标次数后自动关闭

## 文件说明

```
squat_break.py    # 主入口，计时器 + 屏幕状态检测 + 命令处理
_ui_window.py     # 全屏 UI，摄像头画面 + 蹲起计数
ui.py             # UI 启动封装
detector.py       # 蹲起检测状态机（独立模块，可单独测试）
test_detector.py  # 检测模块单元测试
models/           # MediaPipe 姿态模型
requirements.txt  # 依赖列表
```

## 运行测试

```bash
python test_detector.py
```

## License

MIT
