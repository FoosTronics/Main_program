'''
 * File     : KeeperSim.py (keeper_sim.py)
 * Datum    : 14-1-2019
 * Version  : 1.2
 * Modifier : Daniël Boon
 * Used IDE : Visual Studio Code (Python 3.6.7)
 * Function : Simulates the environment of foosball as for the keeper. 
			  This simulation has the intention to train an AI to play the game.
              
			  Use the W,A,S,D keys to move the keeper.
			  Press C to start the simulation.
* Versie controle:
    Verhoudingen van het veld aangepast
    Balradius gewijzigd
    Alle dimensies van de keeper gewijzigd
    Naam veranderd van keeper_sim.py to KeeperSim.py                  
    Snelheid keeper horizontale beweging veranderd
Used libraries/repositories:
    - PyBox2D (PyBox2D - Jan 15, 2018):
        https://github.com/pybox2d/pybox2d
    - Numba 0.35.0 (Numba - Sept 17, 2019)
        https://github.com/numba/numba
'''
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# C++ version Copyright (c) 2006-2007 Erin Catto http://www.box2d.org
# Python version by Ken Lauer / sirkne at gmail dot com


#pylint: disable=E1101

from random import random
from math import (cos,sin,pi)
from time import time
from numba import jit
from Backend.Framework import (Framework, Keys, main)
from Box2D.Box2D import (b2CircleShape, b2EdgeShape, b2FixtureDef)

KEEPER_SPEED = 30
FORCE_MAX = 200
FORCE_MIN = 40

#houd bij welke richting is gekozen voor de keeper om naar toe te gaan
class control:
    x = 0.0
    y = 0.0

class keeper_sim (Framework):
    name = "Keeper_sim"
    description = "Press c to start the game"

    def __init__(self,up_speed=100,down_speed=-100):
        super(keeper_sim, self).__init__()

        # Veld opstellen 
        ground = self.world.CreateStaticBody(
            shapes=[b2EdgeShape(vertices=[(-19.35, 0), (19.35, 0)]), # bovenste lijn
                    b2EdgeShape(vertices=[(-19.35, 0), (-19.35, 6.67)]), #Linker lijn bovenkant
                    b2EdgeShape(vertices=[(-19.35, 20.0), (-19.35, 13.33)]),  #Linker lijn onderkant
                    b2EdgeShape(vertices=[(19.35, 0), (19.35, 6.67)]),  #Rechter lijn bovenkant
                    b2EdgeShape(vertices=[(19.35, 20.0), (19.35, 13.33)]), #Rechter lijn onderkant
                    b2EdgeShape(vertices=[(-19.35, 20.0), (19.35, 20.0)]), #onderste lijn
                    ])

        # ball straal instellen
        self.radius = radius = 0.8
        
        # keeper maken
        self.CreateKeeper((-16.72,10.0))
        
        # zet zwaarte kracht 0 voor top-down
        self.world.gravity = (0, 0)

        # Keep track of the pressed keys
        self.pressed_keys = set()
        
        self.time = pi/KEEPER_SPEED
        self.time_change = 0
        self.goals = 0
        self.blocks = 0
    
    #wanneer een key wordt ingedrukt, kom in deze functie
    @jit(nopython=False)
    def Keyboard(self, key):
        if key == Keys.K_c:
            self.SetBall((0.0 , random() * 20.0))
        if key == Keys.K_w:
            control.y = KEEPER_SPEED
        if key == Keys.K_s:
            control.y = -KEEPER_SPEED
        if key == Keys.K_a:
            control.x = -KEEPER_SPEED
        if key == Keys.K_d:
            control.x = KEEPER_SPEED
        #else:
        #    print("nutteloze knop heb je nou ingedrukt")
        
    #wanneer een key wordt losgelaten, kom in deze functie
    @jit(nopython=False)
    def KeyboardUp(self, key):
        vel = self.body.linearVelocity
        if (key == Keys.K_w or key == Keys.K_s):
            control.y = 0.0
            self.body.linearVelocity.y = 0
        if (key == Keys.K_a or key == Keys.K_d):
            control.x = 0.0
            self.body.linearVelocity.x = 0
        #else:
        #    pass 
        
        self.body.linearVelocity = vel

    #maak keeper object in veld
    @jit(nopython=False)
    def CreateKeeper(self, pos):
        dimensions=(0.14, 0.5)
        self.body = self.world.CreateDynamicBody(position=pos, linearDamping = 0.5)
        self.body.allowSleep = False
        self.body.awake = True
        self.body.fixedRotation = True
        self.fixture = self.body.CreatePolygonFixture(box=dimensions, density=100000000)
        self.fixture.sensor = False
        
    #zet bal met random kracht op doel gericht in het veld
    @jit(nopython=False)
    def SetBall(self, pos):
        goal_lenght = 4.5
        goal = goal_lenght * random()
        goal += (10.0 - (goal_lenght/2))
        spawn = 0, (random() * 30 + 30)
        fixture = b2FixtureDef(shape=b2CircleShape(radius=self.radius,
                                                   pos=(0, 0)),
                               density=1, friction=900000, restitution=0.5)

        self.ball = self.world.CreateDynamicBody(
            position=pos,
            fixtures=fixture,
            linearDamping = 0.5
        )
        power = (FORCE_MAX-FORCE_MIN) * random() + FORCE_MIN
        force = ((-19.35-pos[0])*power,(pos[1]-goal)*-power)
        self.ball.ApplyForce(force, (-19.35,10.0), True)
        self.time_change = round(time()) + 1

    #kom bij iedere frame in deze functie (bepaling keeper positie/snelheid
    def Step(self, settings):
        vel = self.body.linearVelocity
        Framework.Step(self, settings)
        
        #bepaling snelheid keeper bij verticale beweging
        if (control.y < 0) and (self.body.position.y > 7.08 ):
            vel.y = control.y
        elif (control.y > 0) and (self.body.position.y < 12.92):
            vel.y = control.y
        else:
            vel.y = 0
        
        #bepaling snelheid keeper bij horizontale beweging (+maak doorlaatbaar wanneer de keeper te hoog staat)
        if control.x and (settings.hz > 0.0): #0.0
            blub = 2
            if (control.x > 0) and ((KEEPER_SPEED * self.time/blub) < pi): #A
                #print("A")
                self.time += 1.0 / settings.hz
                vel.x = (KEEPER_SPEED * sin(KEEPER_SPEED * self.time/blub))
                if (KEEPER_SPEED * self.time/blub) > 3:#2.7925268032:
                    self.fixture.sensor = True
                else:
                    self.fixture.sensor = False
            elif (control.x < 0) and ((KEEPER_SPEED * (self.time/blub)) > 0): #D
                #print("D")
                self.time -= 1.0 / settings.hz
                vel.x = (-KEEPER_SPEED * sin(KEEPER_SPEED * (self.time/blub)))
                if (KEEPER_SPEED * self.time/blub) < 0.2: #0.3490658504:
                    self.fixture.sensor = True
                else:
                    self.fixture.sensor = False
            else:
                vel.x = 0
        
            
            self.body.linearVelocity = vel
        try:
            # is er een goal gemaakt? goal++ en setball
            if(self.ball.position.x < -19.35):
                self.goals += 1
                self.ball.position.x = 0
                self.world.DestroyBody(self.ball)
                self.SetBall((0.0 , random() * 20))
                self.body.position = (-16.72,10.0)
                self.time = pi/KEEPER_SPEED
                self.fixture.sensor = False
            # is de bal geblocked? blocked++ en setball
            elif((abs(self.ball.linearVelocity.x) < 1 or abs(self.ball.linearVelocity.y) < 1 or (self.ball.linearVelocity.x > 0)) and (round(time()) > self.time_change)):
                self.blocks += 1
                self.ball.linearVelocity.x = -1
                self.ball.linearVelocity.y = -0.5
                self.world.DestroyBody(self.ball)
                self.SetBall((0.0 , random() * 20.0))
                self.body.position = (-16.72,10.0)
                self.time = pi/KEEPER_SPEED
                self.fixture.sensor = False
        except:
            pass
        
        self.Print('goals = %d' % self.goals)
        self.Print('blocked = %d' % self.blocks)

if __name__ == "__main__":
    print("start")
    main(keeper_sim)
