# Video Cutter

一个基于 Python + PyQt6 的视频剪辑工具，支持从多个视频中按时间段截取片段。

## 功能特性

- 📁 支持多种视频格式 (mkv, mp4, MOV, avi 等)
- 📊 从 Excel 表格读取片段信息和时间段
- ✂️ 精确时间截取
- 🎚️ 三种输出质量等级（高/中/低）
- 📈 实时进度显示和剩余时间估算
- ⏸️ 支持暂停/继续/停止
- 📝 任务日志记录
- 🖥️ 跨平台支持 (Windows/macOS/Linux)
- 📦 可打包成独立可执行文件（内置 ffmpeg）

## 安装

### 方式一：从源码运行

1. 安装 Python 依赖：
```bash
pip install -r requirements.txt
```

2. 安装 ffmpeg：
- **Ubuntu/Debian**: `sudo apt install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Windows**: 从 https://ffmpeg.org 下载并添加到 PATH

3. 运行程序：
```bash
python main.py
```

### 方式二：打包为可执行文件

打包后的程序**内置 ffmpeg**，用户无需安装任何依赖。

#### 1. 下载 ffmpeg 二进制文件

```bash
# 下载当前平台的 ffmpeg
python download_ffmpeg.py

# 或下载所有平台（用于跨平台打包）
python download_ffmpeg.py --platform all
```

#### 2. 安装打包工具

```bash
pip install pyinstaller
```

#### 3. 打包

```bash
# Windows (生成单个 exe)
python build.py

# macOS (生成 .app)
python build.py

# Linux (生成可执行文件)
python build.py
```

打包选项：
```bash
python build.py --clean        # 清理后重新打包
python build.py --dir          # 打包为目录（启动更快）
python build.py --console      # 带控制台窗口（调试用）
```

#### 4. 输出

打包完成后，可执行文件在 `dist/` 目录：
- **Windows**: `dist/视频剪辑工具.exe`
- **macOS**: `dist/视频剪辑工具.app`
- **Linux**: `dist/视频剪辑工具`

## 使用方法

1. 运行程序
2. 选择原视频文件夹（包含视频文件，文件名为开始时间格式）
3. 选择 Excel 表格文件
4. 设置输出文件夹和质量等级
5. 点击"开始剪辑"

## Excel 表格格式

表格应包含以下列：
- **起始时间点**：格式 `起 yyyy-mm-dd hh:mm:ss 止 yyyy-mm-dd hh:mm:ss`
- **问题描述**：片段命名（作为输出文件名）

示例：
| 起始时间点 | 问题描述 |
|-----------|---------|
| 起 2026-01-15 10:45:02 止 2026-01-15 11:30:00 | 上午会议记录 |

## 视频文件命名

视频文件应按开始时间命名：
- `2026-01-15 10-45-02.mkv`
- `2026.01.15_10.45.02.mp4`

## 输出质量

| 等级 | 码率 | 说明 |
|-----|------|------|
| 高 | 100% | 与原视频相同 |
| 中 | 50% | 文件体积减半 |
| 低 | 30% | 最小文件体积 |

## 项目结构

```
video-cutter/
├── main.py              # 程序入口
├── build.py             # 打包脚本
├── download_ffmpeg.py   # ffmpeg 下载脚本
├── requirements.txt     # Python 依赖
├── README.md            # 本说明文件
├── src/
│   ├── gui.py           # PyQt6 主界面
│   ├── video_processor.py  # ffmpeg 视频处理
│   ├── excel_parser.py  # Excel 解析
│   ├── ffmpeg_manager.py   # ffmpeg 路径管理
│   └── utils.py         # 工具函数
├── ffmpeg_bin/          # ffmpeg 二进制文件（打包时）
│   ├── windows/
│   ├── macos/
│   └── linux/
├── assets/              # 资源文件
└── tests/               # 测试文件
```

## 开发

```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行
python main.py

# 检查 ffmpeg
python -c "from src.ffmpeg_manager import check_ffmpeg; print(check_ffmpeg())"

# 测试下载 ffmpeg
python download_ffmpeg.py --check-ffmpeg
```

## 分发

将 `dist/` 目录中的可执行文件分发给用户：
- **Windows**: 直接发送 `视频剪辑工具.exe`
- **macOS**: 压缩 `视频剪辑工具.app` 为 zip
- **Linux**: 发送可执行文件

用户无需安装 Python、ffmpeg 或任何其他依赖。

## License

MIT
