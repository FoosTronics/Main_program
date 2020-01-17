"""
    Hoofdclass FoosTronics en main code. 
    De onderdelen voor beeldherkenning, AI en motor aansturing komen in dit bestand bijelkaar.
    In dit bestand bestaat voor grootendeels uit de regeling van de AI.

    File:
        main.py
    Date:
        16.1.2020
    Version:
        V1.1
    Author:
        Daniël Boon
        Kelvin Sweere
    Used_IDE:
        Visual Studio Code (Python 3.6.7 64-bit)

    Version:
        1.1:
            functie: _initAISettings() toegevoegd voor de parameters van de AI in de init.
""" 
#pylint: disable=E1101

from src.KeeperSim import KeeperSim
from src.Backend.Framework import main
# import src.Backend.DeepQLearning as DQL
from src.Backend.DeepQLearning import DQLBase
# from src.Backend.USB import Commands
from src.Controller import Controller

import matplotlib.pylab as plt
import numpy as np

import time
from src.FindContours import FindContours
from src.BallDetect import BallDetection

#TODO temp...
from glob import glob
import os

class Foostronics:
    def __init__(self, keeper_sim):
        """initialisatie main.
           bestaat voornamelijk uit AI initialisatie.
        
        Args:
            keeper_sim (class): adress van draaiende keeper simulatie om variabelen op te halen.
        """

        self.fc = FindContours()

        #TODO temp...
        self.files = glob("C:\\Users\\" + os.getlogin() + "\\Stichting Hogeschool Utrecht\\NLE - Documenten\\Test foto's\\V1.3 cam normal Wide angle + ball\\output_fast.avi")
        for file in self.files:  #check per file
            self.bd = BallDetection(file) #maak class aan
    
        # self.bd = BallDetection()
        self.dql = DQLBase()
        # self.DQL = DQL
        self.ks = KeeperSim()

        try:
            self.con = Controller()
            self.met_drivers = True
        except:
            self.met_drivers = False
        
        img = self.bd.getFrame()
        self.HEIGHT_IMG, self.WIDTH_IMG, _ = img.shape
        # TODO: BeeldKoppeling wordt vervangen
        # self.bk = BeeldKoppeling(debug_flag=True)     # class die de beeldherkenning afhandeld. debug_flag=True (trackbars worden afgemaakt).

        self.hl, = plt.plot([], [])
        self.points_array = []

    def _convert2SimCor(self, x_p, y_p):
        """Zet de pixel positie van de beeldherkenning om naar pixel positie van de simulatie.
        """
        # x_simulatie posite
        x_s = self.mapFunction(x_p, 0, self.WIDTH_IMG, -19.35, 19.35)
        y_s = self.mapFunction(y_p, 0, self.HEIGHT_IMG, 17.42, 0)

        return x_s, y_s
    
    def mapFunction(self, val, in_min, in_max, out_min, out_max):
        """Map functie (zoals in de Arduino IDE) die input schaald in verhouding naar de output.
        
        Args:
            val (int): waarde die geschaald moet worden.
            in_min (int): minimale waarde die de input kan hebben.
            in_max (int): maximale waarde die de input kan hebben.
            out_min (int): minimale waarde die de output mag krijgen.
            out_max (int): maximale waarde die de output mag krijgen.
        
        Returns:
            int: Geschaalde waarde van de input.
        """
        return (val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    def executeAction(self, action, old_action):
        

        if np.array_equal(action, self.dql.possible_actions[0]):
            ks.control.y = ks.KEEPER_SPEED
            if(self.met_drivers and (not np.array_equal(action, old_action))):
                #TODO iets anders...
                self.con.driver.transceive_message(0, Commands.STOP)
                self.con.driver.transceive_message(0, Commands.JOG_MIN)

        elif np.array_equal(action, self.dql.possible_actions[1]):
            ks.control.y = -ks.KEEPER_SPEED
            if(self.met_drivers and (not np.array_equal(action, old_action))):
                #TODO iets anders...
                self.con.driver.transceive_message(0, Commands.STOP)
                self.con.driver.transceive_message(0, Commands.JOG_PLUS)
        else:
            ks.control.y = 0
            ks.body.linearVelocity.y = 0

        if np.array_equal(action, self.dql.possible_actions[2]):
            ks.control.y = 0
            ks.body.linearVelocity.y = 0
            
            if(self.met_drivers):
                #TODO iets anders...
                self.con.driver.transceive_message(0, Commands.STOP)
                self.con.shoot()
        
        if np.array_equal(action, self.dql.possible_actions[3]):
            ks.control.x = 0
            ks.control.y = 0
            ks.body.linearVelocity.x = 0
            ks.body.linearVelocity.y = 0
            if(self.met_drivers):
                #TODO iets anders...
                self.con.driver.transceive_message(0, Commands.STOP)


    def determineGoal(self, vel_x, vel_x_old):
        done = 0
        goal = 0

        if((ks.ball.position.x < -18) and (ks.ball.position.y < 11.26) and (ks.ball.position.y > 6.16)):
            #self.bk.center
            goal = 1
            done = 1
            ks.goals += 1
            self.points_array.append(0)
            if (len(self.points_array)>100):
                self.points_array.pop(0)
            self.ratio = (100*self.points_array.count(1))/len(self.points_array)
            
            
        elif((vel_x_old < 0) and (vel_x > 0) and (ks.ball.position.x < -13) and (ks.ball.position.y < 11.26) and (ks.ball.position.y > 6.16)):#ball.position):
            goal = 0
            done = 1
            ks.blocks += 1
            self.points_array.append(1)
            if (len(self.points_array)>100):
                self.points_array.pop(0)
            self.ratio = (100*self.points_array.count(1))/len(self.points_array)
        
        return done, goal

    # TODO opdelen in functies en waarom staat dit niet in de simulatie files?
    def run(self, ball, keeper, target, goals, blocks):
        """Deze functie wordt om iedere frame aangeroepen en kan gezien worden als de mainloop.
        
        Args:
            ball (Box2D object): Box2D object voor ball positie uitlezen
            keeper (Box2D object): Box2D object voor aansturen keeper door AI
            target (int): gewenste y positie van keeper om bal tegen te houden
            goals (int): totaal aantal goals
            blocks (int): totaal aantal ballen tegengehouden
        
        Returns:
            ball (Box2D object): update nieuwe ball positie in simulatie
            keeper (Box2D object): update nieuwe keeper aansturing in simulatie
            action (int): update gekozen actie van AI in simulatie

        """


        #TODO iets met FindContours doen...

        cor = self.bd.getball_pos()
        ball.position = self._convert2SimCor(cor[0], cor[1])

        action, old_action, target, vel_x, vel_x_old = self.dql.get_ai_action()

        if(ks.tp):
            ks.DeleteTargetpoint()
        
        if(not np.isnan(target)):
            self.ks.CreateTargetpoint((-15, target))
        
        self.executeAction(action, old_action)

        done, goal = self.determineGoal(vel_x, vel_x_old)

        if(done):
            episode_rewards, total_reward = self.dql.prepareNewRound(goal, ks.ball, ks.body)

            self.hl.set_xdata(np.append(self.hl.get_xdata(), (len(total_reward)-1)))
            self.hl.set_ydata(np.append(self.hl.get_ydata(), np.sum(episode_rewards)))                    
            plt.axis([0, len(total_reward), min(total_reward), max(total_reward)])
            plt.draw()
            plt.pause(0.0001)
            plt.show

            if(self.met_drivers):
                #TODO iets anders...
                self.con.driver.transceive_message(0, Commands.STOP)
                if(keeper.position.y >=8.71):
                    self.con.go_home()
                else:
                    self.con.go_home(1)
        else:
            self.dql.updateData(done, ks.ball, ks.body)        

        return ball, keeper, action


if __name__ == "__main__":
    """start main code
    """
    ks = KeeperSim()
    ks.set_Foostronics(Foostronics)
    main(ks)
