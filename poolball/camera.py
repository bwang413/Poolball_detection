from socketIO_client_nexus import SocketIO, LoggingNamespace
import socketio
from datetime import datetime
import time 
import cv2 as cv
import numpy as np
from ultralytics import YOLO


class WebCam(object):
  _instance = None

  def __init__(self, rtsp_url, sio_host):
    self.sio_client = socketio.SimpleClient()

    self.NAME = [1, 10, 2, 3, 4, 5, 6, 7, 8, 9]
    
    self.COLORS = [[0, 0, 0], [0, 125, 15], [64, 227, 141], [143, 243, 207], [146, 38, 213], [98, 71, 94],
                   [136, 177, 151], [188, 191, 74], [156, 95, 221], [174, 192, 215], [6, 244, 119]]
    
    self.THRESHOLD = 0.6
    self.FONT_SCALE = 1
    self.THICKNESS = 2
    self.CAM_MODE = 1
    self.video = cv.VideoCapture(rtsp_url)
    self.sio_client.connect(sio_host)
  
  def __del__(self):
    self.video.release()
  
  def get_frame(self):
    model = YOLO('../detection.pt')
    
    ret, frame = self.video.read()
     
    results = model.predict(frame, conf=0.6)[0]
    
    for data in results.boxes.data.tolist():
      boxes = results.boxes
      
      if len(results.boxes) == 10:
        xyxy_array = boxes.xyxy.cpu().numpy()
        cls = boxes.cls.cpu().numpy().reshape((-1, 1))
        conf = np.hstack(boxes.conf.cpu().numpy())
        
        conf_flag = np.all(conf > self.THRESHOLD)
        
        if conf_flag:
          xyc = np.hstack(((np.array(xyxy_array[:, 0] + xyxy_array[:, 2]) / 2).reshape(-1, 1),
                           (np.array(xyxy_array[:, 1] + xyxy_array[:, 3]) / 2).reshape(-1, 1)))
          
          if self.CAM_MODE == 1:
            s_xyc = np.argsort(xyc[:, 1])
          else:
            s_xyc = np.argsort(xyc[:, 0])
          
          s_cls = np.hstack(cls[s_xyc].astype(int))
          s_name = np.flip([self.NAME[i] for i in s_cls])
          s_pname = ' '.join(str(num) for num in s_name)

          send_result = f"{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}-->{s_pname}"
        
          print(f"Ball order is {send_result}\n\n\n\n")

          xmin, ymin, xmax, ymax, confidence, class_id = data
          
          xmin = int(xmin)
          ymin = int(ymin)
          xmax = int(xmax)
          ymax = int(ymax)
          class_id = int(class_id)
          
          color = [int(c) for c in self.COLORS[class_id]]
          cv.rectangle(frame, (xmin, ymin), (xmax, ymax), color=color, thickness=self.THICKNESS)
          text = f"{self.NAME[class_id]}"
          
          (text_width, text_height) = \
          cv.getTextSize(text, cv.FONT_HERSHEY_SIMPLEX, fontScale=1, thickness=self.THICKNESS)[0]
          text_offset_x = xmin
          text_offset_y = ymin - 5
          box_coords = ((text_offset_x, text_offset_y), (text_offset_x + text_width + 2, text_offset_y - text_height))
          overlay = frame.copy()
          cv.rectangle(overlay, box_coords[0], box_coords[1], color=color, thickness=cv.FILLED)
          
          frame = cv.addWeighted(overlay, 0.6, frame, 0.4, 0)
          
          cv.putText(frame, text, (xmin, ymin - 5), cv.FONT_HERSHEY_SIMPLEX,
                     fontScale=self.FONT_SCALE, color=(255, 255, 255), thickness=self.THICKNESS)
          
          self.sio_client.emit("data", send_result)
  
    ret, jpeg = cv.imencode('.jpg', frame)
    
    return jpeg.tobytes()
