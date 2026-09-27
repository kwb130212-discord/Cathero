from __future__ import annotations
import cv2
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage,QPixmap
from PySide6.QtWidgets import QDoubleSpinBox,QFormLayout,QGroupBox,QHBoxLayout,QLabel,QMainWindow,QPushButton,QSpinBox,QTextEdit,QVBoxLayout,QWidget,QComboBox
from config.actions import load_action_rules
from config.settings import Settings
from core.engine import VisionWorker
from notifications.webhook import WebhookNotifier
from vision.analyzer import LocalVLM,TemplateAnalyzer
from vision.capture import ScreenCapture

STYLE='''QMainWindow,QWidget{background:#0d0f12;color:#e8eaed;font-size:13px}QGroupBox{border:1px solid #292e35;border-radius:10px;margin-top:10px;padding:12px}QPushButton{background:#1a1f26;border:1px solid #303640;border-radius:8px;padding:8px 14px}QPushButton:checked{background:#304a63}QLabel#metric{font-size:20px;font-weight:700}QTextEdit{background:#090b0e;border:1px solid #242932;border-radius:8px}'''

class MainWindow(QMainWindow):
    def __init__(self,settings:Settings):
        super().__init__();self.settings=settings;self.setWindowTitle(settings.app_name);self.resize(1180,760);self.setStyleSheet(STYLE)
        self.preview=QLabel('CAPTURE PREVIEW');self.preview.setAlignment(Qt.AlignCenter);self.preview.setMinimumSize(640,420);self.preview.setStyleSheet('background:#07090c;border:1px solid #262b32;border-radius:12px')
        self.stage,self.fps,self.clicks,self.runtime=[QLabel(x) for x in ('—','0','0','00:00:00')]
        for label in (self.stage,self.fps,self.clicks,self.runtime):label.setObjectName('metric')
        self.log=QTextEdit();self.log.setReadOnly(True);self.start_button=QPushButton('Start');self.stop_button=QPushButton('Stop');self.auto_toggle=QPushButton('Automation OFF');self.auto_toggle.setCheckable(True)
        self.start_button.clicked.connect(self.start_engine);self.stop_button.clicked.connect(self.stop_engine);self.auto_toggle.clicked.connect(self.toggle_automation)
        controls=QHBoxLayout();[controls.addWidget(w) for w in (self.start_button,self.stop_button,self.auto_toggle)];controls.addStretch();metrics=QHBoxLayout()
        for title,widget in (('Stage',self.stage),('FPS',self.fps),('Clicks',self.clicks),('Runtime',self.runtime)):
            box=QGroupBox(title);lay=QVBoxLayout(box);lay.addWidget(widget);metrics.addWidget(box)
        left=QVBoxLayout();left.addLayout(controls);left.addWidget(self.preview,1);right=QVBoxLayout();right.addLayout(metrics);right.addWidget(self._settings_panel());right.addWidget(self.log,1);root=QHBoxLayout();root.addLayout(left,3);root.addLayout(right,2);container=QWidget();container.setLayout(root);self.setCentralWidget(container);self.worker=None
    def _settings_panel(self):
        box=QGroupBox('Runtime');form=QFormLayout(box);self.interval=QSpinBox();self.interval.setRange(30,5000);self.interval.setValue(self.settings.analysis_interval_ms);self.threshold=QDoubleSpinBox();self.threshold.setRange(.5,.99);self.threshold.setSingleStep(.01);self.threshold.setValue(self.settings.match_threshold);self.model_status=QComboBox();self.model_status.addItems(['OpenCV only','OpenCV + Local VLM']);self.model_status.setCurrentIndex(1 if self.settings.vlm_enabled else 0);form.addRow('Analysis interval',self.interval);form.addRow('Template threshold',self.threshold);form.addRow('Vision backend',self.model_status);return box
    def start_engine(self):
        if self.worker and self.worker.isRunning():return
        analyzer=TemplateAnalyzer(threshold=self.threshold.value())
        vlm=LocalVLM(self.settings.vlm_endpoint,self.settings.vlm_model,self.settings.vlm_timeout) if self.settings.vlm_enabled and self.model_status.currentIndex()==1 else None
        notifier=WebhookNotifier(self.settings.discord_webhook_url,self.settings.telegram_bot_token,self.settings.telegram_chat_id)
        rules=load_action_rules()
        self.worker=VisionWorker(self.settings,ScreenCapture(),analyzer,vlm,notifier,rules)
        self.worker.frame_ready.connect(self.on_frame);self.worker.detections_ready.connect(self.on_detections);self.worker.metrics_ready.connect(self.on_metrics);self.worker.event.connect(self.append_log);self.worker.error.connect(lambda m:self.append_log('ERROR: '+m));self.worker.start()
        self.append_log(f'Engine started / rules={len(rules)}')
    def stop_engine(self):
        if self.worker:self.worker.stop();self.worker.wait(2000);self.worker=None;self.append_log('Engine stopped')
    def toggle_automation(self,checked):
        self.auto_toggle.setText('Automation ON' if checked else 'Automation OFF')
        if self.worker:self.worker.set_automation(checked)
    def on_frame(self,frame):
        rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB);h,w,ch=rgb.shape;image=QImage(rgb.data,w,h,ch*w,QImage.Format_RGB888).copy();self.preview.setPixmap(QPixmap.fromImage(image).scaled(self.preview.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))
    def on_detections(self,detections):
        names=', '.join(f'{d.name}:{d.confidence:.2f}' for d in detections)
        if names:self.stage.setText(names[:24])
    def on_metrics(self,metrics):
        self.fps.setText(f"{metrics['fps']:.1f}");self.clicks.setText(str(metrics['clicks']));s=int(metrics['runtime']);self.runtime.setText(f'{s//3600:02d}:{s%3600//60:02d}:{s%60:02d}')
    def append_log(self,message):self.log.append(message)
    def closeEvent(self,event):self.stop_engine();event.accept()
