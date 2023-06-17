import cv2
import numpy as np
import time
import threading
import math

# implement guidance system init once in auto


class FrontEnd(object):

    def __init__(self):
        self.frame = None
        self.designator_frame = None
        self.FRAME_WIDTH = 960
        self.FRAME_HEIGHT = 720
        self.CENTRE_X = int(FRAME_WIDTH / 2)
        self.CENTRE_Y = int(FRAME_HEIGHT / 2)
        self.FONT = cv2.FONT_HERSHEY_COMPLEX
        self.FONT_SCALE = .6
        self.RED = (0, 0, 255)
        self.GREEN = (0, 255, 0)
        self.BLUE = (255, 0, 0)
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.UI_COLOUR = WHITE
        self.LINE_THICKNESS = 1

    def update(self, frame):
        self.frame = frame
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        self.designator_frame = self.frame.copy()

        # fps
        fps = self.backend.get_fps()
        fps_size = cv2.getTextSize("FPS  {}".format(
            fps), self.FONT, self.FONT_SCALE, self.LINE_THICKNESS)[0][0]
        cv2.putText(self.frame, "FPS  {}".format(fps), (self.FRAME_WIDTH -
                    fps_size - 5, 25), self.FONT, self.FONT_SCALE, self.UI_COLOUR, self.LINE_THICKNESS)

        # top left
        cv2.putText(self.frame, "PWR   {}%".format(self.backend.get_battery()),
                    (5, 25), self.FONT, self.FONT_SCALE, self.UI_COLOUR, self.LINE_THICKNESS)
        cv2.putText(self.frame, "TMP  {} C".format(self.backend.get_barometer()),
                    (5, 55), self.FONT, self.FONT_SCALE, self.UI_COLOUR, self.LINE_THICKNESS)

        # crosshair
        cv2.line(self.frame, (self.CENTRE_X - 20, self.CENTRE_Y),
                 (self.CENTRE_X - 10, self.CENTRE_Y), self.UI_COLOUR, 2)
        cv2.line(self.frame, (self.CENTRE_X + 20, self.CENTRE_Y),
                 (self.CENTRE_X + 10, self.CENTRE_Y), self.UI_COLOUR, 2)
        cv2.line(self.frame, (self.CENTRE_X, self.CENTRE_Y - 20),
                 (self.CENTRE_X, self.CENTRE_Y - 10), self.UI_COLOUR, 2)
        cv2.line(self.frame, (self.CENTRE_X, self.CENTRE_Y + 20),
                 (self.CENTRE_X, self.CENTRE_Y + 10), self.UI_COLOUR, 2)

        # crosshair stats
        spd_size = cv2.getTextSize(
            "SPD  {} CM/S".format(self.backend.get_speed_mag()), self.FONT, self.FONT_SCALE, self.LINE_THICKNESS)[0][0]
        cv2.putText(self.frame, "SPD  {} CM/S".format(self.backend.get_speed_mag()), ((self.CENTRE_X) - 90 -
                    spd_size, (self.CENTRE_Y) - 100), self.FONT, self.FONT_SCALE, self.UI_COLOUR, self.LINE_THICKNESS)
        cv2.putText(self.frame, "ALT  {:.1f} FT".format(self.backend.get_altitude()), ((
            self.CENTRE_X) + 90, (self.CENTRE_Y) - 100), self.FONT, self.FONT_SCALE, self.UI_COLOUR, self.LINE_THICKNESS)

        # bottom left telemtry
        cv2.putText(self.frame, "BRM  {}".format(self.backend.get_barometer()),
                    (5, self.FRAME_HEIGHT - 100), self.FONT, self.FONT_SCALE, self.UI_COLOUR, self.LINE_THICKNESS)
        cv2.putText(self.frame, "SPD  {}  {}  {}".format(self.backend.get_speed_x(), self.backend.get_speed_y(
        ), self.backend.get_speed_z()), (5, self.FRAME_HEIGHT - 70), self.FONT, self.FONT_SCALE, self.UI_COLOUR, self.LINE_THICKNESS)
        cv2.putText(self.frame, "ACC  {}  {}  {}".format(self.backend.get_acceleration_x(), self.backend.get_acceleration_y(
        ), self.backend.get_acceleration_z()), (5, self.FRAME_HEIGHT - 40), self.FONT, self.FONT_SCALE, self.UI_COLOUR, self.LINE_THICKNESS)
        cv2.putText(self.frame, "YPR  {}  {}  {}".format(self.backend.get_yaw(), self.backend.get_pitch(
        ), self.backend.get_roll()), (5, self.FRAME_HEIGHT - 10), self.FONT, self.FONT_SCALE, self.UI_COLOUR, self.LINE_THICKNESS)

        time_size = cv2.getTextSize(
            "T + {}".format(self.backend.get_flight_time()), self.FONT, self.FONT_SCALE, self.LINE_THICKNESS)[0][0]
        cv2.putText(self.frame, "T + {}".format(self.backend.get_flight_time()),
                    (self.FRAME_WIDTH - time_size - 5, 55), self.FONT, self.FONT_SCALE, self.UI_COLOUR, self.LINE_THICKNESS)

        # bottom compass
        cv2.circle(self.frame, (self.FRAME_WIDTH - 60, self.FRAME_HEIGHT - 60),
                   50, UI_COLOUR, 1)
        cv2.arrowedLine(self.frame, (self.FRAME_WIDTH - 60, self.FRAME_HEIGHT - 60), (int(-50 * math.cos(math.radians(self.backend.get_yaw() + 90)) +
                        self.FRAME_WIDTH - 60), int((self.FRAME_HEIGHT - 60) - (50 * math.sin(math.radians(self.backend.get_yaw() + 90))))), self.UI_COLOUR, 1, tipLength=.15)

        # top center
        if (self.KC_manual and not self.GS_active):
            cv2.rectangle(self.frame, (self.CENTRE_X - 20, 10),
                          (self.CENTRE_X + 29, 28), self.UI_COLOUR, -1)
            cv2.putText(self.frame, "CTRL", (self.CENTRE_X - 20, 25),
                        self.FONT, self.FONT_SCALE, self.BLACK, self.LINE_THICKNESS)
        else:
            cv2.rectangle(self.frame, (self.CENTRE_X - 20, 10),
                          (self.CENTRE_X + 31, 28), self.UI_COLOUR, -1)
            cv2.putText(self.frame, "AUTO", (self.CENTRE_X - 20, 25),
                        self.FONT, self.FONT_SCALE, self.BLACK, self.LINE_THICKNESS)

        # designator cursor
        if not self.tracker.active:
            cv2.rectangle(self.designator_frame, (cursor_control.cursor_pos[0], cursor_control.cursor_pos[1]), (
                cursor_control.cursor_pos[0] + manual_control.designator_roi_size[0], cursor_control.cursor_pos[1] + manual_control.designator_roi_size[1]), self.UI_COLOUR, 1)
            # top
            cv2.line(self.designator_frame, (cursor_control.cursor_pos[0] + manual_control.designator_roi_size[0] // 2, cursor_control.cursor_pos[1]),
                     (cursor_control.cursor_pos[0] + manual_control.designator_roi_size[0] // 2, 0), self.UI_COLOUR, 1)
            # left
            cv2.line(self.designator_frame, (cursor_control.cursor_pos[0], cursor_control.cursor_pos[1] + manual_control.designator_roi_size[1] // 2),
                     (0, cursor_control.cursor_pos[1] + manual_control.designator_roi_size[1] // 2), self.UI_COLOUR, 1)
            # right
            cv2.line(self.designator_frame, (cursor_control.cursor_pos[0] + manual_control.designator_roi_size[0], cursor_control.cursor_pos[1] + manual_control.designator_roi_size[1] // 2),
                     (self.FRAME_WIDTH, cursor_control.cursor_pos[1] + manual_control.designator_roi_size[1] // 2), self.UI_COLOUR, 1)
            # bottom
            cv2.line(self.designator_frame, (cursor_control.cursor_pos[0] + manual_control.designator_roi_size[0] // 2, cursor_control.cursor_pos[1] + manual_control.designator_roi_size[1]),
                     (cursor_control.cursor_pos[0] + manual_control.designator_roi_size[0] // 2, self.FRAME_HEIGHT), self.UI_COLOUR, 1)

        # active tracking / lock
        if tracker.active:
            x, y, w, h = tracker.get_bbox()
            if (self.CENTRE_X > x and self.CENTRE_X < x + w and self.CENTRE_Y > y and self.CENTRE_Y < y + h and not manual_control.manual):
                self.guidance_system.lock = True
                lock_size = cv2.getTextSize(
                    "LOCK", self.FONT, self.FONT_SCALE, self.LINE_THICKNESS)[0][0]
                cv2.rectangle(self.frame, (self.CENTRE_X - (lock_size // 2), self.FRAME_HEIGHT - 38),
                              (self.CENTRE_X + lock_size - 25, self.FRAME_HEIGHT - 20), self.UI_COLOUR, -1)
                cv2.putText(self.frame, "LOCK", (self.CENTRE_X - (lock_size // 2),
                            self.FRAME_HEIGHT - 22), self.FONT, self.FONT_SCALE, self.BLACK, self.LINE_THICKNESS)
            else:
                self.guidance_system.lock = False
                trk_size = cv2.getTextSize(
                    "TRK", self.FONT, self.FONT_SCALE, self.LINE_THICKNESS)[0][0]
                cv2.rectangle(self.frame, (self.CENTRE_X - (trk_size // 2), self.FRAME_HEIGHT - 38),
                              (self.CENTRE_X + trk_size - 20, self.FRAME_HEIGHT - 20), self.UI_COLOUR, -1)
                cv2.putText(self.frame, "TRK", (self.CENTRE_X - (trk_size // 2),
                            self.FRAME_HEIGHT - 22), self.FONT, self.FONT_SCALE, self.BLACK, self.LINE_THICKNESS)

            cv2.line(self.frame, (x, y), (x + 20, y),
                     self.RED if manual_control.dive else self.UI_COLOUR, 2)
            cv2.line(self.frame, (x, y), (x, y + 20),
                     self.RED if manual_control.dive else self.UI_COLOUR, 2)
            cv2.line(self.frame, (x, y + h), (x, y + h - 20),
                     self.RED if manual_control.dive else self.UI_COLOUR, 2)
            cv2.line(self.frame, (x, y + h), (x + 20, y + h),
                     self.RED if manual_control.dive else self.UI_COLOUR, 2)

            cv2.line(self.frame, (x + w, y), (x + w - 20, y),
                     self.RED if manual_control.dive else self.UI_COLOUR, 2)
            cv2.line(self.frame, (x + w, y), (x + w, y + 20),
                     self.RED if manual_control.dive else self.UI_COLOUR, 2)
            cv2.line(self.frame, (x + w, y + h), (x + w, y + h - 20),
                     self.RED if manual_control.dive else self.UI_COLOUR, 2)
            cv2.line(self.frame, (x + w, y + h), (x + w - 20, y + h),
                     self.RED if manual_control.dive else self.UI_COLOUR, 2)

            cv2.circle(self.frame, (x + w // 2, y + h // 2), 3,
                       self.RED if manual_control.dive else self.UI_COLOUR, -1)
            # top
            cv2.line(self.frame, (x + w // 2, y),
                     (x + w // 2, 0), self.UI_COLOUR, 1)
            # left
            cv2.line(self.frame, (x, y + h // 2),
                     (0, y + h // 2), self.UI_COLOUR, 1)
            # right
            cv2.line(self.frame, (x + w, y + h // 2),
                     (self.FRAME_WIDTH, y + h // 2), self.UI_COLOUR, 1)
            # bottom
            cv2.line(self.frame, (x + w // 2, y + h),
                     (x + w // 2, self.FRAME_HEIGHT), self.UI_COLOUR, 1)

            return (self.frame, self.designator_frame)

    def get_frame_size(self):
        return (self.FRAME_WIDTH, self.FRAME_HEIGHT)

    def get_frame_centre(self):
        return (self.CENTRE_X, self.CENTRE_Y)

    def get_designator_frame(self):
        return self.designator_frame

    def get_frame(self):
        return self.frame
