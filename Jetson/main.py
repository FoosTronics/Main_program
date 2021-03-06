"""
    Hoofdklasse FoosTronics.
    De onderdelen voor beeldherkenning, AI en motor aansturing komen in dit bestand bijelkaar.

    File:
        main.py
    Date:
        23-1-2020
    Version:
        1.49
    Author:
        Daniël Boon
        Kelvin Sweere
        Chileam Bohnen
    Used_IDE:
        Visual Studio Code (Python 3.6.7 64-bit)
    Version management:
        1.1:
            functie: _initAISettings() toegevoegd voor de parameters van de AI in de init.
        1.2:
            Constantes zijn hoofdletters.
        1.3:
            objecten: ImageCapture, FindContours, BallDetect toegevoegd om de Raspi cam te gebruiken
        1.40:
            fixed moving keeper + dubble object keeper_sim
        1.41:
            Doxygen commentaar toegevoegd.
        1.42:
            Spelling en grammatica commentaar nagekeken
        1.43:
            go_home functie operationeel zonder hardware sensor voor home positie
        1.44:
            Proces van afbeelding ophalen tot positie van detecteren in een eigen Thread
        1.45:
            fixed te vaak achterelkaar goals maken
        1.46:
            mogelijke fix toegevoegd voor blocked niet kunnen registreren
        1.47:
            overtollig commetaar verwijdert 
        1.48:
            nieuwe feature ball wordt niet meer weergegeven in simulatie waneer uit het veld
        1.49:
            Loop toegevoegd zodat de simulatie niet opent wanneer de trackbars openstaan.
""" 
#pylint: disable=E1101

from src.ImageCapture import *
from src.FindContours import *
from src.BallDetect import *
from src.KeeperSim import *
from src.Controller import *

from src.Backend.Framework import main
from src.Backend.DeepQLearning import DQLBase

#import matplotlib.pylab as plt
import numpy as np

import cv2
import time
from threading import Thread
from queue import Queue
import sys

from glob import glob
import os

# False wanneer de camera gebruikt moet worden, True wanneer een video afgespeeld moet worden.
DEBUG_VIDEO = False


class Foostronics:
    """Klasse van de main applicatie.
    
    **Author**:       \n
        Daniël Boon   \n
        Kelvin Sweere \n
        Chileam Bohnen\n
        Sipke Vellinga\n
    **Version**:
        1.49          \n
    **Date**:
        23-1-2020 
    """
    def __init__(self, keeper_sim):
        """initialisatie main.
        
        Args:
            keeper_sim: (class) adres van draaiende keeper simulatie om variabelen op te halen.
        """
        if DEBUG_VIDEO:
            self.file = glob("D:\\Stichting Hogeschool Utrecht\\NLE - Documenten\\Test foto's\\new frame\\1.png")
            # self.file = glob("C:\\Users\\" + os.getlogin() + "\\Stichting Hogeschool Utrecht\\NLE - Documenten\\Test foto's\\V1.3 cam normal Wide angle + ball\\output_fast.avi")
            self.camera = ImageCapture(file=self.file[0])
        else:
            self.camera = ImageCapture()

        self.ks = keeper_sim
        # print(self.ks.screen)
        if not self.ks.shoot_bool:
            self.find_contours = FindContours()
            self.ball_detection = BallDetection()

        self.WIDTH_IMG = 640
        self.HEIGHT_IMG = 360

        self.dql = DQLBase()
        self.que = Queue(2)

        try:
            self.con = Controller()
            self.met_drivers = True
        except:
            self.met_drivers = False

        # self.hl, = plt.plot([], [])
        self.points_array = []
        self.scored = 0
        self.old_ball_positions = []
        self.reused_counter = 0

    def calibration(self):
        print("gebruik 'q' om kalibratie te stoppen, en 'n' om de simulatie te starten.")
        while True:
            # get new frame from camera buffer
            _frame = self.camera.get_frame()
            # set new frame in find_contours object for image cropping
            self.find_contours.new_img(_frame)

            # get cropped image from find_contours
            _field = self.find_contours.get_cropped_field()
            cv2.imshow("field", self.find_contours.drawing_img)

            # set height and width parameters
            self.HEIGHT_IMG, self.WIDTH_IMG, _ = _field.shape
            # set new cropped image in ball_detection object
            self.ball_detection.new_frame(_field)
            # get new ball position coordinates in image pixel values
            cor = self.ball_detection.getball_pos()
            cv2.imshow("ball detection", self.ball_detection.frame)
            # convert image pixel values to simulation values

            key = cv2.waitKey(5)
            if key == ord('q'):
                cv2.destroyAllWindows()
                return False
            elif key == ord('n'):
                cv2.destroyAllWindows()
                return True

    def start_get_ball_thread(self):
        """Opstarten van een nieuw proces die de functie update_ball_position uitvoert.
        """
        if self.calibration(): 
            ball_thread = Thread(target=self.update_ball_position, args=())
            ball_thread.daemon = True
            ball_thread.start()
        else:
            self.camera.camera.release()
            self.ks.running = False
            sys.exit()

    def update_ball_position(self):
        """Opstarten van bal detectie proces dat een afbeelding uit van de gstreamer of van een bestand haalt.
        Zie ImageCapture voor het ophalen van afbeeldingen, FindContours om het speelveld te schalen en BallDetect voor de bal detectie.
        """
        while True:
            if not self.ks.running:
                self.camera.camera.release()
                self.con.stop_controller_thread()
                cv2.destroyAllWindows()
                break

            if not self.que.full():
                # get new frame from camera buffer
                _frame = self.camera.get_frame()
                # set new frame in find_contours object for image cropping
                self.find_contours.new_img(_frame)

                # get cropped image from find_contours
                _field = self.find_contours.get_cropped_field()

                # set height and width parameters
                self.HEIGHT_IMG, self.WIDTH_IMG, _ = _field.shape
                # set new cropped image in ball_detection object
                self.ball_detection.new_frame(_field)
                # get new ball position coordinates in image pixel values
                cor = self.ball_detection.getball_pos()
                # convert image pixel values to simulation values
                self.que.put((self._convert2_sim_cor(cor[0], cor[1]), self.ball_detection.reused))
            cv2.waitKey(1)

    def _convert2_sim_cor(self, x_p, y_p):
        """Zet de pixel positie van de beeldherkenning verhoudingsgewijs om naar pixel positie van de simulatie.
        
        Args:
            x_p: (int) x coördinaat van de pixelpositie.
            y_p: (int) y coördinaat van de pixelpositie.
        
        Returns:
            (tuple) x & y coördinaten van de simulatie.
        """
        # x_simulatie posite
        x_s = self.map_function(x_p, 0, self.WIDTH_IMG, self.ks.SIM_LEFT, self.ks.SIM_RIGHT)    #-19.35, 19.35
        #y_s = self.map_function(y_p, 0, self.HEIGHT_IMG, self.ks.SIM_TOP, self.ks.SIM_BOTTOM)   #20, 0
        y_s = self.map_function(y_p, 0, self.HEIGHT_IMG, self.ks.SIM_BOTTOM, self.ks.SIM_TOP)
        return (x_s, y_s)
    
    def map_function(self, val, in_min, in_max, out_min, out_max):
        """Map functie (zoals in de Arduino IDE) die input waarde (in_min & in_max) schaald in verhouding naar de output (out_min & out_max).
        
        Args:
            val: (int) waarde die geschaald moet worden.
            in_min: (int) minimale waarde die de input kan hebben.
            in_max: (int) maximale waarde die de input kan hebben.
            out_min: (int) minimale waarde die de output mag krijgen.
            out_max: (int) maximale waarde die de output mag krijgen.
        
        Returns:
            (int) geschaalde waarde van de input.
        """
        return (val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def execute_action(self, action, old_action):
        """Voer de actie uit, die de AI heeft gekozen, op de stappenmotoren.
        
        Args:
            action: (list) acties die de AI gekozen heeft.
            old_action: (list) de vorige actie die de AI gekozen heeft.
        """
        if not self.con.que.full():
            if np.array_equal(action, self.dql.possible_actions[0]):
                self.ks.control.y = self.ks.KEEPER_SPEED
                if(self.met_drivers and (not np.array_equal(action, old_action))):
                    self.con.que.put(0)
                    #self.con.jog_motor(0) #JOG_MIN

            elif np.array_equal(action, self.dql.possible_actions[1]):
                self.ks.control.y = -self.ks.KEEPER_SPEED
                if(self.met_drivers and (not np.array_equal(action, old_action))):
                    self.con.que.put(1)
                    #self.con.jog_motor(1) #JOG_PLUS
            else:
                self.ks.control.y = 0
                self.ks.body.linearVelocity.y = 0

            if np.array_equal(action, self.dql.possible_actions[2]):
                self.ks.control.y = 0
                self.ks.body.linearVelocity.y = 0
                
                if(self.met_drivers):
                    self.con.que.put(2)
                    #self.con.stop_motor()
                    #self.con.shoot()
            
            if np.array_equal(action, self.dql.possible_actions[3]):
                self.ks.control.x = 0
                self.ks.control.y = 0
                self.ks.body.linearVelocity.x = 0
                self.ks.body.linearVelocity.y = 0
                if(self.met_drivers):
                    self.con.que.put(3)
                    #self.con.stop_motor()

    def determine_goal(self, vel_x, vel_x_old):
        """Bepaal of er een goal is gescoord.
        
        Args:
            vel_x: (int) huidige x coördinaat van de simulatie.
            vel_x_old: (int) vorige x coördinaat van de simulatie.
        
        Returns:
            (tuple) done, goal - done checkt of ronde klaar is met een bool, goal is een int die aantal goals optelt.
        """
        done = 0
        goal = 0

        if(len(self.old_ball_positions)<4):
            self.old_ball_positions.append(self.ks.ball.position)
        else:
            self.old_ball_positions.pop(0)
            self.old_ball_positions.append(self.ks.ball.position)
        
        if(
            ((self.ks.ball.position.x < -18.5) and (self.ks.ball.position.y < (self.ks.SIM_BOTTOM*2/3)) and (self.ks.ball.position.y > (self.ks.SIM_BOTTOM*1/3))) or 
            (self.ks.ball.position.x < self.ks.SIM_LEFT)
          ):
            if(not self.scored):
                self.old_ball_positions = []
                goal = 1
                done = 1
                self.ks.goals += 1
                self.points_array.append(0)
                if (len(self.points_array)>100):
                    self.points_array.pop(0)
                self.ks.ratio = (100*self.points_array.count(1))/len(self.points_array)
                self.ks.body.position = (-16.72,(self.ks.SIM_BOTTOM/2))
                if(self.ks.shoot_bool):
                    self.ks.world.DestroyBody(self.ks.ball)
                    self.ks._reset_ball()
                self.scored = 1
        elif(
              ((vel_x_old < 0) and (vel_x > 0) and (self.old_ball_positions[0].x < -7) and (self.old_ball_positions[0].y < (self.ks.SIM_BOTTOM*2/3)) and (self.old_ball_positions[0].y> (self.ks.SIM_BOTTOM*1/3))) or
              (self.ks.shoot_bool and ((abs(self.ks.ball.linearVelocity.x) < 1) or self.ks.ball.linearVelocity.x > 1))
            ):
            self.old_ball_positions = []
            goal = 0
            done = 1
            self.ks.blocks += 1
            self.points_array.append(1)
            if (len(self.points_array)>100):
                self.points_array.pop(0)
            self.ks.ratio = (100*self.points_array.count(1))/len(self.points_array)
            self.ks.body.position = (-16.72,(self.ks.SIM_BOTTOM/2))
            if(self.ks.shoot_bool):
                self.ks.world.DestroyBody(self.ks.ball)
                self.ks._reset_ball()
            self.scored = 0
        elif(self.scored):
            self.scored = 0
        
        return done, goal

    def run(self):
        """Deze functie wordt na iedere frame aangeroepen en kan gezien worden als de mainloop.
        """
        if(not self.ks.shoot_bool):
            #print(self.que.get())
            self.ks.ball.position, reused = self.que.get()
        action, old_action, target, vel_x, vel_x_old = self.dql.get_ai_action()
        self.ks.action = action
        
        self.execute_action(action, old_action)

        done, goal = self.determine_goal(vel_x, vel_x_old)  

        if done:
            episode_rewards, total_reward = self.dql.prepare_new_round(goal, self.ks.ball, self.ks.body)
            # print(np.sum(episode_rewards))
            # self.hl.set_xdata(np.append(self.hl.get_xdata(), (len(total_reward)-1)))
            # self.hl.set_ydata(np.append(self.hl.get_ydata(), np.sum(episode_rewards)))                    
            # plt.axis([0, len(total_reward), min(total_reward), max(total_reward)])
            # plt.draw()
            # plt.pause(0.0001)
            # plt.show

            if(self.met_drivers):
                #self.con.stop_motor()
                if not self.con.que.full():
                    if(self.ks.body.position.y >=8.71):
                        self.con.que.put(4)
                        #self.con.go_home()
                    else:
                        self.con.que.put(5)
                        #self.con.go_home(1)
        else:
            self.dql.update_data(done, self.ks.ball, self.ks.body)
        if(not self.ks.shoot_bool):
            if(reused):
                self.reused_counter += 1
                if(self.reused_counter > 5):
                    self.ks.ball.position = (200, 200)
            elif((not reused) and self.reused_counter):
                self.reused_counter = 0
        

if __name__ == "__main__":
    """start main code
    """
    keeperSim = KeeperSim()
    foosTronics = Foostronics(keeperSim)
    if not keeperSim.shoot_bool:
        foosTronics.ball_detection.create_trackbar()
        foosTronics.start_get_ball_thread()
        foosTronics.con.start_controller_thread()
    keeperSim.set_Foostronics(foosTronics)
    main(keeperSim)
