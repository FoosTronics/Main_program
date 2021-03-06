"""
    Simuleert de omgeving van de tafelvoetbaltafel met de keeper.
    Deze simulatie is bedoeld om een AI te trainen zodat deze het spel kan spelen

    Gebruik de W,A,S,D toetsen om de keeper te bewegen.
    Druk op C om de simulatie te starten.
    
    File:
        KeeperSim.py
    Date:
        22-1-2020
    Version:
        1.53
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
            Doxygen commentaar toegevoegd. 
            fixed te vaak blocked
        1.47:
            Spelling en grammatica commentaren nagekeken.
        1.48:
            KEEPER_SPEED gevalideerd.
        1.5:
            Initialisatie Foostronics klasse niet in set_Foostronics, maar in main.py. In set_Foostronics wordt nu foosTronics object meegegeven.
        1.51:
            Fixed geen ai save bestanden kunnen laden of opslaan
        1.52:
            Globale variabelen gemaakt voor TOP, BOTTOM, LEFT & RIGHT.
        1.53:
            Doxygen cometaar gecontroleerd + overtollig commetaar verwijdert 
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

from random import random
from math import (cos,sin,pi)
from time import time
from Box2D.Box2D import (b2CircleShape, b2EdgeShape, b2FixtureDef)
from datetime import datetime
import tkinter as tk 
from tkinter.filedialog import askopenfilename
tk.Tk().withdraw()

class Control:
    """Houdt bij welke richting is gekozen voor de keeper om naar toe te gaan.
    """
    x = 0.0
    y = 0.0


class KeeperSim(Framework):
    """Maakt de simulatie objecten aan, regelt de keeper bewegingen, bal schieten en of er wel of niet gescoord is.
    
    Args:
        Framework: (FrameworkBase) De basis van het hoofd van het spel Framework.
    
    **Author**:         \n
        Daniël Boon     \n
        Kelvin Sweere   \n
    **Version**:
        1.53            \n
    **Date**:           
        22-1-2020       
    """
    name = "KeeperSim"
    description = "Druk op C om het spel te starten."

    def __init__(self,up_speed=100, down_speed=-100, shoot_bool=True):
        """Initialisatie van de KeeperSim klasse.
        
        Args:
            up_speed: (int, optional) snelheid van de keeper lateraal. Standaard 100.
            down_speed: (int, optional) negatieve snelheid van de keeper lateraal. Standaard -100.
            shoot_bool: (bool, optional) keuze of beeldherkenning wordt gebruikt voor de simulatie. Standaard True.
        """
        
        super(KeeperSim, self).__init__()

        # Afmetingen veld in verhouding ten opzichte van het echte veld.
        self.SIM_LEFT = -19.35 # Links tot rechts is 1045mm.
        self.SIM_RIGHT = 19.35
        self.SIM_TOP = 0.0 # Boven tot onder is 540mm.
        self.SIM_BOTTOM = 20.0
        # 21mm tot 100mm vanuit de doellijn
        # 71mm keeper vanuit de doellijn.

        # Veld opstellen 
        ground = self.world.CreateStaticBody(
            shapes=[b2EdgeShape(vertices=[(self.SIM_LEFT, self.SIM_TOP), (self.SIM_RIGHT, self.SIM_TOP)]), # Bovenste lijn
                    b2EdgeShape(vertices=[(self.SIM_LEFT, self.SIM_TOP), (self.SIM_LEFT, (self.SIM_BOTTOM/3))]), # Linker lijn bovenkant
                    b2EdgeShape(vertices=[(self.SIM_LEFT, self.SIM_BOTTOM), (self.SIM_LEFT, (self.SIM_BOTTOM*2/3))]),  # Linker lijn onderkant
                    b2EdgeShape(vertices=[(self.SIM_RIGHT, self.SIM_TOP), (self.SIM_RIGHT, (self.SIM_BOTTOM/3))]),  # Rechter lijn bovenkant
                    b2EdgeShape(vertices=[(self.SIM_RIGHT, self.SIM_BOTTOM), (self.SIM_RIGHT, (self.SIM_BOTTOM*2/3))]), # Rechter lijn onderkant
                    b2EdgeShape(vertices=[(self.SIM_LEFT, self.SIM_BOTTOM), (self.SIM_RIGHT, self.SIM_BOTTOM)]), # Onderste lijn
                    ])
        
        # ! KEEPER_SPEED = 35 gevalideerd met Chileam en Kelvin
        self.KEEPER_SPEED = 35  
        self.FORCE_MAX = 100
        self.FORCE_MIN = 40
        
        # Bal straal instellen
        self.radius = radius = 0.5

        self.MIDDELPUNT_KEEPER = -16.72     # x coördinaat waarin de keeper begint.

        # Keeper maken
        self.create_keeper((self.MIDDELPUNT_KEEPER, 10.0))
        self.scaler = 15/self.SIM_RIGHT
        self.target = 0 #Eindpunt voor het schot van de bal.
        
        # Zet zwaarte kracht 0 voor top-down
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
        shoot_bool = True   # Boolean die bepaald of er wordt geschoten (False is schieten!).
        # ! ---------------

        self.shoot_bool = not(shoot_bool)  # Flag die checkt of beeldherkenning aanstaat.
        self.force_param = not(shoot_bool)   # Schieten als beeldherkenning uitstaat!
        
        # Check of de coördinaten van de beeldherkenning moeten worden gebruikt, anders midden.
        b_x, b_y = (0.0, self.SIM_BOTTOM/2) if shoot_bool else (0.0, random() * self.SIM_BOTTOM)
        
        self.set_ball((b_x, b_y))  # Creëer de bal.

    def set_Foostronics(self, foostronics):
        """Foostronics klasse initialiseren in de KeeperSim klasse.
        
        Args:
            Foostronics: (class) klasse van de main applicatie.
        """ 
        self.fs = foostronics

    def Keyboard(self, key, settings):
        """Wanneer een toets wordt ingedrukt, ga in deze functie.

        Toetsen:
            | Toets | Opmerking                                     |
            |:------|-----------------------------------------------|
            | c     | Bal oproepen                                  |
            | w     | Keeper naar boven                             |
            | s     | Keeper naar beneden                           |
            | a     | Keeper naar links                             |
            | d     | Keeper naar rechts                            |
            | j     | Versnel de keeper simulatie (is instabiel)    |
            | m     | Sla de gecreerde data van de ai op            |
            | r     | Herstel een opgeslagen ai bestand             |

        Args:
            key: (int) nummer input toets die word ingedrukt.
            settings: (class) klasse met parameter instellingen.
        """
        if key == Keys.K_c:
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
            save_path = self.fs.dql.saver.save(self.fs.dql.sess, "AI_models/AI_save_%s.ckpt" % (date_time))
            print("AI model opgeslagen")
        if key == Keys.K_r:
            filename = askopenfilename().split('.')
            try:
                filename = (filename[0]+'.'+filename[1])
                if filename:
                    self.fs.dql.saver.restore(self.fs.dql.sess, filename)
                    print("AI geladen van bestand: " + filename)
            except:
                print("geen bestand gevonden")
        
    def Keyboard_up(self, key):
        """Wanneer een toets wordt losgelaten, ga naar deze functie.
        
        Args:
            key: (int) nummer input toets die werd losgelaten.
        """
        vel = self.body.linearVelocity
        if (key == Keys.K_w or key == Keys.K_s):
            self.control.y = 0.0
            self.body.linearVelocity.y = 0
        if (key == Keys.K_a or key == Keys.K_d):
            self.control.x = 0.0
            self.body.linearVelocity.x = 0
        
        self.body.linearVelocity = vel

    def create_keeper(self, pos):
        """Maak keeper object in het veld.
        
        Args:
            pos: (tuple) x & y coördinaten waar de keeper moet komen te staan.
        """
        dimensions=(0.12, 0.55)
        self.body = self.world.CreateDynamicBody(position=pos, linearDamping = 0.5)
        self.body.allowSleep = False
        self.body.awake = True
        self.body.fixedRotation = True
        self.fixture = self.body.CreatePolygonFixture(box=dimensions, density=100000000)
        self.fixture.sensor = False
    
    def create_targetpoint(self, pos):
        """Creëer targetpoint (gewenste positie keeper) in de simulatie die weergegeven moet worden.
        
        Args:
            pos: (tuple) x & y coördinaten waar het targetpoint moet komen te staan.
        """
        
        self.fixture_tp = b2FixtureDef(shape=b2CircleShape(radius=0.3,  #create targetpoint.
                                                   pos=(0, 0)),
                               density=1, friction=900000, restitution=0.5)
        self.fixture_tp.sensor = True
        self.tp = self.world.CreateDynamicBody(
            position=pos,
            fixtures=self.fixture_tp,
            linearDamping = 0.5
        )
        self.fixture_tp2 = self.tp.CreatePolygonFixture(shape=b2CircleShape(radius=0.3), density=100000000)
        self.fixture_tp2.sensor = True

    def delete_targetpoint(self):
        """Delete targetpoint als die er is.
        """
        if(self.tp):
            self.world.DestroyBody(self.tp)
            self.tp = None

    def _create_ball(self, pos):
        """Creëren van een bal in Box2D omgeving.
        
        Args:
            pos: (tuple) x,y coördinaten van de bal.
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
        """Bereken de kracht die op de bal moet worden uitgeoefend.
        
        Args:
            pos: (tuple) x,y coördinaten van de bal.
        
        Returns:
            (int) kracht van de bal naar de keeper.
        """
        goal_length = 4.5   #constant
        goal = goal_length * random()
        goal += (10.0 - (goal_length/2))

        power = (self.FORCE_MAX-self.FORCE_MIN) * random() + self.FORCE_MIN
        force = ((self.SIM_LEFT-pos[0])*power,(pos[1]-goal)*-power)

        self.target = ((goal-pos[1])*self.scaler)+pos[1]

        return force


    #zet bal met random kracht op doel gericht in het veld
    def set_ball(self, pos):
        """Maak een bal aan. Hierbij zijn self.ball.x & self.ball.y de coördinaten van de bal.
        
        Args:
            pos: (tuple) positie van de bal.
            force_param: (bool, optional) debug parameter die bepaald of er een kracht op de bal moet worden uitgeoefend.
        """
        #crieëer de bal
        self._create_ball(pos)

        #als er een kracht op moet worden gezet, doe dat dan.
        if self.force_param:
            force = self._calculate_force_ball(pos)
            self.ball.ApplyForce(force, (self.SIM_LEFT,self.SIM_BOTTOM/2), True)

        self.time_change = round(time()) + 1


    def _reset_ball(self):
        """Functie die de bal reset aan de hand van of er beeldherkenning wordt gebruikt.
        """
        if self.shoot_bool: #shoot_bool is waar, dus schieten.
            self.set_ball((0.0 , random() * self.SIM_BOTTOM))   
            # Reset bal op punt 0,0 als er nog geen bal wordt gedetecteerd.
 
    

    #kom bij iedere frame in deze functie (bepaling keeper positie/snelheid
    def Step(self, settings):
        """Functie die bij elke frame wordt aangeroepen en hierbij de bepaling van de keeper positie/snelheid regelt.
        
        Args:
            settings: (Class) de instellingen die vooraf zijn gedefinieerd. 
        """
        vel = self.body.linearVelocity  #velocity van de keeper
        Framework.Step(self, settings)  
        
        #bepaling snelheid keeper bij laterale beweging
        if ((self.control.y < 0) and (self.body.position.y > 7.08 )):
            vel.y = self.control.y
        elif ((self.control.y > 0) and (self.body.position.y < 12.92)):
            vel.y = self.control.y
        else:
            vel.y = 0

        #bepaling snelheid keeper bij axiale beweging (+maak doorlaatbaar wanneer de keeper te hoog staat)
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

        if(self.fixture.sensor and ((self.body.position.x < -14) and self.body.position.x > -16)):
            self.fixture.sensor = False

        self.print_ai_stats()

    def print_ai_stats(self):
        """Print alle statistieken van de performance van de AI in Pygame.
        """
        # Print namen van de variabelen.
        self.Print('Doelpunten = %d' % self.goals)
        self.Print('Geblokt = %d' % self.blocks)
        self.Print('Rondes = %d' % (self.goals+self.blocks))
        self.Print('Ratio laatste 100 geblokt/doelpunten = %d' % (self.ratio))
        if self.goals:
            self.Print('Ratio totaal geblokt/doelpunten = %d' %
                       ((self.blocks*100)/(self.goals+self.blocks)))
        else:
            self.Print('Ratio geblokt/doelpunten = 100')
        self.Print(('|  |%d|  |' % (self.action[0])))
        self.Print(('|%d|%d|%d|' % (0, self.action[3], self.action[2])))
        self.Print(('|  |%d|  |' % (self.action[1])))


if __name__ == "__main__":
    main(KeeperSim)
