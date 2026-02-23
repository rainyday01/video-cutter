"""Main GUI for Video Cutter application."""
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar,
    QTextEdit, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QStatusBar, QToolBar
)
from PyQt6.QtGui import QAction, QIcon

from .excel_parser import parse_excel_clips, ClipDefinition
from .video_processor import VideoProcessor, VideoInfo, ClipTask, QualitySettings
from .utils import parse_video_filename, get_video_files
from .ffmpeg_manager import check_ffmpeg, check_ffprobe, get_ffmpeg_path, get_ffprobe_path


class WorkerThread(QThread):
    """Worker thread for video processing."""
    
    progress_updated = pyqtSignal(float)
    log_message = pyqtSignal(str)
    task_completed = pyqtSignal(str, bool)  # description, success
    all_completed = pyqtSignal()
    
    def __init__(
        self,
        processor: VideoProcessor,
        tasks: list[ClipTask],
        quality: QualitySettings,
        video_infos: list[VideoInfo]
    ):
        super().__init__()
        self.processor = processor
        self.tasks = tasks
        self.quality = quality
        self.video_infos = video_infos
        self._running = True
        self._paused = False
    
    def run(self):
        """Process all tasks."""
        # Assign video info to each task
        for task in self.tasks:
            if not self._running:
                break
            
            # Resume from paused state
            while self._paused and self._running:
                import time
                time.sleep(0.1)
            
            if not self._running:
                break
            
            # Find source video for this task
            task.video_info = self.processor.find_video_for_clip(
                self.video_infos, task.clip_start, task.clip_end
            )
            
            if task.video_info:
                self.processor.cut_clip(
                    task, self.quality,
                    progress_callback=lambda p: self.progress_updated.emit(p),
                    log_callback=lambda msg: self.log_message.emit(msg)
                )
                
                success = task.status == "completed"
                self.task_completed.emit(task.description, success)
            else:
                task.status = "failed"
                task.error = "找不到源视频"
                self.log_message.emit(f"失败: {task.description} - 找不到源视频")
                self.task_completed.emit(task.description, False)
        
        if self._running:
            self.all_completed.emit()
    
    def pause(self):
        """Pause processing."""
        self._paused = True
    
    def resume(self):
        """Resume processing."""
        self._paused = False
    
    def stop(self):
        """Stop processing."""
        self._running = False
        self.processor.stop()


class VideoCutterWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频剪辑工具")
        self.resize(900, 700)
        
        # Data
        self.video_folder: Path | None = None
        self.excel_path: Path | None = None
        self.output_folder: Path | None = None
        self.video_infos: list[VideoInfo] = []
        self.clip_definitions: list[ClipDefinition] = []
        self.clip_tasks: list[ClipTask] = []
        
        # Processing
        self.processor = VideoProcessor()
        self.worker: WorkerThread | None = None
        self.start_time: datetime | None = None
        self.total_clips = 0
        self.completed_clips = 0
        self.failed_clips = 0
        
        self.setup_ui()
        self.setup_menu()
        self.setup_statusbar()
        self.check_ffmpeg_availability()
    
    def check_ffmpeg_availability(self):
        """Check if ffmpeg is available and show warning if not."""
        ffmpeg_ok, ffmpeg_msg = check_ffmpeg()
        ffprobe_ok, ffprobe_msg = check_ffprobe()
        
        if not ffmpeg_ok or not ffprobe_ok:
            msg = "视频处理工具未正确配置:\n\n"
            if not ffmpeg_ok:
                msg += f"• ffmpeg: {ffmpeg_msg}\n"
            if not ffprobe_ok:
                msg += f"• ffprobe: {ffprobe_msg}\n"
            msg += "\n请安装 ffmpeg 或使用包含 ffmpeg 的打包版本。"
            
            QMessageBox.warning(self, "依赖缺失", msg)
            self.statusBar().showMessage("警告: ffmpeg 不可用")
        else:
            self.statusBar().showMessage(f"就绪 (ffmpeg: {get_ffmpeg_path()})")
    
    def setup_ui(self):
        """Setup user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        
        # === Input Section ===
        input_group = QGroupBox("输入设置")
        input_layout = QVBoxLayout()
        
        # Video folder selection
        video_layout = QHBoxLayout()
        video_layout.addWidget(QLabel("原视频文件夹:"))
        self.video_path_edit = QLineEdit()
        self.video_path_edit.setPlaceholderText("选择包含视频文件的文件夹")
        self.video_path_edit.setReadOnly(True)
        video_layout.addWidget(self.video_path_edit)
        self.video_btn = QPushButton("选择...")
        self.video_btn.clicked.connect(self.select_video_folder)
        video_layout.addWidget(self.video_btn)
        input_layout.addLayout(video_layout)
        
        # Excel file selection
        excel_layout = QHBoxLayout()
        excel_layout.addWidget(QLabel("Excel表格:"))
        self.excel_path_edit = QLineEdit()
        self.excel_path_edit.setPlaceholderText("选择包含片段信息的Excel文件")
        self.excel_path_edit.setReadOnly(True)
        excel_layout.addWidget(self.excel_path_edit)
        self.excel_btn = QPushButton("选择...")
        self.excel_btn.clicked.connect(self.select_excel_file)
        excel_layout.addWidget(self.excel_btn)
        input_layout.addLayout(excel_layout)
        
        # Video count label
        self.video_count_label = QLabel("请选择原视频文件夹")
        self.video_count_label.setStyleSheet("color: #666;")
        input_layout.addWidget(self.video_count_label)
        
        # Clip count label
        self.clip_count_label = QLabel("请选择Excel表格")
        self.clip_count_label.setStyleSheet("color: #666;")
        input_layout.addWidget(self.clip_count_label)
        
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)
        
        # === Output Section ===
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout()
        
        # Output folder selection
        out_folder_layout = QHBoxLayout()
        out_folder_layout.addWidget(QLabel("输出文件夹:"))
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("默认输出到原视频同一目录")
        self.output_path_edit.setReadOnly(True)
        out_folder_layout.addWidget(self.output_path_edit)
        self.output_btn = QPushButton("选择...")
        self.output_btn.clicked.connect(self.select_output_folder)
        out_folder_layout.addWidget(self.output_btn)
        output_layout.addLayout(out_folder_layout)
        
        # Quality selection
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("输出质量:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItem("高质量 (原码率)", QualitySettings.high())
        self.quality_combo.addItem("中等质量 (50%码率)", QualitySettings.medium())
        self.quality_combo.addItem("低质量 (30%码率)", QualitySettings.low())
        quality_layout.addWidget(self.quality_combo)
        quality_layout.addStretch()
        output_layout.addLayout(quality_layout)
        
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)
        
        # === Progress Section ===
        progress_group = QGroupBox("任务进度")
        progress_layout = QVBoxLayout()
        
        # Overall progress
        overall_layout = QHBoxLayout()
        overall_layout.addWidget(QLabel("总体进度:"))
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        overall_layout.addWidget(self.overall_progress)
        self.overall_label = QLabel("0%")
        overall_layout.addWidget(self.overall_label)
        progress_layout.addLayout(overall_layout)
        
        # Current task progress
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("当前任务:"))
        self.current_task_label = QLabel("等待开始...")
        current_layout.addWidget(self.current_task_label)
        progress_layout.addLayout(current_layout)
        
        self.current_progress = QProgressBar()
        self.current_progress.setRange(0, 100)
        progress_layout.addWidget(self.current_progress)
        
        # Time estimate
        time_layout = QHBoxLayout()
        self.time_label = QLabel("预计剩余时间: --:--")
        time_layout.addWidget(self.time_label)
        time_layout.addStretch()
        progress_layout.addLayout(time_layout)
        
        # Task list
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(3)
        self.task_table.setHorizontalHeaderLabels(["任务", "状态", "进度"])
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.task_table.setAlternatingRowColors(True)
        self.task_table.setMaximumHeight(150)
        progress_layout.addWidget(self.task_table)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始剪辑")
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setEnabled(False)
        button_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("暂停")
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)
        button_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        progress_layout.addLayout(button_layout)
        
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # === Log Section ===
        log_group = QGroupBox("任务日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(120)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
    
    def setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("文件")
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_statusbar(self):
        """Setup status bar."""
        self.statusBar().showMessage("就绪")
    
    def log(self, message: str):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.statusBar().showMessage(message)
    
    def select_video_folder(self):
        """Select source video folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "选择原视频文件夹",
            str(Path.home())
        )
        
        if folder:
            self.video_folder = Path(folder)
            self.video_path_edit.setText(str(self.video_folder))
            
            # Scan for video files
            videos = get_video_files(self.video_folder)
            
            if videos:
                # Get video info for each file
                self.video_infos = []
                for video_path in videos:
                    info = None
                    # Try to get video info (requires ffprobe)
                    try:
                        from .video_processor import get_video_info
                        info = get_video_info(video_path)
                    except:
                        pass
                    
                    if info:
                        self.video_infos.append(info)
                    else:
                        # Create basic info from filename
                        start_time = parse_video_filename(video_path.name)
                        if start_time:
                            self.video_infos.append(VideoInfo(
                                path=video_path,
                                start_time=start_time,
                                duration=0,  # Unknown
                                width=0, height=0, bitrate=0, fps=0
                            ))
                
                count = len(self.video_infos)
                self.video_count_label.setText(f"发现 {count} 个视频文件")
                self.video_count_label.setStyleSheet("color: green;")
                
                self.log(f"已加载 {count} 个视频文件")
            else:
                self.video_count_label.setText("文件夹中没有找到视频文件")
                self.video_count_label.setStyleSheet("color: red;")
                self.video_infos = []
            
            self.update_start_button()
    
    def select_excel_file(self):
        """Select Excel file with clip definitions."""
        file, _ = QFileDialog.getOpenFileName(
            self, "选择Excel表格",
            str(Path.home()),
            "Excel Files (*.xlsx *.xls)"
        )
        
        if file:
            self.excel_path = Path(file)
            self.excel_path_edit.setText(str(self.excel_path))
            
            # Parse Excel with debug logging
            self.log("正在解析 Excel 文件...")
            self.clip_definitions = parse_excel_clips(self.excel_path, debug=True)
            
            if self.clip_definitions:
                count = len(self.clip_definitions)
                self.clip_count_label.setText(f"待剪切 {count} 个片段")
                self.clip_count_label.setStyleSheet("color: green;")
                
                self.log(f"✓ 已加载 {count} 个片段")
                
                # Update task table
                self.update_task_table()
            else:
                self.clip_count_label.setText("未能解析到片段信息")
                self.clip_count_label.setStyleSheet("color: red;")
                self.clip_definitions = []
                self.log("✗ 解析失败，请查看上方日志了解原因")
            
            self.update_start_button()
    
    def select_output_folder(self):
        """Select output folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "选择输出文件夹",
            str(self.video_folder) if self.video_folder else str(Path.home())
        )
        
        if folder:
            self.output_folder = Path(folder)
            self.output_path_edit.setText(str(self.output_folder))
    
    def update_task_table(self):
        """Update task table with clip definitions."""
        self.task_table.setRowCount(len(self.clip_definitions))
        
        for row, clip in enumerate(self.clip_definitions):
            # Task name
            self.task_table.setItem(row, 0, QTableWidgetItem(clip.description))
            
            # Status
            status_item = QTableWidgetItem("等待")
            status_item.setData(Qt.ItemDataRole.UserRole, "pending")
            self.task_table.setItem(row, 1, status_item)
            
            # Progress
            progress_item = QTableWidgetItem("0%")
            progress_item.setData(Qt.ItemDataRole.UserRole, 0.0)
            self.task_table.setItem(row, 2, progress_item)
    
    def update_start_button(self):
        """Update start button enabled state."""
        has_videos = len(self.video_infos) > 0
        has_clips = len(self.clip_definitions) > 0
        self.start_btn.setEnabled(has_videos and has_clips)
    
    def start_processing(self):
        """Start video processing."""
        if not self.video_infos or not self.clip_definitions:
            return
        
        # Prepare output folder
        if not self.output_folder:
            self.output_folder = self.video_folder
        
        # Create clip tasks
        self.clip_tasks = []
        for clip in self.clip_definitions:
            task = ClipTask(
                clip_start=clip.start_time,
                clip_end=clip.end_time,
                description=clip.description,
                output_path=self.output_folder / clip.get_output_filename()
            )
            self.clip_tasks.append(task)
        
        # Get quality setting
        quality = self.quality_combo.currentData()
        
        # Reset counters
        self.total_clips = len(self.clip_tasks)
        self.completed_clips = 0
        self.failed_clips = 0
        self.start_time = datetime.now()
        
        # Update task table
        for row in range(self.task_table.rowCount()):
            self.task_table.item(row, 1).setText("等待")
            self.task_table.item(row, 1).setData(Qt.ItemDataRole.UserRole, "pending")
            self.task_table.item(row, 2).setText("0%")
            self.task_table.item(row, 2).setData(Qt.ItemDataRole.UserRole, 0.0)
        
        # Disable controls
        self.video_btn.setEnabled(False)
        self.excel_btn.setEnabled(False)
        self.output_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        
        # Start worker thread
        self.worker = WorkerThread(
            self.processor, self.clip_tasks, quality, self.video_infos
        )
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.log_message.connect(self.on_log_message)
        self.worker.task_completed.connect(self.on_task_completed)
        self.worker.all_completed.connect(self.on_all_completed)
        self.worker.start()
        
        # Update progress timer
        self.update_progress_timer = QTimer()
        self.update_progress_timer.timeout.connect(self.update_progress_display)
        self.update_progress_timer.start(500)
        
        self.log("开始处理任务...")
    
    def toggle_pause(self):
        """Toggle pause/resume."""
        if self.worker and self.worker.isRunning():
            if self.worker._paused:
                self.worker.resume()
                self.processor.resume()
                self.pause_btn.setText("暂停")
                self.log("继续处理")
            else:
                self.worker.pause()
                self.processor.pause()
                self.pause_btn.setText("继续")
                self.log("暂停处理")
    
    def stop_processing(self):
        """Stop processing."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "确认停止",
                "确定要停止处理吗？已完成的片段会被保留。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.stop()
                self.worker.wait()
                self.log("处理已停止")
                
                # Re-enable controls
                self.video_btn.setEnabled(True)
                self.excel_btn.setEnabled(True)
                self.output_btn.setEnabled(True)
                self.start_btn.setEnabled(True)
                self.pause_btn.setEnabled(False)
                self.stop_btn.setEnabled(False)
                self.pause_btn.setText("暂停")
                
                if self.update_progress_timer:
                    self.update_progress_timer.stop()
    
    def on_progress_updated(self, progress: float):
        """Handle progress update from worker."""
        # Update current task progress in table
        if self.worker and self.worker.current_task:
            task = self.worker.current_task
            task.progress = progress
            
            # Find row in table
            for row in range(self.task_table.rowCount()):
                if self.task_table.item(row, 0).text() == task.description:
                    self.task_table.item(row, 2).setText(f"{int(progress * 100)}%")
                    self.task_table.item(row, 2).setData(Qt.ItemDataRole.UserRole, progress)
                    break
    
    def on_log_message(self, message: str):
        """Handle log message from worker."""
        self.log(message)
    
    def on_task_completed(self, description: str, success: bool):
        """Handle task completion."""
        # Find and update row
        for row in range(self.task_table.rowCount()):
            if self.task_table.item(row, 0).text() == description:
                if success:
                    self.task_table.item(row, 1).setText("完成")
                    self.task_table.item(row, 1).setData(Qt.ItemDataRole.UserRole, "completed")
                    self.task_table.item(row, 1).setForeground(Qt.GlobalColor.darkGreen)
                    self.completed_clips += 1
                else:
                    self.task_table.item(row, 1).setText("失败")
                    self.task_table.item(row, 1).setData(Qt.ItemDataRole.UserRole, "failed")
                    self.task_table.item(row, 1).setForeground(Qt.GlobalColor.red)
                    self.failed_clips += 1
                break
    
    def on_all_completed(self):
        """Handle all tasks completed."""
        self.log(f"处理完成! 成功: {self.completed_clips}, 失败: {self.failed_clips}")
        
        # Re-enable controls
        self.video_btn.setEnabled(True)
        self.excel_btn.setEnabled(True)
        self.output_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        if self.update_progress_timer:
            self.update_progress_timer.stop()
        
        # Final progress update
        self.overall_label.setText("100%")
        self.overall_progress.setValue(100)
        self.current_task_label.setText("全部完成")
    
    def update_progress_display(self):
        """Update progress display."""
        if not self.start_time:
            return
        
        # Calculate overall progress
        completed = self.completed_clips + self.failed_clips
        if completed > 0:
            # Completed tasks count as 100%, current task has progress
            current_progress = 0
            if self.worker and self.worker.current_task:
                current_progress = self.worker.current_task.progress
            
            overall = (completed - 1 + current_progress) / self.total_clips * 100
            overall = min(100, max(0, overall))
            
            self.overall_progress.setValue(int(overall))
            self.overall_label.setText(f"{int(overall)}%")
        
        # Estimate remaining time
        if completed > 0 and self.completed_clips > 0:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            avg_time_per_task = elapsed / self.completed_clips
            remaining_tasks = self.total_clips - completed
            remaining_seconds = remaining_tasks * avg_time_per_task
            
            # Format remaining time
            hours = int(remaining_seconds // 3600)
            minutes = int((remaining_seconds % 3600) // 60)
            secs = int(remaining_seconds % 60)
            
            remaining_str = f"{hours:02d}:{minutes:02d}:{secs:02d}"
            self.time_label.setText(f"预计剩余时间: {remaining_str}")
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "关于视频剪辑工具",
            "视频剪辑工具 v1.0\n\n"
            "基于 PyQt6 + ffmpeg 构建\n\n"
            "功能:\n"
            "- 从多个视频中按时间段截取片段\n"
            "- 支持多种视频格式 (mkv, mp4, mov等)\n"
            "- 三种输出质量等级\n"
            "- 实时进度显示和剩余时间估算\n"
            "- 暂停/继续/停止功能"
        )
    
    def closeEvent(self, event):
        """Handle window close."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "确认退出",
                "处理任务正在进行中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            
            self.worker.stop()
            self.worker.wait()
        
        event.accept()


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for better look
    
    window = VideoCutterWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
