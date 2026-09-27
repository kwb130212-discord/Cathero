from __future__ import annotations
from dataclasses import dataclass
import time,cv2,mss
import numpy as np
@dataclass(frozen=True)
class Region:
    left:int; top:int; width:int; height:int
class ScreenCapture:
    def __init__(self,region:Region|None=None): self.sct=mss.mss(); self.region=region
    def grab(self):
        monitor={'left':self.region.left,'top':self.region.top,'width':self.region.width,'height':self.region.height} if self.region else self.sct.monitors[1]
        return cv2.cvtColor(np.asarray(self.sct.grab(monitor),dtype=np.uint8),cv2.COLOR_BGRA2BGR)
    def stream(self,fps:int):
        delay=1/max(1,fps)
        while True:
            started=time.perf_counter(); yield self.grab(); remain=delay-(time.perf_counter()-started)
            if remain>0: time.sleep(remain)
    def close(self): self.sct.close()
