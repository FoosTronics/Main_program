# imports
import cv2
from ImageCapture import *
from BallDetectClass import *
from FindContours import *
from Controller import *

from extra.rst_lib import nothing

# if __name__ == "__main__":
#     from tkinter import *
"""
FoosTronics applicatie
    - gebruik een bestaande video of foto 

File:
    ImageProcessing.py
Date:
    15.11.2019
Version:
    V1.0
Authors:
    Chileam Bohnen
Used_IDE:
    PyCharm (Python 3.6.9 64-bit)
"""

class FoosTronics:
    """
    Applicatie die aan de hand van video of afbeeldingen een oranje tafelvoetbal bal traceert.
    Wanneer de richting van de bal kruist met het bereik van de keeper wordt de keeper verplaatst naar dit kruispunt.
    """

    def __init__(self):
        """
        Initalisatie applicatie object
        """
        self.debug      = False
        self.ball_color = 'orange'
        self.image_size = (640, 480)
        self.ball_positions = [(0, 0), (0, 0)]
        self.capture    = ImageCapture
        self.raster = Raster
        self.ballDetection = BallDetection
        self.controller = Controller
        self.running    = False

        self.KEEP_X = 25
        self.move_pos = 0
        self.LINE_Y_MIN = 140
        self.LINE_Y_MAX = 280

    def init_image_processing(self):
        """
        Initalisatie van applicatie onderdelen. En zet applicatie status op True
        """
        self.controller = Controller()
        self.capture = ImageCapture(self.image_size)
        self.raster = Raster(True)
        self.ballDetection = BallDetection()
        self.ballDetection.create_trackbar()
        self.running = True

    def process_image(self):
        """
        Applicatie procedure van af het ophalen van camera beelden tot het aansturen van de stepper motors
        """
        start_time = time.time()
        # haal een afbeelding uit het camera geheugen
        frame = self.capture.get_frame()
        print("get frame:", (time.time() - start_time) * 1000, "ms")

        start_time = time.time()
        # detecteer het voetbaltafel frame
        self.raster.new_img(frame)
        # verklein het beeld tot de contouren van het voetbalveld.
        field = self.raster.get_cropped_field()
        height, width, _ = field.shape
        self.controller.y_length = height
        self.controller.ratio_y_to_MM = (540 / height) 

        print("get cropped field:", (time.time() - start_time) * 1000, "ms")
        # het voetbalveld wordt geladen in de stepper motor controller
        self.controller.frame = field

        start_time = time.time()
        # het voetbalveld wordt geladen in een bal detectie object
        self.ballDetection.new_frame(field)
        self.ballDetection.get_trackbarpos()

        # positie van de gedetecteerde bal wordt opgehaald en de vorige positie wordt in een geheugen element geplaatst
        ball_pos = self.ballDetection.getball_pos()
        self.ball_positions[1] = self.ball_positions[0]
        self.ball_positions[0] = ball_pos
        print("get ball position:", (time.time() - start_time) * 1000, "ms")

        # self.ball_positions[0] = (cv2.getTrackbarPos("pos x1", "ball positions"), cv2.getTrackbarPos("pos y1", "ball positions"))
        # self.ball_positions[1] = (cv2.getTrackbarPos("pos x2", "ball positions"), cv2.getTrackbarPos("pos y2", "ball positions"))

        # bereik van de keeper wordt getekend
        cv2.line(field, (self.KEEP_X, self.LINE_Y_MIN), (self.KEEP_X, self.LINE_Y_MAX), (255, 0, 255), 3)

        print(self.ball_positions)
        # de houdige en vorige positie van de bal wordt geaccentueerd
        # cv2.circle(field, self.ball_positions[0], 10, (255, 0, 127), -1)
        # cv2.circle(field, self.ball_positions[1], 10, (255, 255, 127), -1)

        # de nieuwe positie voor de keeper wordt berekend m.b.v. extrapolation
        pos_keeper = self.controller.linear_extrapolation(pnt1=self.ball_positions[1], pnt2=self.ball_positions[0], value_x=self.KEEP_X, max_y=self.LINE_Y_MAX, min_y=self.LINE_Y_MIN)

        # print(pos_keeper)

        #
        if (pos_keeper != (None, None)):
            cv2.circle(field, (self.KEEP_X, int(pos_keeper[1])), 10, (255, 0, 0), -1)
            self.move_pos = int((pos_keeper[1] - self.LINE_Y_MIN) * (350 + 350) / (self.LINE_Y_MAX - self.LINE_Y_MIN) - 350)
            self.controller.new_pos[0] = self.move_pos

        start_time = time.time()
        cv2.imshow("table", self.ballDetection.frame)
        print("imshow:", (time.time() - start_time) * 1000, "ms")
        cv2.imshow("ball mask", self.ballDetection.mask)
        key = cv2.waitKey(1)
        if key == ord('q'):
            # stop application
            self.running = False
            self.controller.stopped = True

    def create_ball_positions(self, width, height):
        """
        Schuifbalk voor debug doeleinden. Met deze schuifbalken kunnen de balposities worden verplaatst.
        
        Args:
            width (int): De breedte van het voetbalveld in pixels
            height (int): De hoogte van het voetbalveld in pixels
        """
        cv2.namedWindow("ball positions")

        cv2.createTrackbar("pos x1", "ball positions", self.ball_positions[0][0], width, nothing)
        cv2.createTrackbar("pos y1", "ball positions", self.ball_positions[0][1], height, nothing)
        cv2.createTrackbar("pos x2", "ball positions", self.ball_positions[1][0], width, nothing)
        cv2.createTrackbar("pos y2", "ball positions", self.ball_positions[1][1], height, nothing)

    def exit(self):
        """
        Stoppen van applicatie
        
        Returns:
            bool: Geeft applicatie status True terug wanneer applicatie wordt afgesloten
        """
        return not self.running


if __name__ == "__main__":
    app = FoosTronics()
    app.init_image_processing()

    # master = Tk()
    # Button(master, text='SHOOT!', command=app.controller.shoot).pack()
    
    while app.running:
        # master.update_idletasks()
        # master.update()
        start_time = time.time()
        app.process_image()
        print("app time:", (time.time() - start_time) * 1000, "ms")

        if app.exit():
            break
