from __future__ import annotations
import base64,json
from dataclasses import dataclass
from pathlib import Path
import cv2,requests
@dataclass(frozen=True)
class Detection:
    name:str; confidence:float; x:int; y:int; width:int; height:int
    @property
    def center(self): return self.x+self.width//2,self.y+self.height//2
class TemplateAnalyzer:
    def __init__(self,template_dir='assets/templates',threshold=.86): self.template_dir=Path(template_dir); self.threshold=threshold; self.templates={}; self.reload()
    def reload(self):
        self.templates.clear(); self.template_dir.mkdir(parents=True,exist_ok=True)
        for path in self.template_dir.glob('*.png'):
            image=cv2.imread(str(path),cv2.IMREAD_GRAYSCALE)
            if image is not None and image.size:self.templates[path.stem]=image
    def detect(self,frame):
        if not self.templates:return []
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY); found=[]
        for name,template in self.templates.items():
            th,tw=template.shape[:2]
            if th>gray.shape[0] or tw>gray.shape[1]:continue
            result=cv2.matchTemplate(gray,template,cv2.TM_CCOEFF_NORMED); _,confidence,_,location=cv2.minMaxLoc(result)
            if confidence>=self.threshold:
                x,y=location; found.append(Detection(name,float(confidence),x,y,tw,th))
        return found
class LocalVLM:
    def __init__(self,endpoint,model,timeout=8):self.endpoint=endpoint;self.model=model;self.timeout=timeout
    def analyze(self,frame,prompt):
        ok,encoded=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,70])
        if not ok:raise RuntimeError('JPEG encoding failed')
        image=base64.b64encode(encoded.tobytes()).decode('ascii')
        payload={'model':self.model,'temperature':0,'max_tokens':256,'messages':[{'role':'user','content':[{'type':'text','text':prompt},{'type':'image_url','image_url':{'url':f'data:image/jpeg;base64,{image}'}}]}]}
        response=requests.post(self.endpoint,json=payload,timeout=self.timeout);response.raise_for_status();content=response.json()['choices'][0]['message']['content']
        try:return json.loads(content)
        except json.JSONDecodeError:return {'raw':content}
    @staticmethod
    def default_prompt():return 'Analyze this game UI screenshot. Return JSON only with keys state, stage, currency_low, popup, blocked, notable_event. state must be idle,battle,reward,menu,unknown.'
