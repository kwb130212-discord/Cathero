from __future__ import annotations
import time
from dataclasses import dataclass
import pyautogui
from PySide6.QtCore import QThread,Signal
@dataclass(frozen=True)
class ActionRule:
    template:str;enabled:bool=False;click:bool=False
class VisionWorker(QThread):
    frame_ready=Signal(object);detections_ready=Signal(object);metrics_ready=Signal(object);event=Signal(str);error=Signal(str)
    def __init__(self,settings,capture,analyzer,vlm,notifier,rules):
        super().__init__();self.settings=settings;self.capture=capture;self.analyzer=analyzer;self.vlm=vlm;self.notifier=notifier;self.rules=rules;self.running=True;self.automation_enabled=settings.automation_enabled;self._interval=max(.03,settings.analysis_interval_ms/1000);self._last_vlm=0;self._last_action={};self._clicks=0;self._started=time.monotonic()
    def stop(self):self.running=False
    def set_automation(self,enabled):self.automation_enabled=enabled
    def set_analysis_interval(self,milliseconds):self._interval=max(.03,milliseconds/1000)
    def run(self):
        while self.running:
            started=time.monotonic()
            try:
                frame=self.capture.grab();detections=self.analyzer.detect(frame);self.frame_ready.emit(frame);self.detections_ready.emit(detections);self._act(detections);now=time.monotonic()
                if self.vlm and now-self._last_vlm>=self.settings.vlm_interval_ms/1000:self._last_vlm=now;self.event.emit(f"VLM: {self.vlm.analyze(frame,self.vlm.default_prompt())}")
                self.metrics_ready.emit({"fps":1/max(.001,time.monotonic()-started),"clicks":self._clicks,"runtime":int(now-self._started)})
            except Exception as exc:self.error.emit(str(exc))
            remain=self._interval-(time.monotonic()-started)
            if remain>0:self.msleep(int(remain*1000))
        self.capture.close()
    def _act(self,detections):
        if not self.automation_enabled:return
        by_name={d.name:d for d in detections};now=time.monotonic();cooldown=self.settings.action_interval_ms/1000
        for rule in self.rules:
            if not rule.enabled or not rule.click:continue
            detection=by_name.get(rule.template)
            if not detection or now-self._last_action.get(rule.template,0)<cooldown:continue
            x,y=detection.center;pyautogui.click(x,y);self._last_action[rule.template]=now;self._clicks+=1;self.event.emit(f"CLICK {rule.template} ({detection.confidence:.2f})")
