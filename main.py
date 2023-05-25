from djitellopy import Tello
import cv2, math, time, threading
import numpy as np
from pynput import keyboard
from pid import PID
from simple_pid import PID as PID2
import matplotlib.pyplot as plt

init_alt = 0
relative_alt = 0
spd_mag = 0
default_dist = 30

WIDTH = 960
HEIGHT = 720
CENTRE_X = WIDTH // 2
CENTRE_Y = HEIGHT // 2
start_time = time.time()
FONT = cv2.FONT_HERSHEY_COMPLEX
FONT_SCALE = .6
RED = (0, 0, 255)
GREEN = (0, 255, 0)
BLUE = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LINE_THICKNESS = 1
roi_colour = WHITE
manual_control = True
empty_frame = None

tracker_lock = threading.Lock()
track_thread_active = False
reset_track = False
tracker_thread = None
tracking = False
roi = None
tracker_ret = False
first_point = None
second_point = None
point_counter = 0
lock = False

flt_ctrl_active = False
flt_ctrl_lock = threading.Lock()
flight_ctrl_thread = None

# ku = 0.5
# tu = 1.20
# kp = 0.6 * ku
# ki = 1.2 * ku / tu
# kd = 3 * ku * tu / 40

YAW_PID = [0.25, 0, 0]
Y_PID = [0.1, 0.1, 0.1]
X_PID = [0.1, 0.1, 0.1]

yaw_pid_array = []

drone = Tello()

try:
    drone.connect()
    if (drone.get_battery() < 20):
        print("[DRONE] - Low battery")
        drone.end()
except:
    print("[DRONE] - Connection Error")

time.sleep(1)

try:
    drone.streamon()
    time.sleep(1)
    frame_read = drone.get_frame_read()
except:
    print("[DRONE] - No feed signal")

def guidance_system():
    global CENTRE_X, CENTRE_Y, drone, yaw_pid, y_pid, x_pid, roi, tracker_ret, flt_ctrl_lock, flt_ctrl_active, tracking, manual_control, lock
    try:
        print("[FLT CTRL] - ACTIVE")
        #yaw_pid = PID(YAW_PID[0], YAW_PID[1], YAW_PID[2], CENTRE_X, -100, 100, True)
        yaw_pid = PID2(YAW_PID[0], YAW_PID[1], YAW_PID[2], setpoint=CENTRE_X, output_limits=(-100,100))
        y_pid = PID2(Y_PID[0], Y_PID[1], Y_PID[2], setpoint=CENTRE_Y, output_limits=(-80,100))
        #x_pid = PID(X_PID[0], X_PID[1], X_PID[2], CENTRE_X, -90, 90, True)

        while tracking and tracker_ret and manual_control == False:
            x, y, w, h = [int(value) for value in roi]
            targetX = x + w // 2
            targetY = y + h // 2
            roiArea = (x + w) * (y + h) // 2
            
            #yaw_velocity = yaw_pid.compute(targetX)
            yaw_velocity = int(yaw_pid(targetX))
            #x_velocity = yaw_pid.compute(targetX)
            y_velocity = int(y_pid(targetY))

            if (lock):
                z_spd = 15
            else:
                z_spd = 0

            #print("YAW: {}".format(yaw_velocity))
            if drone.send_rc_control:
            #    if (x_velocity > 40):
            #        drone.send_rc_control(-x_velocity, 0, y_velocity, 0)
            #    else:
                drone.send_rc_control(0, 0, y_velocity, -yaw_velocity)

        #yaw_pid.reset()
        #y_pid.reset()
        flt_ctrl_lock.acquire()
        flt_ctrl_active = False
        flt_ctrl_lock.release()
        drone.send_rc_control(0, 0, 0, 0)
        print("[FLT CTRL] - TERMINATED")

    except Exception as error:
        yaw_pid.reset()
        flt_ctrl_lock.acquire()
        flt_ctrl_active = False
        manual_control = False
        flt_ctrl_lock.release()
        print("[FLT CTRL] - Error occured\n", error)

def manual_controller(key):
    global manual_control, drone, default_dist
    try:
        if key.char == 'z':
            if manual_control:
                manual_control = False
            else:
                manual_control = True
                drone.send_rc_control(0, 0, 0, 0)

        if manual_control:
            if key.char == 'i':
                drone.send_rc_control(0, 0, 0, 0)
                drone.takeoff()
            elif key.char == 'k':
                drone.land()
            elif key.char == 'w':
                drone.move_forward(default_dist)
            elif key.char == 'a':
                drone.move_left(default_dist)
            elif key.char == 'd':
                drone.move_right(default_dist)
            elif key.char == 's':
                drone.move_back(default_dist)
            elif key.char == 'q':
                drone.rotate_counter_clockwise(default_dist)
            elif key.char == 'e':
                drone.rotate_clockwise(default_dist)
            elif key.char == 'up':
                drone.move_up(default_dist)
            elif key.char == 'down':
                drone.move_down(default_dist)
    except:
        print("[MNUL CTRL] - Invalid key")

def on_release(key):
    if key == keyboard.Key.esc:
        return False 

def mouse_event_handler(event, x, y, flags, param):
    global tracker, tracking, point_counter, first_point, second_point, reset_track
    if event == cv2.EVENT_LBUTTONDOWN:
        if point_counter == 0:
            #print("[TRACK] - P1: ({}, {})".format(x,y))
            first_point = (x, y)
            point_counter += 1
        if point_counter == 1 and (x,y) != first_point:
            #print("[TRACK] - P2: ({}, {})".format(x,y))
            second_point = (x, y)
            point_counter += 1
        if tracking and point_counter == 2:
            point_counter = 0
            first_point = None
            second_point = None
            tracking = False
            reset_track = True
            #print("[TRACK] - ROI RESET")
        if point_counter == 2:
            reset_track = False
            tracker = cv2.legacy.TrackerCSRT_create()
            tracker.init(empty_frame, (first_point[0], first_point[1], abs(second_point[0] - first_point[0]), abs(second_point[1] - first_point[1])))
            tracking = True

def tracker_control():
    global tracking, empty_frame, tracker, roi, tracker_ret, track_thread_active, reset_track, point_counter, drone
    tracker_lock.acquire()
    track_thread_active = True
    while tracking:
        tracker_ret, roi = tracker.update(empty_frame)
        if tracker_ret == False or reset_track:
            tracking = False
            point_counter = 0

    track_thread_active = False
    tracker_thread = None
    tracker_lock.release()
    drone.send_rc_control(0, 0, 0, 0)
    print("[TRACK] - TRACKING TERMINATED")

cv2.namedWindow("FEED", cv2.WINDOW_NORMAL)
cv2.moveWindow("FEED", int((1920 // 2) - (WIDTH // 2)), int(( 1080 // 2) - ( HEIGHT // 2)))
cv2.setMouseCallback("FEED", mouse_event_handler)

key_listener = keyboard.Listener(on_press=manual_controller, on_release=on_release)
key_listener.start()
init_alt = drone.get_barometer()

while True:
    try:
        frame = frame_read.frame
        timer = cv2.getTickCount()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        empty_frame = frame.copy()

        # top right (fps)
        elapsed_time = time.time() - start_time
        fps = 1 / elapsed_time
        fps_size = cv2.getTextSize("FPS  {}".format(str(int(fps))), FONT, FONT_SCALE, LINE_THICKNESS)[0][0]
        cv2.putText(frame, "FPS  {}".format(str(int(fps))), (WIDTH - fps_size - 5, 25), FONT, FONT_SCALE, WHITE, LINE_THICKNESS)

        relative_alt = (drone.get_barometer() - init_alt) * 0.0328
        spd_mag = int(math.sqrt(drone.get_speed_x() ** 2 + drone.get_speed_y() ** 2 + drone.get_speed_z() ** 2))

        # top left
        cv2.putText(frame, "PWR   {}%".format(drone.get_battery()), (5, 25), FONT, FONT_SCALE, WHITE, LINE_THICKNESS)
        cv2.putText(frame, "TMP  {} C".format(drone.get_temperature()), (5, 55), FONT, FONT_SCALE, WHITE, LINE_THICKNESS)

        # crosshair
        cv2.line(frame, (int(WIDTH / 2) - 30, int(HEIGHT / 2)), (int(WIDTH / 2) - 10, int(HEIGHT / 2)), WHITE, 2)
        cv2.line(frame, (int(WIDTH / 2) + 30, int(HEIGHT / 2)), (int(WIDTH / 2) + 10, int(HEIGHT / 2)), WHITE, 2)
        cv2.line(frame, (int(WIDTH / 2), int(HEIGHT / 2) - 30), (int(WIDTH / 2), int(HEIGHT / 2) - 10), WHITE, 2)
        cv2.line(frame, (int(WIDTH / 2), int(HEIGHT / 2) + 30), (int(WIDTH / 2), int(HEIGHT / 2) + 10), WHITE, 2)

        #crosshair stats
        spd_size = cv2.getTextSize("SPD  {} CM/S".format(abs(spd_mag)), FONT, FONT_SCALE, LINE_THICKNESS)[0][0]
        cv2.putText(frame, "SPD  {} CM/S".format(abs(spd_mag)), ((WIDTH // 2) - 90 - spd_size, (HEIGHT // 2) - 100), FONT, FONT_SCALE, WHITE, LINE_THICKNESS)
        cv2.putText(frame, "ALT  {:.1f} FT".format(relative_alt), ((WIDTH // 2) + 90, (HEIGHT // 2) - 100), FONT, FONT_SCALE, WHITE, LINE_THICKNESS)

        # bottom left telemtry
        cv2.putText(frame, "SPD  {}  {}  {}".format(drone.get_speed_x(), drone.get_speed_y(), drone.get_speed_z()), (5, HEIGHT - 70), FONT, FONT_SCALE, WHITE, LINE_THICKNESS)
        cv2.putText(frame, "ACC  {}  {}  {}".format(drone.get_acceleration_x(), drone.get_acceleration_y(), drone.get_acceleration_z()), (5, HEIGHT - 40), FONT, FONT_SCALE, WHITE, LINE_THICKNESS)
        cv2.putText(frame, "YPR  {}  {}  {}".format(drone.get_yaw(), drone.get_pitch(), drone.get_roll()), (5, HEIGHT - 10), FONT, FONT_SCALE, WHITE, LINE_THICKNESS)

        time_size = cv2.getTextSize("T + {}".format(drone.get_flight_time()), FONT, FONT_SCALE, LINE_THICKNESS)[0][0]
        cv2.putText(frame, "T + {}".format(drone.get_flight_time()), (WIDTH - time_size - 5, 55), FONT, FONT_SCALE, WHITE, LINE_THICKNESS)


        # bottom compass
        cv2.circle(frame, (WIDTH - 60, HEIGHT - 60), 50, WHITE, 1)
        cv2.arrowedLine(frame, (WIDTH - 60, HEIGHT - 60), (round(-50 * math.cos(math.radians(drone.get_yaw())) + WIDTH - 60), round((HEIGHT - 60) - (50 * math.sin(math.radians(drone.get_yaw()))))), WHITE, 1, tipLength = .2)

        # top center
        if (manual_control and flt_ctrl_active == False):
            cv2.rectangle(frame, (WIDTH//2 - 20, 10), (WIDTH//2 + 29, 28), WHITE, -1)
            cv2.putText(frame, "CTRL", (WIDTH//2 - 20, 25), FONT, FONT_SCALE, BLACK, LINE_THICKNESS)
        else:
            cv2.rectangle(frame, (WIDTH//2 - 20, 10), (WIDTH//2 + 31, 28), WHITE, -1)
            cv2.putText(frame, "AUTO", (WIDTH//2 - 20, 25), FONT, FONT_SCALE, BLACK, LINE_THICKNESS)

        if tracking and track_thread_active == False:
            print("[TRACK] - TRACKING ACTIVE")
            tracker_thread = threading.Thread(target=tracker_control, daemon=True)
            tracker_thread.start()

        if tracking == False and track_thread_active == False and tracker_thread:
            print("[TRACK] - TRACKING RESET")
            tracker_thread = None

        # active tracking / lock
        if tracker_ret and tracking:
            # color the roi red when it is close to the centre
            x, y, w, h = [int(value) for value in roi]
            if (CENTRE_X >= x and CENTRE_X <= x + w and CENTRE_Y >= y and CENTRE_Y <= y + h):
                lock = True
                roi_colour = RED
                lock_size = cv2.getTextSize("LOCK", FONT, FONT_SCALE, LINE_THICKNESS)[0][0]
                cv2.rectangle(frame, (WIDTH // 2 - (lock_size // 2), HEIGHT - 38), (WIDTH // 2 + lock_size - 25, HEIGHT - 20), roi_colour, -1)
                cv2.putText(frame, "LOCK", (WIDTH // 2 - (lock_size // 2), HEIGHT - 22), FONT, FONT_SCALE, WHITE, LINE_THICKNESS)
            else:
                lock = False
                roi_colour = WHITE
                trk_size = cv2.getTextSize("TRK", FONT, FONT_SCALE, LINE_THICKNESS)[0][0]
                cv2.rectangle(frame, (WIDTH // 2 - (trk_size // 2), HEIGHT - 38), (WIDTH // 2 + trk_size - 20, HEIGHT - 20), WHITE, -1)
                cv2.putText(frame, "TRK", (WIDTH // 2 - (trk_size // 2), HEIGHT - 22), FONT, FONT_SCALE, BLACK, LINE_THICKNESS)

            cv2.rectangle(frame, (x, y), (x + w, y + h), roi_colour, 1)
            # top
            cv2.line(frame, (x + w // 2, y), (x + w // 2, 0), roi_colour, 1)
            # left
            cv2.line(frame, (x, y + h // 2), (0, y + h // 2), roi_colour, 1)
            # right
            cv2.line(frame, (x + w, y + h // 2), (WIDTH, y + h // 2), roi_colour, 1)
            # bottom
            cv2.line(frame, (x + w // 2, y + h), (x + w // 2, HEIGHT), roi_colour, 1)
                
            if flt_ctrl_active == False and manual_control == False:
                flight_ctrl_thread = threading.Thread(target=guidance_system, daemon=True)
                flight_ctrl_thread.start()
                flt_ctrl_active = True

    except Exception as error:
        print("[FEED] - Interface error\n", error)
    try:
        cv2.imshow("FEED", frame)
    except Exception as error:
        print("[FEED] - Display error\n", error)
        key_listener.join()
        drone.streamoff()
        drone.end()
        break

    start_time = time.time()
    
    if (cv2.waitKey(1) & 0xff) == 27:
        break

key_listener.join()
cv2.destroyAllWindows()
drone.streamoff()
drone.end()

if yaw_pid_array:
    plt.plot(yaw_pid_array)
    plt.show()

print("[DRONE] - CONNECTION TERMINATED")