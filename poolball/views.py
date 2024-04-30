from django.shortcuts import render
from django.http import StreamingHttpResponse
from poolball.camera import WebCam
from django.views.decorators.csrf import csrf_exempt


def index(request):
  return render(request, 'index.html')


def gen(camera=None):
  while True:
    frame = camera.get_frame()
    
    yield(b'--frame\r\n'
          b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    
  
@csrf_exempt
def webcam(request):
  if request.method == 'GET':

    url = request.GET.get("url")
    socurl = request.GET.get("socurl")

    webcam = WebCam(url, socurl)

    return StreamingHttpResponse(gen(webcam),
                                 content_type='multipart/x-mixed-replace; boundary=frame')
  