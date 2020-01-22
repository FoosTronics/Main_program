"""
    Dit bestand betreft de functionaliteit van de AI

    Simuleert de omgeving van de tafelvoetbaltafel met de keeper.
    Deze simulatie is bedoeld om een AI te trainen zodat deze het spel kan spelen

    Gebruik de W,A,S,D toetsen om de keeper te bewegen.
    Druk op C om de simulatie te starten.

    File:
        PygameFramework.py
    Date:
        16-1-2020
    Version:
        V1.0
    Modifier:
        Daniël Boon    
    Used_IDE:
        Visual Studio Code (Python 3.6.7 64-bit)
    Used libraries/repositories:
        - PyBox2D (PyBox2D - Jan 15, 2018):
            https://github.com/pybox2d/pybox2d
        - Numba 0.35.0 (Numba - Sept 17, 2019)
            https://github.com/numba/numba
        - pygame 1.9.6 (pygame - Apr 25, 2019):
            https://github.com/pygame/pygame
    Global Keys:
        F1     - toggle menu (can greatly improve fps)
        Space  - shoot projectile
        Z/X    - zoom
        Escape - quit
    Other keys can be set by the individual test.
    Mouse:
        Left click  - select/drag body (creates mouse joint)
        Right click - pan
        Shift+Left  - drag to create a directed projectile
        Scroll      - zoom
    Version management:
        1.0:
            Verwijzingen naar bestandsnamen gewijzigd
            Header aangepast
        1.01:
            Doxygen commentaar toegevoegd.
"""
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# C++ version Copyright (c) 2006-2007 Erin Catto http://www.box2d.org
# Python version Copyright (c) 2010 kne / sirkne at gmail dot com
#
# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the authors be held liable for any damages
# arising from the use of this software.
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
# 1. The origin of this software must not be misrepresented; you must not
# claim that you wrote the original software. If you use this software
# in a product, an acknowledgment in the product documentation would be
# appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
# misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.


from __future__ import (print_function, absolute_import, division)
import sys
import warnings
#from main import Foostronics

try:
    import pygame_sdl2
except ImportError:
    if sys.platform in ('darwin', ):
        warnings.warn('OSX has major issues with pygame/SDL 1.2 when used '
                      'inside a virtualenv. If this affects you, try '
                      'installing the updated pygame_sdl2 library.')
else:
    # pygame_sdl2 is backward-compatible with pygame:
    pygame_sdl2.import_as_pygame()

import pygame
from pygame.locals import (QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN,
                           MOUSEBUTTONUP, MOUSEMOTION, KMOD_LSHIFT)

from .Framework import FrameworkBase, Keys
#from .Framework import (FrameworkBase, Keys)
from .Settings import fwSettings
from Box2D import (b2DrawExtended, b2Vec2)

GUIEnabled = False

class PygameDraw(b2DrawExtended):
    """Deze class wordt aangeroepen door Box2D en handelt de rendering. 

    **Athor**:
        Box2D         \n
    **Version**:
        1.01          \n
    **Date**:
        22-1-2020 
    """
    surface = None
    axisScale = 10.0

    def __init__(self, test=None, **kwargs):
        b2DrawExtended.__init__(self, **kwargs)
        self.flipX = False
        self.flipY = True
        self.convertVertices = True
        self.test = test

    def StartDraw(self):
        """Begin met tekenen.
        """
        self.zoom = self.test.viewZoom
        self.center = self.test.viewCenter
        self.offset = self.test.viewOffset
        self.screenSize = self.test.screenSize

    def EndDraw(self):
        """Stop met tekenen.
        """
        pass

    def DrawPoint(self, p, size, color):
        """Tekent een enkele punt die wordt aangeroepen.
        
        Args:
            p: (tuple) pixel punt in x & y coördinaten.
            size: (int) groote van het te tekenen pixel.
            color: (tuple) kleur van de te tekenen pixel in RGB.
        """
        self.DrawCircle(p, size / self.zoom, color, drawwidth=0)

    def DrawAABB(self, aabb, color):
        """Tekent een lijn rond het punt AABB met een gegeven kleur.
        
        Args:
            aabb: (int) de te tekenen aabb waarde.
            color: (tuple) de te tekenen kleur in RGB.
        """
        points = [(aabb.lowerBound.x, aabb.lowerBound.y),
                  (aabb.upperBound.x, aabb.lowerBound.y),
                  (aabb.upperBound.x, aabb.upperBound.y),
                  (aabb.lowerBound.x, aabb.upperBound.y)]

        pygame.draw.aalines(self.surface, color, True, points)

    def DrawSegment(self, p1, p2, color):
        """Teken een lijn vanaf het segment p1 tot p2 met een gekozen kleur.

        Args:
            p1: (tuple) x & y coördinaten van pixelpositie 1.
            p2: (tuple) x & y coördinaten van pixelpositie 2.
            color: (tuple) kleur die getekend moet worden in RGB.
        """
        pygame.draw.aaline(self.surface, color.bytes, p1, p2)

    def DrawTransform(self, xf):
        """Teken de getransformeerde van xf op het scherm.
        
        Args:
            xf: (tuple) xf waarde die moet worden getekend.
        """
        p1 = xf.position
        p2 = self.to_screen(p1 + self.axisScale * xf.R.x_axis)
        p3 = self.to_screen(p1 + self.axisScale * xf.R.y_axis)
        p1 = self.to_screen(p1)
        pygame.draw.aaline(self.surface, (255, 0, 0), p1, p2)
        pygame.draw.aaline(self.surface, (0, 255, 0), p1, p3)


kleur die getekend moet worden in RGB.
    def DrawCircle(self, center, radius, color, drawwidth=1):
        """Teken een cirkel in de simulatie.
        
        Args:
            center: (tuple) x,y coördinaten op de simulatie.
            radius: (int) pixel breedte vanaf de center.
            color: (tuple) kleur die getekend moet worden in RGB.
            drawwidth: (int, optional) dikte van de lijn. Standaard 1.

        Note:
            Wanneer een ingekleurde cirkel getekend moet worden gebruik: DrawSolidCircle.
        """
        radius *= self.zoom
        if radius < 1:
            radius = 1
        else:
            radius = int(radius)

        pygame.draw.circle(self.surface, color.bytes,
                           center, radius, drawwidth)

    def DrawSolidCircle(self, center, radius, axis, color):
        """Teken een ingekleurde cirkel in de simulatie.
        
        Args:
            center: (tuple) x,y coördinaten op de simulatie.
            radius: (int) pixel breedte vanaf de center.
            color: (tuple) kleur die getekend moet worden in RGB.
            drawwidth: (int, optional) dikte van de lijn. Standaard 1.
        
        Note:
            Wanneer een niet ingekleurde cirkel getekend moet worden gebruik: DrawCircle.
        """
        radius *= self.zoom
        if radius < 1:
            radius = 1
        else:
            radius = int(radius)

        pygame.draw.circle(self.surface, (color / 2).bytes + [127],
                           center, radius, 0)
        pygame.draw.circle(self.surface, color.bytes, center, radius, 1)
        pygame.draw.aaline(self.surface, (255, 0, 0), center,
                           (center[0] - radius * axis[0],
                            center[1] + radius * axis[1]))

    def DrawPolygon(self, vertices, color):
        """Teken een polygon op het scherm.
        
        Args:
            vertices: (tuple) hoekpunten van het te tekenen polygon.
            color: (tuple) kleur die getekend moet worden in RGB.
        """
        if not vertices:
            return

        if len(vertices) == 2:
            pygame.draw.aaline(self.surface, color.bytes,
                               vertices[0], vertices)
        else:
            pygame.draw.polygon(self.surface, color.bytes, vertices, 1)

    def DrawSolidPolygon(self, vertices, color):
        """Teken een ingekleurde polygon.
        
        Args:
            vertices: (tuple) hoekpunten van het te tekenen polygon.
            color: (tuple) kleur die getekend moet worden in RGB.
        Note:
            Wanneer een niet ingekleurde polygon getekend moet worden kan de functi
        """
        if not vertices:
            return

        if len(vertices) == 2:
            pygame.draw.aaline(self.surface, color.bytes,
                               vertices[0], vertices[1])
        else:
            pygame.draw.polygon(
                self.surface, (color / 2).bytes + [127], vertices, 0)
            pygame.draw.polygon(self.surface, color.bytes, vertices, 1)

    # the to_screen conversions are done in C with b2DrawExtended, leading to
    # an increase in fps.
    # You can also use the base b2Draw and implement these yourself, as the
    # b2DrawExtended is implemented:
    # def to_screen(self, point):
    #     """
    #     Convert from world to screen coordinates.
    #     In the class instance, we store a zoom factor, an offset indicating where
    #     the view extents start at, and the screen size (in pixels).
    #     """
    #     x=(point.x * self.zoom)-self.offset.x
    #     if self.flipX:
    #         x = self.screenSize.x - x
    #     y=(point.y * self.zoom)-self.offset.y
    #     if self.flipY:
    #         y = self.screenSize.y-y
    #     return (x, y)


class PygameFramework(FrameworkBase):
    """PygameFramework is het raamwerk van de Box2D simulatie.
    
    Args:
        FrameworkBase: (class) base van het Pygame raamwerk.
    
    **Athor**:
        Box2D         \n
    **Version**:
        1.01          \n
    **Date**:
        22-1-2020 
    """
    TEXTLINE_START = 30

    def setup_keys(self):
        """Initaliseer de knoppen.
        """
        keys = [s for s in dir(pygame.locals) if s.startswith('K_')]
        for key in keys:
            value = getattr(pygame.locals, key)
            setattr(Keys, key, value)

    def __reset(self):
        """Reset de PygameFramework klasse.
        """
        # Screen/rendering-related
        self._viewZoom = 10.0
        self._viewCenter = None
        self._viewOffset = None
        self.screenSize = None
        self.rMouseDown = False
        self.textLine = 30
        self.font = None
        self.fps = 0

        # GUI-related (PGU)
        self.gui_app = None
        self.gui_table = None
        self.setup_keys()

    def __init__(self):
        """Initaliseer de PygameFramework class.
        """
        super(PygameFramework, self).__init__()

        self.__reset()
        if fwSettings.onlyInit:  # testing mode doesn't initialize pygame
            return

        print('Initializing pygame framework...')
        # Pygame Initialization
        pygame.init()
        caption = "Python Box2D Testbed - " + self.name
        pygame.display.set_caption(caption)

        # Screen and debug draw
        self.screen = pygame.display.set_mode((640, 480))
        self.screenSize = b2Vec2(*self.screen.get_size())

        self.renderer = PygameDraw(surface=self.screen, test=self)
        self.world.renderer = self.renderer

        self.running = True

        try:
            self.font = pygame.font.Font(None, 15)
        except IOError:
            try:
                self.font = pygame.font.Font("freesansbold.ttf", 15)
            except IOError:
                print("Unable to load default font or 'freesansbold.ttf'")
                print("Disabling text drawing.")
                self.Print = lambda *args: 0
                self.DrawStringAt = lambda *args: 0

        # GUI Initialization
        if GUIEnabled:
            self.gui_app = gui.App()
            self.gui_table = fwGUI(self.settings)
            container = gui.Container(align=1, valign=-1)
            container.add(self.gui_table, 0, 0)
            self.gui_app.init(container)

        self.viewCenter = (0, 20.0)
        self.groundbody = self.world.CreateBody()

    def setCenter(self, value):
        """Ververst het scherm gebaseert op het midden van het scherm.

        Args:
            value: (tuple) waarde die geset worden geset.
        """
        self._viewCenter = b2Vec2(*value)
        self._viewCenter *= self._viewZoom
        self._viewOffset = self._viewCenter - self.screenSize / 2

    def setZoom(self, zoom):
        self._viewZoom = zoom

    viewZoom = property(lambda self: self._viewZoom, setZoom,
                        doc='Zoom factor for the display')
    viewCenter = property(lambda self: self._viewCenter / self._viewZoom, setCenter,
                          doc='Screen center in camera coordinates')
    viewOffset = property(lambda self: self._viewOffset,
                          doc='The offset of the top-left corner of the screen')

    def checkEvents(self):
        """Checkt of er een pygame event optreed (toetsenbord of muis).
        Geeft het gevonden event door aan de GUI.
        """
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == Keys.K_ESCAPE):
                return False
            elif event.type == KEYDOWN:
                self._Keyboard_Event(event.key, down=True)
            elif event.type == KEYUP:
                self._Keyboard_Event(event.key, down=False)
            elif event.type == MOUSEBUTTONDOWN:
                p = self.ConvertScreenToWorld(*event.pos)
                if event.button == 1:  # left
                    mods = pygame.key.get_mods()
                    if mods & KMOD_LSHIFT:
                        self.ShiftMouseDown(p)
                    else:
                        self.MouseDown(p)
                elif event.button == 2:  # middle
                    pass
                elif event.button == 3:  # right
                    self.rMouseDown = True
                elif event.button == 4:
                    self.viewZoom *= 1.1
                elif event.button == 5:
                    self.viewZoom /= 1.1
            elif event.type == MOUSEBUTTONUP:
                p = self.ConvertScreenToWorld(*event.pos)
                if event.button == 3:  # right
                    self.rMouseDown = False
                else:
                    self.MouseUp(p)
            elif event.type == MOUSEMOTION:
                p = self.ConvertScreenToWorld(*event.pos)

                self.MouseMove(p)

                if self.rMouseDown:
                    self.viewCenter -= (event.rel[0] /
                                        5.0, -event.rel[1] / 5.0)

            if GUIEnabled:
                self.gui_app.event(event)  # Pass the event to the GUI

        return True
    
    #TODO: Vanaf hier wordt de AI geprogrammeerd.

    def run(self):
        """
        Main loop van de class.

        Wordt uitgevoerd wanneer checkEvents controleert of er een 
        event is opgetreden.

        Ververst het scherm en zorgt dat de GUI de objecten weergeeft.
        """
        # If any of the test constructors update the settings, reflect
        # those changes on the GUI before running
        if GUIEnabled:
            self.gui_table.updateGUI(self.settings)

        clock = pygame.time.Clock()

        # Initialize the decay rate (that will use to reduce epsilon) 
        decay_step = 0
                    # Set step to 0
        step = 0

        self.running = self.checkEvents()
        self.screen.fill((0, 0, 0))

        # Check keys that should be checked every loop (not only on initial
        # keydown)
        self.CheckKeys()

        # Run the simulation loop
        self.SimulationLoop()

        if GUIEnabled and self.settings.drawMenu:
            self.gui_app.paint(self.screen)

        pygame.display.flip()
        clock.tick(self.settings.c_hz)
        self.fps = clock.get_fps()

        # Make a new episode and observe the first state
        #game.new_episode()

        while self.running:
            self.fs.run()
            # time.sleep(0.03)
            # print(possible_actions[2])
            # print(action)

            self.running = self.checkEvents()
            self.screen.fill((0, 0, 0))

            # Check keys that should be checked every loop (not only on initial
            # keydown)
            self.CheckKeys()

            # Run the simulation loop
            self.SimulationLoop()

            if GUIEnabled and self.settings.drawMenu:
                self.gui_app.paint(self.screen)

            pygame.display.flip()
            clock.tick(self.settings.c_hz)
            self.fps = clock.get_fps()

            step += 1
                
            # Increase decay_step
            decay_step +=1
            
            # Predict the action to take and take it
            # pc.driver.transceive_message(0, Commands.STOP)
            # time.sleep(2)

        self.fs.dql.sess.close()
        self.world.contactListener = None
        self.world.destructionListener = None
        self.world.renderer = None
        self.fs.camera.camera.release()

    def _Keyboard_Event(self, key, down=True):
        """Interne keyboard events.
       
        Args:
            key: (char) ingedrukte knop.
            down: (bool, optional) boolean of de knop is ingedrukt, true = ingedrukt, false = niet ingedrukt.
            Standaard True.

        Warning:
            Overschrijf dit niet!
        """
        if down:
            if key == Keys.K_z:       # Zoom in
                self.viewZoom = min(1.1 * self.viewZoom, 50.0)
            elif key == Keys.K_x:     # Zoom out
                self.viewZoom = max(0.9 * self.viewZoom, 0.02)
            elif key == Keys.K_SPACE:  # Launch a bomb
                self.LaunchRandomBomb()
            elif key == Keys.K_F1:    # Toggle drawing the menu
                self.settings.drawMenu = not self.settings.drawMenu
            elif key == Keys.K_F2:    # Do a single step
                self.settings.singleStep = True
                if GUIEnabled:
                    self.gui_table.updateGUI(self.settings)
            else:              # Inform the test of the key press
                self.Keyboard(key, self.settings)
        else:
            self.KeyboardUp(key)

    def CheckKeys(self):
        """Controleer de toetsen die worden ingedrukt in de main loop.
        """
        pygame.event.pump()
        self.keys = keys = pygame.key.get_pressed()
        if keys[Keys.K_LEFT]:
            self.viewCenter -= (0.5, 0)
        elif keys[Keys.K_RIGHT]:
            self.viewCenter += (0.5, 0)

        if keys[Keys.K_UP]:
            self.viewCenter += (0, 0.5)
        elif keys[Keys.K_DOWN]:
            self.viewCenter -= (0, 0.5)

        if keys[Keys.K_HOME]:
            self.viewZoom = 1.0
            self.viewCenter = (0.0, 20.0)

    def Step(self, settings):
        """Zet een stap verder in de simualtie.
        
        Args:
            settings: (class) instellingen van de klasse.
        """
        if GUIEnabled:
            # Update the settings based on the GUI
            self.gui_table.updateSettings(self.settings)

        super(PygameFramework, self).Step(settings)

        if GUIEnabled:
            # In case during the step the settings changed, update the GUI reflecting
            # those settings.
            self.gui_table.updateGUI(self.settings)

    def ConvertScreenToWorld(self, x, y):
        """Converteert het scherm naar de simulatie.
        
        Args:
            x: (int) coördinaat x.
            y: (int) coördinaat y.
        """
        return b2Vec2((x + self.viewOffset.x) / self.viewZoom,
                      ((self.screenSize.y - y + self.viewOffset.y) / self.viewZoom))

    def DrawStringAt(self, x, y, str, color=(229, 153, 153, 255)):
        """Teken een string van tekst naar de Box2D simulatie op de x,y coördinaten.
        
        Args:
            x: (int) coördinaat x.
            y: (int) coördinaat y.
            str: (string) tekst die moet worden weergegeven in de simulatie.
            color: (tuple, optional) kleur van het object in RGB. Standaard (229, 153, 153, 255).
        """
        self.screen.blit(self.font.render(str, True, color), (x, y))

    def Print(self, str, color=(229, 153, 153, 255)):
        """Print tekst op de bovenste coördinaten.

        Args:
            str: (string) tekst die moet worden weergegeven.
            color: (tuple, optional) kleur van het object in RGB. Standaard (229, 153, 153, 255).
        """
        self.screen.blit(self.font.render(
            str, True, color), (5, self.textLine))
        self.textLine += 15

    def Keyboard(self, key):
        """Fucntie die standaard wordt uitgevoerd bij het intoetsen van een toets. Resulteert in niks.
        
        Args:
            key: (char) toets die wordt ingedrukt.
        """
        pass

    def KeyboardUp(self, key):
        """Zie Keyboard functie voor beschrijven.
        
        Args:
            key: (char) toets die wordt ingedrukt.
        """
        pass
