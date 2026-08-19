import cv2

CAMERA_INDEX = 1

cam = cv2.VideoCapture(CAMERA_INDEX)

if not cam.isOpened():
    print("Could not open camera.")
    exit()

while True:
    ret, frame = cam.read()

    if not ret:
        print("Could not read frame.")
        break

    # Two arbitrary points
    point_a = (100, 100)
    point_b = (500, 300)

    # Draw a line between them
    cv2.circle(frame,point_a,5,(0,0,255),3)
    cv2.circle(frame,point_b,5,(0,0,255),3)
    cv2.rectangle(frame,point_a,point_b,(255,0,0),3)
    cv2.line(
        frame,
        point_a,
        point_b,
        (0, 255, 0),
        3
    )

    cv2.imshow("Line Test", frame)

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cam.release()
cv2.destroyAllWindows()