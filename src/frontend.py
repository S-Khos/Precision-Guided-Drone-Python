import cv2
import numpy as np
import time
import threading
import math
from backend import BackEnd


class FrontEnd(object):

    FRAME_WIDTH = 960
    FRAME_HEIGHT = 720
    CENTRE_X = int(FRAME_WIDTH / 2)
    CENTRE_Y = int(FRAME_HEIGHT / 2)
    FONT = cv2.FONT_HERSHEY_COMPLEX
    FONT_SCALE = .6
    RED = (0, 0, 255)
    GREEN = (0, 255, 0)
    BLUE = (255, 0, 0)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    UI_COLOUR = WHITE
    LINE_THICKNESS = 1

    def __init__(self, drone):
        self.frame = None
        self.drone = drone
        self.fps_init_time = time.time()
        self.backend = BackEnd(drone)

    def update(self, frame):
        try:
            self.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # top right (fps)
            fps = self.get_fps()
            fps_size = cv2.getTextSize("FPS  {}".format(
                str(int(fps))), FONT, FONT_SCALE, LINE_THICKNESS)[0][0]
            cv2.putText(frame, "FPS  {}".format(str(int(fps))), (FRAME_WIDTH -
                        fps_size - 5, 25), FONT, FONT_SCALE, UI_COLOUR, LINE_THICKNESS)

            # top left
            cv2.putText(frame, "PWR   {}%".format(self.backend.get_battery()),
                        (5, 25), FONT, FONT_SCALE, UI_COLOUR, LINE_THICKNESS)
            cv2.putText(frame, "TMP  {} C".format(self.backend.get_temperature()),
                        (5, 55), FONT, FONT_SCALE, UI_COLOUR, LINE_THICKNESS)

            # crosshair
            cv2.line(frame, (int(WIDTH / 2) - 20, int(HEIGHT / 2)),
                     (int(WIDTH / 2) - 10, int(HEIGHT / 2)), UI_COLOUR, 2)
            cv2.line(frame, (int(WIDTH / 2) + 20, int(HEIGHT / 2)),
                     (int(WIDTH / 2) + 10, int(HEIGHT / 2)), UI_COLOUR, 2)
            cv2.line(frame, (int(WIDTH / 2), int(HEIGHT / 2) - 20),
                     (int(WIDTH / 2), int(HEIGHT / 2) - 10), UI_COLOUR, 2)
            cv2.line(frame, (int(WIDTH / 2), int(HEIGHT / 2) + 20),
                     (int(WIDTH / 2), int(HEIGHT / 2) + 10), UI_COLOUR, 2)

            # crosshair stats
            spd_size = cv2.getTextSize(
                "SPD  {} CM/S".format(self.backend.get_speed_mag()), FONT, FONT_SCALE, LINE_THICKNESS)[0][0]
            cv2.putText(frame, "SPD  {} CM/S".format(self.backend.get_speed_mag()), ((WIDTH // 2) - 90 -
                        spd_size, (HEIGHT // 2) - 100), FONT, FONT_SCALE, ui_text_clr, LINE_THICKNESS)
            cv2.putText(frame, "ALT  {:.1f} FT".format(self.backend.get_altitude()), ((
                WIDTH // 2) + 90, (HEIGHT // 2) - 100), FONT, FONT_SCALE, ui_text_clr, LINE_THICKNESS)

            # bottom left
            cv2.putText(frame, "BRM  {}".format(self.backend.get_barometer()),
                        (5, HEIGHT - 100), FONT, FONT_SCALE, UI_COLOUR, LINE_THICKNESS)

            cv2.putText(frame, "SPD  {}  {}  {}".format(
                self.backend.get_speed_x(), self.backend.get_speed_y(), self.backend_get_speed_z()), (5, HEIGHT - 70), FONT, FONT_SCALE, ui_text_clr, LINE_THICKNESS)

            cv2.putText(frame, "ACC  {}  {}  {}".format(
                self.backend.get_acceleration_x(), self.backend.get_acceleration_y(), self.backend.get_acceleration_z()), (5, HEIGHT - 40), FONT, FONT_SCALE, ui_text_clr, LINE_THICKNESS)

            cv2.putText(frame, "YPR  {}  {}  {}".format(
                self.backend.get_yaw(), self.backend.get_pitch(), self.backend.get_roll()), (5, HEIGHT - 10), FONT, FONT_SCALE, ui_text_clr, LINE_THICKNESS)

            # top right
            time_size = cv2.getTextSize(
                "T + {}".format(self.backend.get_flight_time()), FONT, FONT_SCALE, LINE_THICKNESS)[0][0]
            cv2.putText(frame, "T + {}".format(self.backend.get_flight_time()),
                        (WIDTH - time_size - 5, 55), FONT, FONT_SCALE, ui_text_clr, LINE_THICKNESS)

            # bottom compass
            cv2.circle(frame, (WIDTH - 60, HEIGHT - 60), 50, ui_text_clr, 1)
            cv2.arrowedLine(frame, (WIDTH - 60, HEIGHT - 60), (int(-50 * math.cos(math.radians(self.backend.get_yaw() + 90)) +
                            WIDTH - 60), int((HEIGHT - 60) - (50 * math.sin(math.radians(self.backend.get_yaw() + 90))))), UI_COLOUR, 1, tipLength=.15)

        except Exception as error:
            print("[FEED] - UI ERROR\n", error)

    def get_fps(self):
        elapsed_time = time.time() - self.fps_init_time
        fps = 1 / elapsed_time
        return fps
