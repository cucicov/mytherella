import cv2
import pyshine as ps
from time import perf_counter
import shutil

faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_alt.xml')

# grab the reference to the webcam
vs = cv2.VideoCapture(0)
vs.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
width = 1920
height = 1080
vs.set(cv2.CAP_PROP_FRAME_WIDTH, width)
vs.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

faceDetected = False
start_time_window_hidden = perf_counter()
start_time_window_shown = perf_counter()
start_time_window_retake = perf_counter()
photo_taken = False
PORTRAIT_OFFSET_TOLERANCE = 50
DELAY_TILL_NO_FACE_ACTIVATES = 100
WAIT_TILL_FEED_DISPLAY_AFTER_FACE_DETECTED = 3  # 3 seconds after face detection before displaying the feed.
WAIT_TILL_FOR_IMAGE_RETAKE = 5  # 3 seconds after face detection before displaying the feed.
img_counter = 0
force_retake_picture = False
img_name = None
seed_sent = False

# keep looping
while True:
    # grab the current frame
    ret, frame = vs.read()

    # if we are viewing a video and we did not grab a frame,
    # then we have reached the end of the video
    if frame is None:
        break

    faces = faceCascade.detectMultiScale(frame)

    if len(faces) > 0:
        # first reset counter of activity
        start_time_window_shown = perf_counter()

    # PHASE 1 ______________________
    if not photo_taken and len(faces) > 0:

        start_time_window_retake = perf_counter()  # reset counter for display in picture retake.

        # start displaying step 1 - face matching the rect.
        if force_retake_picture or \
                perf_counter() - start_time_window_hidden > WAIT_TILL_FEED_DISPLAY_AFTER_FACE_DETECTED:

            cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty("window", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

            # calculate sizes
            (x, y, w, h) = faces[0]
            face_rect_upper_left = (x, y)
            face_rect_bottom_right = (x + w, y + h)
            screen_width = vs.get(3)
            screen_height = vs.get(4)
            portrait_sides_space = ((screen_width / 5) * 2) - 100
            portrait_updown_space = screen_height / 4
            correct_position_upper_left = (int(portrait_sides_space), int(portrait_updown_space))
            correct_position_bottom_right = (int(screen_width - portrait_sides_space),
                                             int(screen_height - portrait_updown_space))

            # check if face inside correct position
            is_face_in_right_position = abs(
                correct_position_bottom_right[0] - face_rect_bottom_right[0]) < PORTRAIT_OFFSET_TOLERANCE and abs(
                correct_position_bottom_right[1] - face_rect_bottom_right[1]) < PORTRAIT_OFFSET_TOLERANCE and abs(
                correct_position_upper_left[0] - face_rect_upper_left[0]) < PORTRAIT_OFFSET_TOLERANCE and abs(
                correct_position_upper_left[1] - face_rect_upper_left[1]) < PORTRAIT_OFFSET_TOLERANCE

            if is_face_in_right_position:
                face_rect_color = (0, 255, 0)
                # wait for key input
                k = cv2.waitKey(1)

                if k % 256 == 32:
                    photo_taken = True
                    img_counter += 1
                    img_name = "portraits/opencv_frame_{}.png".format(img_counter)
                    cv2.imwrite(img_name, frame)
                    print("{} written!".format(img_name))
                    seed_sent = False
            else:
                face_rect_color = (0, 0, 255)

            if not photo_taken:
                # draw face rectangle
                cv2.rectangle(frame, face_rect_upper_left, face_rect_bottom_right, face_rect_color, 2)
                # draw rectangle for correct position
                cv2.rectangle(frame, correct_position_upper_left, correct_position_bottom_right, (0, 255, 0), 2)
            else:
                # here you arrive after the photo has been taken. remove active window and display taken picture
                force_retake_picture = False  # reset flag after picture was taken
                cv2.destroyAllWindows()

            # display image from webcam
            frame = cv2.flip(frame, 1)  # mirror image for natural effect.
            # display first text
            text1 = 'place your head in the shape, when you are ready press enter.'
            text_1 = ps.putBText(frame, text1, text_offset_x=20, text_offset_y=int(screen_height - 50),
                                 vspace=10, hspace=10, font_scale=1.0, background_RGB=(0, 0, 0),
                                 text_RGB=(255, 250, 250), alpha=0.0, font=cv2.FONT_HERSHEY_SIMPLEX)
            cv2.imshow("window", frame)

    # PHASE 2 ______________________
    # just display taken picture and wait for seconds if user wants to retake picture.
    elif img_name is not None and len(faces) > 0:
        image = cv2.imread(img_name)
        image = cv2.flip(image, 1)
        retake_countdown = WAIT_TILL_FOR_IMAGE_RETAKE - (int(perf_counter() - start_time_window_retake))
        text1 = "Press space to retake picture. " + \
                str(retake_countdown)
        text_1 = ps.putBText(image, text1, text_offset_x=20, text_offset_y=int(screen_height - 50),
                             vspace=10, hspace=10, font_scale=1.0, background_RGB=(0, 0, 0),
                             text_RGB=(255, 250, 250), alpha=0.0, font=cv2.FONT_HERSHEY_SIMPLEX)

        cv2.namedWindow("window2", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("window2", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.imshow("window2", image)

        # listen for trigger to take new picture
        k = cv2.waitKey(1)
        if k % 256 == 32:
            cv2.destroyAllWindows()
            force_retake_picture = True
            photo_taken = False

        # PHASE FINALE ______________
        # close all windows and proceed to animation.
        if retake_countdown < 0:
            cv2.destroyAllWindows()
            start_time_window_hidden = perf_counter()
            if not seed_sent:
                shutil.copy(img_name, 'projector/seed/')
                seed_sent = True

    # PHASE 3 ______________________
    # when no face is detected, waits for seconds before closing all windows and waits for another human.
    elif perf_counter() - start_time_window_shown > WAIT_TILL_FEED_DISPLAY_AFTER_FACE_DETECTED:
        # it is time to hide cam feed and enter next level with animation.
        cv2.destroyAllWindows()
        start_time_window_hidden = perf_counter()
        photo_taken = False

    key = cv2.waitKey(1) & 0xFF

    # if the 'q' or ESC key is pressed, stop the loop
    if key == ord("q") or key == 27:
        break

# close all windows
cv2.destroyAllWindows()
