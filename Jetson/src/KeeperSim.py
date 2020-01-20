"""
    Simulates the the enviorment of foosball as for the keeper. 
    This simulation has the intention to train an AI to play the game.

    Use the W,A,S,D keys to move the keeper.
    Press C to start the simulation.

    File:
        keeper_sim.py
    Date:
        16.12.2019
    Version:
        1.46
    Modifier:
        Daniël Boon
        Kelvin Sweere
    Used_IDE:
        Visual Studio Code (Python 3.6.7 64-bit)
    Version Management:
        1.41:
            Headers veranderd. 
        1.42:
            Functies met underscore gemaakt ipv C++ lowerCamelCase style.
        1.43:
            Jit van Numba verwijdert
            Verhoudingen van simulatieveld aangepast
        1.44:
            Google docstring format toegepast op functies.
            Functies met underscore gemaakt ipv C++ lowerCamelCase style.
        1.45:
            print_ai_stats functie gemaakt.
            ball_reset niet wanneer er niet is gescoord, de beeldherkenning is leidend.
        1.46:
            fixed te vaak blocked
""" 
'''
Used libraries/repositories:
        - PyBox2D (PyBox2D - Jan 15, 2018):
            https://github.com/pybox2d/pybox2d
        - Numba 0.35.0 (Numba - Sept 17, 2019)
            https://github.com/numba/numba
        - pygame 1.9.6 (pygame - Apr 25, 2019):
            https://github.com/pygame/pygame
'''
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# C++ version Copyright (c) 2006-2007 Erin Catto http://www.box2d.org
# Python version by Ken Lauer / sirkne at gmail dot com


#pylint: disable=E1101
from .Backend.Framework import (Framework, Keys, main)
#import deep_q_learning

from random import random
from math import (cos,sin,pi)
from time import time
from Box2D.Box2D import (b2CircleShape, b2EdgeShape, b2FixtureDef)
from datetime import datetime
import tkinter as tk 
from tkinter.filedialog import askopenfilename
tk.Tk().withdraw()

class Control:
    """houd bij welke richting is gekozen voor de keeper om naar toe te gaan
    """
    x = 0.0
    y = 0.0


class KeeperSim(Framework):
    """maakt de simulatie objecten aan, regelt de keeper begingen, bal schieten en of er wel of niet gescoord is.
    
    Args:
        Framework (FrameworkBase): The base of the main testbed framework.
    """
    name = "KeeperSim"
    description = "Press c to start the game"

    def __init__(self,up_speed=100, down_speed=-100, shoot_bool=True):
        """Init van de keep_sim class.
        
        Args:
            up_speed (int, optional): Snelheid van de keeper lateraal. Defaults to 100.
            down_speed (int, optional): Negatieve snelheid van de keeper lateraal. Defaults to -100.
            shoot_bool (bool, optional): keuze of beeldherkenning wordt gebruikt voor de simulatie. Standaard uit (False).
        """
        
        super(KeeperSim, self).__init__()

        # Veld opstellen 
        ground = self.world.CreateStaticBody(
            shapes=[b2EdgeShape(vertices=[(-19.35, 0), (19.35, 0)]), # bovenste lijn
                    b2EdgeShape(vertices=[(-19.35, 0), (-19.35, 6.67)]), #Linker lijn bovenkant
                    b2EdgeShape(vertices=[(-19.35, 20.0), (-19.35, 13.33)]),  #Linker lijn onderkant
                    b2EdgeShape(vertices=[(19.35, 0), (19.35, 6.67)]),  #Rechter lijn bovenkant
                    b2EdgeShape(vertices=[(19.35, 20.0), (19.35, 13.33)]), #Rechter lijn onderkant
                    b2EdgeShape(vertices=[(-19.35, 20.0), (19.35, 20.0)]), #onderste lijn
                    ])
        self.KEEPER_SPEED = 40
        self.FORCE_MAX = 100
        self.FORCE_MIN = 60
        # bal straal instellen
        self.radius = radius = 0.5
        
        # keeper maken
        self.create_keeper((-16.72,10.0))
        self.scaler = 15/19.35
        self.target = 0 #eindpunt voor het schot van de bal.
        
        # zet zwaarte kracht 0 voor top-down
        self.world.gravity = (0, 0)
        # Keep track of the pressed keys
        self.pressed_keys = set()
        
        self.time = pi/self.KEEPER_SPEED
        self.time_change = 0
        self.goals = 0
        self.blocks = 0
        self.control = Control()
        self.action = [0,0,0,0,0]
        self.ratio = 0
        self.tp = None

        #TODO: debug waarde!
        shoot_bool = True   #boolean die bepaald of er wordt geschoten (False is schieten!)
        # ! ---------------

        self.shoot_bool = not(shoot_bool)  #flag die checkt of beeldherkenning aanstaat.
        self.force_param = shoot_bool   #schieten als beeldherkenning uitstaat!
        
        # check of cordinaten van de beeldherkenning moeten worden gebruikt, anders midden.
        b_x, b_y = (0.0, 8.71) if shoot_bool else (0.0 , random() * 20.0)   
        
        self.set_ball((b_x, b_y))  #creeeër de bal.

    def set_Foostronics(self, Foostronics):
        """Foostronics class initaliseren in de KeeperSim class.
        
        Args:
            Foostronics (class): Class van de main applicatie.
        """ 
        self.fs = Foostronics(self)

    def Keyboard(self, key, settings):
        """wanneer een key wordt ingedrukt, kom in deze functie

        Keys:
            c = spawn ball
            w = keeper naar boven
            s = keeper naar beneden
            a = keeper naar links
            d = keeper naar rechts
            j = versnell keeper simullatie (is instabiel)
            m = save ai
            r = restore ai file
        
        Args:
            key (int): nummer input key die word ingedrukt.
            settings (class): class met parameter intellingen.
        """
        if key == Keys.K_c:
            # self.SetBall((0.0 , random() * 20.0), force_param=False)
            self._reset_ball()
        if key == Keys.K_w:
            self.control.y = self.KEEPER_SPEED
        if key == Keys.K_s:
            self.control.y = -self.KEEPER_SPEED
        if key == Keys.K_a:
            self.control.x = -self.KEEPER_SPEED
        if key == Keys.K_d:
            self.control.x = self.KEEPER_SPEED
        if key == Keys.K_j:
            if self.settings.c_hz == 60:
                #settings.hz = 2
                self.settings.timeStep = 1.0 / 25
                self.settings.c_hz = 140
                settings.positionIterations = 90
                settings.velocityIterations = 240
            else:
                self.settings.timeStep = 1.0 / 60
                self.settings.c_hz = 60
                settings.positionIterations = 24
                settings.velocityIterations = 64
        if key == Keys.K_m:
            date_time = datetime.now().strftime("%m-%d-%Y, %H-%M-%S")
            #save_path = self.saver.save(self.sess, "/AI_models/AI_save %s.ckpt" % (date_time))
            save_path = self.saver.save(self.sess, "AI_models/AI_save_%s.ckpt" % (date_time))
            print("AI model saved")
        if key == Keys.K_r:
            filename = askopenfilename().split('.')
            filename = (filename[0]+'.'+filename[1])
            # filename = (filename.split('.')[0],'.',filename.split('.')[1])
            print(filename)
            if filename:
                self.saver.restore(self.sess, filename)
        
    def Keyboard_up(self, key):
        """wanneer een key wordt losgelaten, kom in deze functie.
        
        Args:
            key (int): nummer input key die werd losgelaten.
        """
        vel = self.body.linearVelocity
        if (key == Keys.K_w or key == Keys.K_s):
            self.control.y = 0.0
            self.body.linearVelocity.y = 0
        if (key == Keys.K_a or key == Keys.K_d):
            self.control.x = 0.0
            self.body.linearVelocity.x = 0
        #else:
        #    pass 
        
        self.body.linearVelocity = vel

    def create_keeper(self, pos):
        """maak keeper object in veld.
        
        Args:
            pos ((int, int)): x & y coördinaten waar keeper moet komen te staan.
        """
        dimensions=(0.12, 0.55)
        self.body = self.world.CreateDynamicBody(position=pos, linearDamping = 0.5)
        self.body.allowSleep = False
        self.body.awake = True
        self.body.fixedRotation = True
        self.fixture = self.body.CreatePolygonFixture(box=dimensions, density=100000000)
        self.fixture.sensor = False
    
    def create_targetpoint(self, pos):
        """Creeër een punt in de simulatie die weergegeven moet worden.
        
        Args:
            pos (tuple): x & y cordinaten waar het targetpoint moet komen te staan.
        """
        
        fixture = b2FixtureDef(shape=b2CircleShape(radius=0.3,  #create ball.
                                                   pos=(0, 0)),
                               density=1, friction=900000, restitution=0.5)
        fixture.sensor = True
        # balpositie, vanaf nu ball.
        self.tp = self.world.CreateDynamicBody(
            position=pos,
            fixtures=fixture,
            linearDamping = 0.5
        )

    def delete_targetpoint(self):
        if(self.tp):
            self.world.DestroyBody(self.tp)
            self.tp = None

    def _create_ball(self, pos):
        """Creeëren van een bal in Box2D omgeving.
        
        Args:
            pos (tuple): x,y cordinaten van de bal.
        """
        fixture = b2FixtureDef(shape=b2CircleShape(radius=self.radius,  #create ball.
                                                   pos=(0, 0)),
                               density=1, friction=900000, restitution=0.5)
        # balpositie, vanaf nu ball.
        self.ball = self.world.CreateDynamicBody(
            position=pos,
            fixtures=fixture,
            linearDamping = 0.5
        )

    def _calculate_force_ball(self, pos):
        """Bereken de kracht die op de bal moet komen te staan.
        
        Args:
            pos (tuple): x,y cordinaten van de bal.
        
        Returns:
            int: kracht van de bal naar de keeper.
        """
        goal_lenght = 4.5   #constant
        goal = goal_lenght * random()
        goal += (10.0 - (goal_lenght/2))

        power = (self.FORCE_MAX-self.FORCE_MIN) * random() + self.FORCE_MIN
        force = ((-19.35-pos[0])*power,(pos[1]-goal)*-power)

        self.target = ((goal-pos[1])*self.scaler)+pos[1]

        return force


    #zet bal met random kracht op doel gericht in het veld
    def set_ball(self, pos):
        """Maak een bal aan. Hierbij is self.ball.x & self.ball.y de cordinaten van de bal.
        
        Args:
            pos (tuple):                    Positie van de bal.
            force_param (bool, optional):   Debug param die bepaald of er een kracht op de bal moet worden gezet.
        """
        #crieëer de bal
        self._create_ball(pos)

        #als er een kracht op moet worden gezet, doe dat dan.
        if self.force_param:
            force = self._calculate_force_ball(pos)
            self.ball.ApplyForce(force, (-19.35,10.0), True)

        self.time_change = round(time()) + 1


    def _reset_ball(self):
        """Functie die de bal reset aan de hand van of er beeldherkenning wordt gebruikt.
        """
        if self.shoot_bool: #shoot_bool is waar, dus schieten.
            # Reset bal op punt 0,0 als er nog geen bal wordt gedetecteerd.
            pass
        else:
            self.set_ball((0.0 , random() * 20.0))    
    

    #kom bij iedere frame in deze functie (bepaling keeper positie/snelheid
    def Step(self, settings):
        """Functie die elke frame wordt aangeroepen en hierbij de bepaling van de keeper positie/snelheid regelt.
        
        Args:
            settings (Class): De instellingen die vooraf zijn gedefinieerd. 
        """
        vel = self.body.linearVelocity  #velocity van de keeper
        Framework.Step(self, settings)  #
        
        #bepaling snelheid keeper bij verticale beweging
        if ((self.control.y < 0) and (self.body.position.y > 7.08 )):
            vel.y = self.control.y
        elif ((self.control.y > 0) and (self.body.position.y < 12.92)):
            vel.y = self.control.y
        else:
            vel.y = 0

        #bepaling snelheid keeper bij horizontale beweging (+maak doorlaatbaar wanneer de keeper te hoog staat)
        if self.control.x and (settings.hz > 0.0):
            blub = 2   
            if (self.control.x > 0) and ((self.KEEPER_SPEED * self.time/blub) < pi): #A
                #print("A")
                self.time += 1.0 / settings.hz
                vel.x = (self.KEEPER_SPEED * sin(self.KEEPER_SPEED * self.time/blub))
                if (self.KEEPER_SPEED * self.time/blub) > 2.7925268032:
                    self.fixture.sensor = False #True
                else:
                    self.fixture.sensor = False
            elif (self.control.x < 0) and ((self.KEEPER_SPEED * (self.time/blub)) > 0): #D
                #print("D")
                self.time -= 1.0 / settings.hz
                vel.x = (-self.KEEPER_SPEED * sin(self.KEEPER_SPEED * (self.time/blub)))
                if (self.KEEPER_SPEED * self.time) < 0.3490658504:
                    self.fixture.sensor = False #True
                else:
                    self.fixture.sensor = False
            else:
                vel.x = 0
        
            
        self.body.linearVelocity = vel
        if(self.shoot_bool):
            try:
                # is er een goal gemaakt? goal++ en setball
                if(self.ball.position.x < -19.35):
                    self.goals += 1
                    self.ball.position.x = 0
                    # ? dit is hetzelfde als de try elif -> dus functie!
                    self.world.DestroyBody(self.ball)
                    #self.world.DestroyBody(self.ball_target)
                    self._reset_ball()   #reset de bal op het veld.
                    self.body.position = (-16.72,10.0)
                    self.time = pi/self.KEEPER_SPEED
                    self.fixture.sensor = False

                # is de bal geblocked? blocked++ en setball
                elif abs(self.ball.linearVelocity.x) < 1 or abs(self.ball.linearVelocity.y) < 1 or (self.ball.linearVelocity.x > 0): #and (round(time()) > self.time_change)):
                    if not self.shoot_bool:
                        self.blocks += 1
                        self.ball.linearVelocity.x = -1
                        self.ball.linearVelocity.y = -0.5
                        # ?  dit is hetzelfde als de try if -> dus functie!
                        self.world.DestroyBody(self.ball)
                        #self.world.DestroyBody(self.ball_target)
                        self._reset_ball()   #reset de bal op het veld.
                        self.body.position = (-16.72,10.0)
                        self.time = pi/self.KEEPER_SPEED
                        self.fixture.sensor = False
            except:
                pass

        # print(self.fixture.sensor)
        if(self.fixture.sensor and ((self.body.position.x < -14) and self.body.position.x > -16)):
            self.fixture.sensor = False

        self.print_ai_stats()

    def print_ai_stats(self):
        """Print alle statistieken van de performance van de AI.
        """
        # Print namen van de variabelen.
        self.Print('goals = %d' % self.goals)
        self.Print('blocked = %d' % self.blocks)
        self.Print('rounds = %d' % (self.goals+self.blocks))
        self.Print('ratio last 100 blocked/goals = %d' % (self.ratio))
        if self.goals:
            self.Print('ratio total blocked/goals = %d' %
                       ((self.blocks*100)/(self.goals+self.blocks)))
        else:
            self.Print('ratio blocked/goals = 100')
        self.Print(('|  |%d|  |' % (self.action[0])))
        self.Print(('|%d|%d|%d|' % (0, self.action[3], self.action[2])))
        self.Print(('|  |%d|  |' % (self.action[1])))


if __name__ == "__main__":
    main(KeeperSim)
