import cv2
cam = cv2.VideoCapture(0);ret,frame = cam.read()
cv2.imwrite("test.jpg",frame);cam.release()