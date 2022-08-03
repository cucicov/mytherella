import cv2

faceCascade = cv2.CascadeClassifier('cascade_default.xml')

# grab the reference to the webcam
vs = cv2.VideoCapture(0)

faceDetected = False
# keep looping
while True:
    # grab the current frame
    ret, frame = vs.read()

    # if we are viewing a video and we did not grab a frame,
    # then we have reached the end of the video
    if frame is None:
        break

    faces = faceCascade.detectMultiScale(frame)

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

    # show the frame to our screen

    if (len(faces) > 0):
        cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("window", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.imshow("window", frame)
    else:
        cv2.destroyAllWindows()

    key = cv2.waitKey(1) & 0xFF

    # if the 'q' or ESC key is pressed, stop the loop
    if key == ord("q") or key == 27:
        break

# close all windows
cv2.destroyAllWindows()