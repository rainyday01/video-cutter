# Video Cutter

一个基于 Python + PyQt6 的视频剪辑工具，支持从多个视频中按时间段截取片段。

## 功能特性

- 📁 支持多种视频格式 (mkv, mp4, MOV, avi 等)
- 📊 从 Excel 表格读取片段信息和时间段
- ✂️ 精确时间截取
- 🎚️ 三种输出质量等级（高/中/低）
- 📈 实时进度显示和剩余时间估算
- ⏸️ 支持暂停/继续/停止
- 📝 任务日志记录（含 Excel 解析调试日志）
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

### 方式二：下载发布版本

从 [Releases](https://github.com/rainyday01/video-cutter/releases) 页面下载对应平台的可执行文件。

### 方式三：打包为可执行文件

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
- **Windows**: `dist/VideoCutter.exe`
- **macOS**: `dist/VideoCutter.app`
- **Linux**: `dist/VideoCutter`

## 使用方法

1. 运行程序
2. 选择原视频文件夹（包含视频文件，文件名为开始时间格式）
3. 选择 Excel 表格文件
4. 设置输出文件夹和质量等级
5. 点击"开始剪辑"

## Excel 表格格式

表格应包含以下列：
- **时间列**：支持多种表头名称（起止时间点、起始时间、开始时间等）
- **描述列**：支持多种表头名称（问题描述、描述、标题等）

### 时间格式支持

时间列支持多种格式：

```
起 2026-01-15 10:45:02 止 2026-01-15 11:30:00     # 标准格式
起 2026/01/15 10:45:02 止 2026/01/15 11:30:00     # 斜杠日期
起 2026.01.15 10:45:02 止 2026.01.15 11:30:00     # 点号日期
```

**分隔符支持**：
- 空格分隔
- 换行符分隔（`\n`、`\r\n`）
- 无分隔符直接连接（`起xxx止xxx`）

### 示例表格

| 问题描述 | 起止时间点 |
|---------|-----------|
| 上午会议记录 | 起 2026-01-15 10:45:02 止 2026-01-15 11:30:00 |
| 下午讨论 | 起 2026-01-15 14:00:00 止 2026-01-15 15:30:00 |

### 调试与故障排查

### 日志文件

程序运行时会在**程序所在目录**生成 `log.txt` 日志文件，记录：
- Excel 解析过程
- 视频文件匹配结果
- FFmpeg 执行状态
- 错误和异常信息

**日志级别**：
- `DEBUG` - 详细调试信息（文件解析、FFmpeg 每行输出等）
- `INFO` - 正常操作信息（任务开始、完成等）
- `WARNING` - 警告信息
- `ERROR` - 错误信息

### 常见问题

| 问题 | 可能原因 | 解决方法 |
|------|---------|---------|
| 视频无法匹配 | 文件名格式不支持 | 检查文件名是否符合支持的格式 |
| FFmpeg 失败 | 输出路径有特殊字符 | 尝试更换输出目录 |
| Excel 解析失败 | 表头或时间格式不对 | 使用 `test_excel_parser.py` 诊断 |
| 程序崩溃 | 未知错误 | 查看 `log.txt` 并提交 Issue |

### 反馈问题

如果遇到问题：
1. 查看 `log.txt` 日志文件
2. 在 [GitHub Issues](https://github.com/rainyday01/video-cutter/issues) 提交问题
3. 附上日志相关内容（可去除敏感信息）

### 请求新功能

如果需要支持新的视频文件名格式或其他功能：
1. 在 [GitHub Issues](https://github.com/rainyday01/video-cutter/issues) 新建 Issue
2. 标题格式：`[功能请求] 支持xxx视频命名格式`
3. 提供示例文件名和期望的解析结果

如果 Excel 解析有问题，可以使用测试脚本诊断：

```bash
python test_excel_parser.py 你的文件.xlsx
```

脚本会输出详细的解析日志，帮助定位问题。

## 视频文件命名

程序通过解析视频文件名来确定视频的开始时间，支持以下格式：

### OBS 录制格式（推荐）

使用 `-` 或 `.` 作为日期和时间分隔符：

| 格式 | 示例 |
|------|------|
| yyyy-mm-dd hh-mm-ss | `2026-01-15 10-45-02.mkv` |
| yyyy.mm.dd hh.mm.ss | `2026.01.15 10.45.02.mp4` |
| yyyy-mm-dd_hh-mm-ss | `2026-01-15_10-45-00.MOV` |
| yyyy.mm.dd_hh.mm.ss | `2026.01.15_10.45.00.avi` |

**注意**：此格式要求月份、日期、时、分、秒必须是两位数（如 `01` 而非 `1`）。

### 紧凑格式（通用）

文件名中包含 `yyyymmdd_hhmmss` 格式的时间字符串：

| 格式 | 示例 |
|------|------|
| yyyymmdd_hhmmss | `20260201_090101.mp4` |
| 前缀_yyyymmdd_hhmmss | `abcxyz_20260201_090101.mp4` |
| 前缀_yyyymmdd_hhmm | `REC_20260215_143022.mp4` |

**特点**：
- 支持任意前缀字符（如设备名、录制类型等）
- 时间字符串前有 `_` 分隔符

### 行车记录仪/手机录制格式

使用 `/` 作为日期分隔符，`:` 作为时间分隔符：

| 格式 | 示例（文件路径） |
|------|------|
| yyyy/m/d h:mm:ss | `D:/videos/2026/2/1 16:01:33.mp4` |
| yyyy/mm/dd hh:mm:ss | `/storage/2026/02/01 16:01:33.mkv` |
| yyyy/m/d h:mm | `C:/dashcam/2026/2/1 16:01.mov` |

**特点**：
- 支持月、日、时的一位数表示（如 `2/1` 表示 2月1日，`8:30` 表示 8点30分）
- **日期作为目录结构**：日期部分（年/月/日）通常是目录路径，文件名只有时间部分
- 程序会从**完整路径**中提取日期时间信息

### 支持的视频扩展名

`.mkv` `.mp4` `.mov` `.avi` `.wmv` `.flv` `.webm`

### 文件命名要求

1. **文件名必须包含完整的日期时间信息**
2. 时间部分表示视频录制的**开始时间**
3. 程序会自动匹配：如果剪辑时间段在某个视频的开始时间之后、下一个视频开始时间之前，则使用该视频

### 无法识别的文件名

如果视频文件名不符合上述格式，程序将无法自动识别。请：
1. 重命名视频文件以符合上述格式
2. 或在 [GitHub Issues](https://github.com/rainyday01/video-cutter/issues) 提交新格式支持请求

## 输出质量

| 等级 | 码率 | 说明 |
|-----|------|------|
| 高 | 100% | 与原视频相同 |
| 中 | 50% | 文件体积减半 |
| 低 | 30% | 最小文件体积 |

## 时间偏移设置

在输出设置中可以配置全局时间偏移，用于调整剪辑片段的起止时间：

| 设置 | 范围 | 说明 |
|-----|------|------|
| 起始时间偏移 | ±60秒 | 正数=提前开始，负数=延后开始 |
| 结束时间偏移 | ±60秒 | 正数=延后结束，负数=提前结束 |
| 最小时长 | 1-300秒 | 偏移后时长不足时自动延长 |

**示例**：
- 原片段: 10:00:00 ~ 10:00:05 (5秒)
- 设置: 起始+10秒, 结束+10秒, 最小10秒
- 结果: 09:59:50 ~ 10:00:15 → 自动延长到 09:59:50 ~ 10:00:00 (10秒)

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
│   ├── excel_parser.py  # Excel 解析（含调试日志）
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

# 测试 Excel 解析
python test_excel_parser.py test.xlsx

# 测试下载 ffmpeg
python download_ffmpeg.py --check-ffmpeg
```

## 更新日志

### v1.1.0
- 📹 新增紧凑格式支持（`abcxyz_20260201_090101.mp4`）
- 🎨 添加程序图标（剪刀图标）
- 🖥️ 程序图标在任务栏和窗口标题栏正确显示

### v1.0.9
- 📹 新增行车记录仪视频命名格式支持（`2026/2/1 16:01:33`）
- 📖 详细文档说明支持的视频文件名格式
- 📖 添加调试与故障排查章节
- 📖 添加 Issue 反馈指南

### v1.0.8
- 🔧 重写 FFmpeg 输出读取逻辑
- 🧵 使用独立线程读取 stderr
- ⏱️ 添加空行时的短暂延迟避免 CPU 占用
- 📝 更多日志细节

### v1.0.7
- 📝 增强 FFmpeg 执行过程日志
- 🔍 每隔100行输出进度状态
- 🔍 每10%进度记录一次
- 🔍 检测进程是否提前结束

### v1.0.6
- 🐛 **修复关键 bug**: `WorkerThread` 缺少 `current_task` 属性导致程序崩溃
- 这是导致"只完成一个任务就退出"的真正原因！

### v1.0.5
- 📝 增强 FFmpeg 执行日志（记录每一行输出）
- 🔧 添加 Qt 消息处理器捕获 Qt 内部错误
- 🛡️ 添加全局异常钩子和线程异常钩子
- 🐛 修复可能的 readline() 异常处理

### v1.0.4
- 📝 新增详细日志文件 `log.txt`（程序同目录）
- 🐛 修复 `_stopped` 标志未重置导致后续任务失败
- 🛡️ 增强异常处理和日志追踪
- 📊 显示每个任务的匹配结果

### v1.0.3
- 🐛 修复 duration=0 时无法匹配视频的问题
- 🐛 修复程序只处理一个任务就退出的问题
- 📝 添加详细日志显示视频匹配过程
- 🛡️ 添加完整异常处理防止单任务失败导致崩溃

### v1.0.2
- 🪟 修复 Windows 平台命令行窗口弹出问题
- 🛠️ 修复主窗口意外退出问题
- ⏱️ 新增全局时间偏移设置
  - 起始时间偏移 (±60秒)
  - 结束时间偏移 (±60秒)  
  - 最小时长保证 (默认10秒)

### v1.0.1
- 📊 支持"起止时间点"等更多 Excel 表头格式
- 🔧 处理多种时间分隔符（换行、回车、无空格）
- 📝 添加详细解析日志便于调试
- 🛠️ 新增 `test_excel_parser.py` 测试脚本

### v1.0.0
- 🎉 初始发布
- ✂️ 基本视频剪辑功能
- 📊 Excel 表格导入
- 🖥️ 跨平台支持

## 分发

将 `dist/` 目录中的可执行文件分发给用户：
- **Windows**: 直接发送 `VideoCutter.exe`
- **macOS**: 压缩 `VideoCutter.app` 为 zip
- **Linux**: 发送可执行文件

用户无需安装 Python、ffmpeg 或任何其他依赖。

## License

MIT
