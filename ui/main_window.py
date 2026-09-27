from __future__ import annotations

import cv2
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QComboBox,QDoubleSpinBox,QFormLayout,QGridLayout,QGroupBox,QHBoxLayout,QLabel,QMainWindow,QPushButton,QScrollArea,QSpinBox,QTextEdit,QVBoxLayout,QWidget
from config.actions import load_action_rules
from core.engine import VisionWorker
from notifications.webhook import WebhookNotifier
from vision.analyzer import LocalVLM,TemplateAnalyzer
from vision.capture import ScreenCapture

STYLE="""QMainWindow,QWidget{background:#0d0f12;color:#e8eaed;font-size:13px}QGroupBox{border:1px solid #292e35;border-radius:10px;margin-top:9px;padding:10px}QPushButton{background:#1a1f26;border:1px solid #303640;border-radius:8px;padding:8px 12px}QPushButton:hover{background:#222a34}QPushButton:checked{background:#304a63}QLabel#metric{font-size:19px;font-weight:700}QTextEdit{background:#090b0e;border:1px solid #242932;border-radius:8px}QScrollArea{border:0;background:transparent}"""

class MainWindow(QMainWindow):
    def __init__(self,settings):
        super().__init__();self.settings=settings;self.worker=None;self._preview_pixmap=None;self._compact=False
        self.setWindowTitle(settings.app_name);self.setMinimumSize(420,360)
        screen=self.screen()
        if screen:
            area=screen.availableGeometry();self.resize(min(1180,int(area.width()*.88)),min(760,int(area.height()*.88)))
        else:self.resize(1180,760)
        self.setStyleSheet(STYLE)
        self.preview=QLabel("CAPTURE PREVIEW");self.preview.setAlignment(Qt.AlignCenter);self.preview.setMinimumSize(180,180);self.preview.setStyleSheet("background:#07090c;border:1px solid #262b32;border-radius:12px")
        self.stage,self.fps,self.clicks,self.runtime=[QLabel(x) for x in ("—","0","0","00:00:00")]
        for label in (self.stage,self.fps,self.clicks,self.runtime):label.setObjectName("metric")
        self.log=QTextEdit();self.log.setReadOnly(True);self.log.setMinimumHeight(100)
        self.start_button=QPushButton("Start");self.stop_button=QPushButton("Stop");self.auto_toggle=QPushButton("Automation OFF");self.auto_toggle.setCheckable(True)
        self.start_button.clicked.connect(self.start_engine);self.stop_button.clicked.connect(self.stop_engine);self.auto_toggle.clicked.connect(self.toggle_automation)
        self._build_layout();self._apply_responsive_layout(self.width())

    def _controls(self):
        row=QHBoxLayout()
        for widget in (self.start_button,self.stop_button,self.auto_toggle):row.addWidget(widget)
        row.addStretch();return row

    def _metrics(self):
        grid=QGridLayout();items=(("Stage",self.stage),("FPS",self.fps),("Clicks",self.clicks),("Runtime",self.runtime))
        for i,(title,widget) in enumerate(items):
            box=QGroupBox(title);lay=QVBoxLayout(box);lay.addWidget(widget);grid.addWidget(box,i//2,i%2)
        self.metrics_widget=QWidget();self.metrics_widget.setLayout(grid);return self.metrics_widget

    def _settings_panel(self):
        box=QGroupBox("Runtime");form=QFormLayout(box)
        self.interval=QSpinBox();self.interval.setRange(30,5000);self.interval.setSingleStep(10);self.interval.setValue(self.settings.analysis_interval_ms);self.interval.valueChanged.connect(self._sync_settings)
        self.threshold=QDoubleSpinBox();self.threshold.setRange(.5,.99);self.threshold.setSingleStep(.01);self.threshold.setValue(self.settings.match_threshold)
        self.model_status=QComboBox();self.model_status.addItems(["OpenCV only","OpenCV + Local VLM"]);self.model_status.setCurrentIndex(1 if self.settings.vlm_enabled else 0)
        form.addRow("Analysis interval",self.interval);form.addRow("Template threshold",self.threshold);form.addRow("Vision backend",self.model_status);return box

    def _build_layout(self):
        self.left=QWidget();left_layout=QVBoxLayout(self.left);left_layout.setContentsMargins(0,0,0,0);left_layout.addLayout(self._controls());left_layout.addWidget(self.preview,1)
        self.right=QWidget();right_layout=QVBoxLayout(self.right);right_layout.setContentsMargins(0,0,0,0);right_layout.addWidget(self._metrics());right_layout.addWidget(self._settings_panel());right_layout.addWidget(self.log,1)
        self.content=QWidget();self.root=QHBoxLayout(self.content);self.root.setContentsMargins(10,10,10,10);self.root.setSpacing(10);self.root.addWidget(self.left,3);self.root.addWidget(self.right,2)
        self.scroll=QScrollArea();self.scroll.setWidgetResizable(True);self.scroll.setWidget(self.content);self.setCentralWidget(self.scroll)

    def _apply_responsive_layout(self,width):
        compact=width<900
        if compact==self._compact:return
        self._compact=compact;self.root.setDirection(QVBoxLayout.TopToBottom if compact else QVBoxLayout.LeftToRight);self.root.setSpacing(8 if compact else 10)
        self.preview.setMinimumHeight(max(180,min(360,int(self.height()*.38))) if compact else 260)
        self.right.setMinimumWidth(0 if compact else 300);self._refresh_preview()

    def resizeEvent(self,event):
        super().resizeEvent(event);self._apply_responsive_layout(event.size().width());self._refresh_preview()

    def _refresh_preview(self):
        if self._preview_pixmap and not self.preview.size().isEmpty():self.preview.setPixmap(self._preview_pixmap.scaled(self.preview.size(),Qt.KeepAspectRatio,Qt.FastTransformation))

    def _sync_settings(self):
        if self.worker:self.worker.set_analysis_interval(self.interval.value())

    def start_engine(self):
        if self.worker and self.worker.isRunning():return
        analyzer=TemplateAnalyzer(threshold=self.threshold.value())
        vlm=LocalVLM(self.settings.vlm_endpoint,self.settings.vlm_model,self.settings.vlm_timeout) if self.settings.vlm_enabled and self.model_status.currentIndex()==1 else None
        notifier=WebhookNotifier(self.settings.discord_webhook_url,self.settings.telegram_bot_token,self.settings.telegram_chat_id)
        rules=load_action_rules();self.worker=VisionWorker(self.settings,ScreenCapture(),analyzer,vlm,notifier,rules)
        self.worker.frame_ready.connect(self.on_frame);self.worker.detections_ready.connect(self.on_detections);self.worker.metrics_ready.connect(self.on_metrics);self.worker.event.connect(self.append_log);self.worker.error.connect(lambda m:self.append_log("ERROR: "+m));self.worker.start();self._sync_settings();self.append_log(f"Engine started / rules={len(rules)}")

    def stop_engine(self):
        if self.worker:self.worker.stop();self.worker.wait(2000);self.worker=None;self.append_log("Engine stopped")

    def toggle_automation(self,checked):
        self.auto_toggle.setText("Automation ON" if checked else "Automation OFF")
        if self.worker:self.worker.set_automation(checked)

    def on_frame(self,frame):
        rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB);h,w,ch=rgb.shape;self._preview_pixmap=QPixmap.fromImage(QImage(rgb.data,w,h,ch*w,QImage.Format_RGB888));self._refresh_preview()

    def on_detections(self,detections):
        names=", ".join(f"{d.name}:{d.confidence:.2f}" for d in detections)
        if names:self.stage.setText(names[:24])

    def on_metrics(self,metrics):
        self.fps.setText(f"{metrics['fps']:.1f}");self.clicks.setText(str(metrics["clicks"]));seconds=int(metrics["runtime"]);self.runtime.setText(f"{seconds//3600:02d}:{seconds%3600//60:02d}:{seconds%60:02d}")

    def append_log(self,message):self.log.append(message)
    def closeEvent(self,event):self.stop_engine();event.accept()
