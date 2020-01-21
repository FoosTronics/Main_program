"""
    Hoofdklasse FoosTronics.
    De onderdelen voor beeldherkenning, AI en motor aansturing komen in dit bestand bijelkaar.

    File:
        main.py
    Date:
        20-1-2020
    Version:
        1.43
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

""" 
#pylint: disable=E1101

from src.ImageCapture import *
from src.FindContours import *
from src.BallDetect import *
from src.KeeperSim import *
from src.Controller import *

from src.Backend.USB import Commands
from src.Backend.Framework import main
# import src.Backend.DeepQLearning as DQL
from src.Backend.DeepQLearning import DQLBase

#import matplotlib.pylab as plt
import numpy as np

import cv2
import time

#TODO temp...
from glob import glob
import os

DEBUG_VIDEO = False

class Foostronics:
    """Klasse van de main applicatie.
    
    **Author**:       \n
       Daniël Boon    \n
        Kelvin Sweere \n
        Chileam Bohnen\n
    **Version**:
        1.42          \n
    **Date**:
        20-1-2020 
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
        self.find_contours = FindContours()
        self.ball_detection = BallDetection()
        self.ball_detection.create_trackbar()

        self.WIDTH_IMG = 640
        self.HEIGHT_IMG = 360

        #TODO temp...
        # self.files = glob("C:\\Users\\" + os.getlogin() + "\\Stichting Hogeschool Utrecht\\NLE - Documenten\\Test foto's\\V1.3 cam normal Wide angle + ball\\output_fast.avi")
        # for file in self.files:  #check per file
        #     self.bd = BallDetection(file) #maak class aan
        # img = self.bd.get_frame()
        # self.HEIGHT_IMG, self.WIDTH_IMG, _ = img.shape
        # # TODO: BeeldKoppeling wordt vervangen
        # # self.bk = BeeldKoppeling(debug_flag=True)     # class die de beeldherkenning afhandeld. debug_flag=True (trackbars worden afgemaakt).

        # self.bd = BallDetection()
        self.dql = DQLBase()
        # self.DQL = DQL
        self.ks = keeper_sim
        print(self.ks.screen)

        try:
            self.con = Controller()
            self.met_drivers = True
        except:
            self.met_drivers = False

        # self.hl, = plt.plot([], [])
        self.points_array = []

    def _convert2_sim_cor(self, x_p, y_p):
        """Zet de pixel positie van de beeldherkenning verhoudingsgewijs om naar pixel positie van de simulatie.
        
        Args:
            x_p: (int) x coördinaat van de pixelpositie.
            y_p: (int) y coördinaat van de pixelpositie.
        
        Returns:
            (tuple) x & y coördinaten van de simulatie.
        """
        # x_simulatie posite
        x_s = self.map_function(x_p, 0, self.WIDTH_IMG, -19.35, 19.35)
        y_s = self.map_function(y_p, 0, self.HEIGHT_IMG, 17.42, 0)

        return x_s, y_s
    
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

        if np.array_equal(action, self.dql.possible_actions[0]):
            self.ks.control.y = self.ks.KEEPER_SPEED
            if(self.met_drivers and (not np.array_equal(action, old_action))):
                #TODO iets anders...
                self.con.driver.transceive_message(0, Commands.STOP)
                self.con.driver.transceive_message(0, Commands.JOG_MIN)

        elif np.array_equal(action, self.dql.possible_actions[1]):
            self.ks.control.y = -self.ks.KEEPER_SPEED
            if(self.met_drivers and (not np.array_equal(action, old_action))):
                #TODO iets anders...
                self.con.driver.transceive_message(0, Commands.STOP)
                self.con.driver.transceive_message(0, Commands.JOG_PLUS)
        else:
            self.ks.control.y = 0
            self.ks.body.linearVelocity.y = 0

        if np.array_equal(action, self.dql.possible_actions[2]):
            self.ks.control.y = 0
            self.ks.body.linearVelocity.y = 0
            
            if(self.met_drivers):
                #TODO iets anders...
                self.con.driver.transceive_message(0, Commands.STOP)
                self.con.shoot()
        
        if np.array_equal(action, self.dql.possible_actions[3]):
            self.ks.control.x = 0
            self.ks.control.y = 0
            self.ks.body.linearVelocity.x = 0
            self.ks.body.linearVelocity.y = 0
            if(self.met_drivers):
                #TODO iets anders...
                self.con.driver.transceive_message(0, Commands.STOP)


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

        if((self.ks.ball.position.x < -18) and (self.ks.ball.position.y < 11.26) and (self.ks.ball.position.y > 6.16)):
            #self.bk.center
            goal = 1
            done = 1
            self.ks.goals += 1
            self.points_array.append(0)
            if (len(self.points_array)>100):
                self.points_array.pop(0)
            self.ratio = (100*self.points_array.count(1))/len(self.points_array)
            self.ks.body.position = (-16.72,10.0)
            
            
        elif((vel_x_old < 0) and (vel_x > 0) and (self.ks.ball.position.x < -13) and (self.ks.ball.position.y < 11.26) and (self.ks.ball.position.y > 6.16)):#ball.position):
            goal = 0
            done = 1
            self.ks.blocks += 1
            self.points_array.append(1)
            if (len(self.points_array)>100):
                self.points_array.pop(0)
            self.ratio = (100*self.points_array.count(1))/len(self.points_array)
            self.ks.body.position = (-16.72,10.0)
        
        return done, goal

    def run(self, ball, keeper, target, goals, blocks):
        """Deze functie wordt na iedere frame aangeroepen en kan gezien worden als de mainloop.
        
        Args:
            ball: (Box2D object) Box2D object voor ball positie uitlezen
            keeper: (Box2D object) Box2D object voor aansturen keeper door AI
            target: (int) gewenste y positie van keeper om bal tegen te houden
            goals: (int) totaal aantal goals
            blocks: (int) totaal aantal ballen tegengehouden
        
        Returns:
            ball: (Box2D object) update nieuwe ball positie in simulatie
            keeper: (Box2D object) update nieuwe keeper aansturing in simulatie
            action: (int) update gekozen actie van AI in simulatie
        """
        if not self.ks.running:
            self.camera.camera.release()
            cv2.destroyAllWindows()

        # get new frame from camera buffer
        _frame = self.camera.get_frame()
        # set new frame in find_contours object for image cropping
        self.find_contours.new_img(_frame)
        # get cropped image from find_contours
        _field = self.find_contours.get_cropped_field()
        cv2.imshow("field", self.find_contours.drawing_img)
        cv2.waitKey(1)

        # set height and width parameters
        self.HEIGHT_IMG, self.WIDTH_IMG, _ = _field.shape
        # set new cropped image in ball_detection object
        self.ball_detection.new_frame(_field)
        # get new ball position coordinates in image pixel values
        cor = self.ball_detection.getball_pos()
        # convert image pixel values to simulation values
        ball.position = self._convert2_sim_cor(cor[0], cor[1])

        action, old_action, target, vel_x, vel_x_old = self.dql.get_ai_action()

        if self.ks.tp:
            self.ks.delete_targetpoint()
        
        if not np.isnan(target):
            self.ks.create_targetpoint((-16.72, target))
        
        self.execute_action(action, old_action)

        done, goal = self.determine_goal(vel_x, vel_x_old)

        if done:
            episode_rewards, total_reward = self.dql.prepare_new_round(goal, self.ks.ball, self.ks.body)

            # self.hl.set_xdata(np.append(self.hl.get_xdata(), (len(total_reward)-1)))
            # self.hl.set_ydata(np.append(self.hl.get_ydata(), np.sum(episode_rewards)))                    
            # plt.axis([0, len(total_reward), min(total_reward), max(total_reward)])
            # plt.draw()
            # plt.pause(0.0001)
            # plt.show

            if(self.met_drivers):
                #TODO iets anders...
                self.con.driver.transceive_message(0, Commands.STOP)
                if(keeper.position.y >=8.71):
                    self.con.go_home()
                else:
                    self.con.go_home(1)
        else:
            self.dql.update_data(done, self.ks.ball, self.ks.body)

        return ball, keeper, action


if __name__ == "__main__":
    """start main code
    """
    keeperSim = KeeperSim()
    keeperSim.set_Foostronics(Foostronics)
    main(keeperSim)
