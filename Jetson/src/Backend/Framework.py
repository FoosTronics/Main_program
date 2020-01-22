""" 
    Geraamte voor de Box2D simulatie.
    De basis van het geraamte is FrameworkBase. Kijk bij de hulp sectie hiervan voor meer informatie. 
    
    File:
        Framework.py
    Date:
        22-1-2020
    Version:
        1.12
    Modifier:
        Daniël Boon
    Used_IDE:
        Visual Studio Code (Python 3.6.7 64-bit)
    Schematic:
        -
    Version management:
        1.0:
            Headers toegevoegd
        1.1:
            Commentaar toegevoegd in Google docstring format. 
        1.11:
            Spelling en grammatica nagekeken
            Engels vertaald naar Nederlands
        1.12:
            Commentaar afgemaakt
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# C++ version Copyright (c) 2006-2007 Erin Catto http://www.box2d.org
# Python version by Ken Lauer / sirkne at gmail dot com
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

#from .PygameFramework import PygameFramework as Framework
from .Settings import fwSettings

from time import time

from Box2D.Box2D import (b2World, b2AABB, b2CircleShape, b2Color, b2Vec2)
from Box2D.Box2D import (b2ContactListener, b2DestructionListener, b2DrawExtended)
from Box2D.Box2D import (b2Fixture, b2FixtureDef, b2Joint)
from Box2D.Box2D import (b2GetPointStates, b2QueryCallback, b2Random)
from Box2D.Box2D import (b2_addState, b2_dynamicBody, b2_epsilon, b2_persistState)


class fwDestructionListener(b2DestructionListener):
    """The destruction listener callback:
    "SayGoodbye" wordt aangeroepen als een verbinding of vorm is verwijdert.
    
    Args:
        b2DestructionListener ([class]): Verbindingen en vormen worden vernietigd wanneer 
        hun bijbehorende lichaam wordt vernietigd. Implementeer deze luisteraar zodat u 
        verwijzingen naar deze verbindingen en vormen teniet kunt doen.
        
    **Modifier**: 
        Daniël Boon   \n
    **Version**:
        1.12           \n
    **Date**:
        22-1-2020
    
    Warning:
        Deze code is geschreven door derden en waar nodig aangepast/vertaald door de projectgroep. 
        Dit is daarom niet volledig volgens Doxygen geformuleerd.

    """

    def __init__(self, test, **kwargs):
        """Hier wordt de klasse van fwDestructionListener geinitialiseerd.
        
        Args:
            test ([type]): [description]
        """
        super(fwDestructionListener, self).__init__(**kwargs)
        self.test = test


    def SayGoodbye(self, obj):
        """Verwijder een Box2D object.
        
        Args:
            obj: (@@@) Object die moet worden verwijderd uit de simulatie.
        """
        if isinstance(obj, b2Joint):
            if self.test.mouseJoint == obj:
                self.test.mouseJoint = None
            else:
                self.test.JointDestroyed(obj)
        elif isinstance(obj, b2Fixture):
            self.test.FixtureDestroyed(obj)

class fwQueryCallback(b2QueryCallback):
    """Klasse voor het aanmaken van Query callbacks
    
    Args:
        b2QueryCallback ([type]): [description]
    
    Returns:
        [type]: [description]

    **Modifier**: 
        Daniël Boon   \n
    **Version**:
        1.12           \n
    **Date**:
        22-1-2020  
    
    Warning:
        Deze code is geschreven door derden en waar nodig aangepast/vertaald door de projectgroep. 
        Dit is daarom niet volledig volgens Doxygen geformuleerd.

    """

    def __init__(self, p):
        """Initialisatie van de klasse fwQueryCallback.
        
        Args:
            p ([type]): [description]
        """
        super(fwQueryCallback, self).__init__()
        self.point = p
        self.fixture = None

    def ReportFixture(self, fixture):
        """Hier wordt gecontroleerd of er een nieuw object is aangemaakt.

        Args:
            fixture ([type]): [description]
        
        Returns:
            [type]: [description]
        """
        body = fixture.body
        if body.type == b2_dynamicBody:
            inside = fixture.TestPoint(self.point)
            if inside:
                self.fixture = fixture
                # We hebben het object gevonden, dus stop met vragen.
                return False
        # Ga door met vragen.
        return True


class Keys(object):
    """Deze functie wordt aangeroepen wanneer een andere functie een pointer genereerd, om nieuwe waardes te verversen.
    
    Args:
        object ([type]): [description]
    
    **Modifier**: 
        Daniël Boon   \n
    **Version**:
        1.12           \n
    **Date**:
        22-1-2020
    
    Warning:
        Deze code is geschreven door derden en waar nodig aangepast/vertaald door de projectgroep. 
        Dit is daarom niet volledig volgens Doxygen geformuleerd.

    """
    pass


class FrameworkBase(b2ContactListener):
    """De basis van het hoofd testbed geraamte.

    Als u van plan bent het testbed-framework te gebruiken en:
     * U wilt uw eigen renderer implementeren (anders dan Pygame, etc.):
       Leid hieruit je eigen klasse om je eigen testen te implementeren.
       Zie empty.py of een van de andere tests voor meer informatie.
     * Wilt u uw eigen renderer NIET implementeren:
       Leid je klasse uit Framework. De gekozen renderer in
       fwSettings (zie settings.py) of op de opdrachtregel wordt automatisch
       gebruikt voor uw test.

    **Modifier**: 
        Daniël Boon   \n
    **Version**:
        1.12          \n
    **Date**:
        22-1-2020   

    Warning:
        Deze code is geschreven door derden en waar nodig aangepast/vertaald door de projectgroep. 
        Dit is daarom niet volledig volgens Doxygen geformuleerd.
        
    """

    name = "None"
    description = None
    TEXTLINE_START = 30
    colors = {
        'mouse_point': b2Color(0, 1, 0),
        'bomb_center': b2Color(0, 0, 1.0),
        'bomb_line': b2Color(0, 1.0, 1.0),
        'joint_line': b2Color(0.8, 0.8, 0.8),
        'contact_add': b2Color(0.3, 0.95, 0.3),
        'contact_persist': b2Color(0.3, 0.3, 0.95),
        'contact_normal': b2Color(0.4, 0.9, 0.4),
    }

    def __reset(self):
        """Herstel alle variabelen naar hun start waardes.
        Niet aanroepen behalve bij initialisatie.
        """
        
        # Box2D-gerelateerd
        self.points = []
        self.world = None
        self.bomb = None
        self.mouseJoint = None
        self.settings = fwSettings
        self.bombSpawning = False
        self.bombSpawnPoint = None
        self.mouseWorld = None
        self.using_contacts = False
        self.stepCount = 0

        # Box2D-callbacks
        self.destructionListener = None
        self.renderer = None

    def __init__(self):
        """Initialisatie van de FrameworkBase klasse.
        """
        super(FrameworkBase, self).__init__()

        self.__reset()

        # Box2D Initialisatie
        self.world = b2World(gravity=(0, -10), doSleep=True)

        self.destructionListener = fwDestructionListener(test=self)
        self.world.destructionListener = self.destructionListener
        self.world.contactListener = self
        self.t_steps, self.t_draws = [], []
        self.fps = 0
        self.groundbody = 0
        self.settings.timeStep = 1 / 60
        self.settings.c_hz = 60

    def __del__(self):
        """Deze functie wordt aangeroepen wanneer een andere functie een pointer genereerd, om nieuwe waardes te verversen.
        """
        pass

    def Step(self, settings):
        """De belangrijkste stap voor de fysica.

        Zorgt voor de natuurkundige tekening (callbacks worden uitgevoerd na de world.Step() )
        en voor het tekeningen van aanvullende informatie.
        
        Args:
            settings (Class): instellingen van de simulatie. 
        """

        self.stepCount += 1
        # Doe niks als de settings HZ <= 0.
        if settings.hz > 0.0:
            timeStep = 1.0 / settings.hz
        else:
            timeStep = 0.0

        renderer = self.renderer

        # Als er is gepauzeerd, weergeef dat.
        if settings.pause:
            if settings.singleStep:
                settings.singleStep = False
            else:
                timeStep = 0.0

            self.Print("****GEPAUZEERD****", (200, 0, 0))

        # Zet de flags gebaseerd op wat de instellingen laten zien.
        if renderer:
            # convertVertices is alleen van toepassing als b2DrawExtended gebruikt wordt.  
            # Het geeft een indicatie dat de C code de box2d coördinaten moet omzetten naar beeld coördinaten.
            is_extended = isinstance(renderer, b2DrawExtended)
            renderer.flags = dict(drawShapes=settings.drawShapes,
                                  drawJoints=settings.drawJoints,
                                  drawAABBs=settings.drawAABBs,
                                  drawPairs=settings.drawPairs,
                                  drawCOMs=settings.drawCOMs,
                                  convertVertices=is_extended,
                                  )

        # Zet de andere instellingen die niet in de flags zitten.
        self.world.warmStarting = settings.enableWarmStarting
        self.world.continuousPhysics = settings.enableContinuous
        self.world.subStepping = settings.enableSubStepping

        # Herstel de punten voor collision.
        self.points = []

        # Vertel Box2D om te stappen.
        t_step = time()
        
        self.world.Step(self.settings.timeStep, settings.velocityIterations,
                        settings.positionIterations)

        self.world.ClearForces()
        t_step = time() - t_step

        # Update de debug teken instellingen zodat de hoekpunten op de juiste 
        # wijze omgezet worden naar beeld coördinaten
        t_draw = time()

        if renderer is not None:
            renderer.StartDraw()

        self.world.DrawDebugData()

        # Als de bom is bevroren, zorg dat deze verdwijnt.
        if self.bomb and not self.bomb.awake:
            self.world.DestroyBody(self.bomb)
            self.bomb = None

        # Zorg voor aanvullend tekeningen (fps, mouse joint, slingshot bomb,
        # contact points)

        if renderer:
            # Als er een mouse join is, teken dan de connectie tussen het object en de huidige pointer positie.
            if self.mouseJoint:
                p1 = renderer.to_screen(self.mouseJoint.anchorB)
                p2 = renderer.to_screen(self.mouseJoint.target)

                renderer.DrawPoint(p1, settings.pointSize,
                                   self.colors['mouse_point'])
                renderer.DrawPoint(p2, settings.pointSize,
                                   self.colors['mouse_point'])
                renderer.DrawSegment(p1, p2, self.colors['joint_line'])

            # Teken de slingshot bom.
            if self.bombSpawning:
                renderer.DrawPoint(renderer.to_screen(self.bombSpawnPoint),
                                   settings.pointSize, self.colors['bomb_center'])
                renderer.DrawSegment(renderer.to_screen(self.bombSpawnPoint),
                                     renderer.to_screen(self.mouseWorld),
                                     self.colors['bomb_line'])

            # Teken elk van de contact punten in verschillende kleuren.
            if self.settings.drawContactPoints:
                for point in self.points:
                    if point['state'] == b2_addState:
                        renderer.DrawPoint(renderer.to_screen(point['position']),
                                           settings.pointSize,
                                           self.colors['contact_add'])
                    elif point['state'] == b2_persistState:
                        renderer.DrawPoint(renderer.to_screen(point['position']),
                                           settings.pointSize,
                                           self.colors['contact_persist'])

            if settings.drawContactNormals:
                for point in self.points:
                    p1 = renderer.to_screen(point['position'])
                    p2 = renderer.axisScale * point['normal'] + p1
                    renderer.DrawSegment(p1, p2, self.colors['contact_normal'])

            renderer.EndDraw()
            t_draw = time() - t_draw

            t_draw = max(b2_epsilon, t_draw)
            t_step = max(b2_epsilon, t_step)

            try:
                self.t_draws.append(1.0 / t_draw)
            except:
                pass
            else:
                if len(self.t_draws) > 2:
                    self.t_draws.pop(0)

            try:
                self.t_steps.append(1.0 / t_step)
            except:
                pass
            else:
                if len(self.t_steps) > 2:
                    self.t_steps.pop(0)

            if settings.drawFPS:
                self.Print("Gecombineerde FPS %d" % self.fps)

            if settings.drawStats:
                self.Print("bodies=%d contacts=%d joints=%d proxies=%d" %
                           (self.world.bodyCount, self.world.contactCount,
                            self.world.jointCount, self.world.proxyCount))

                self.Print("hz %d vel/pos iterations %d/%d" %
                           (settings.hz, settings.velocityIterations,
                            settings.positionIterations))

                if self.t_draws and self.t_steps:
                    self.Print("Potential draw rate: %.2f fps Step rate: %.2f Hz"
                               "" % (sum(self.t_draws) / len(self.t_draws),
                                     sum(self.t_steps) / len(self.t_steps))
                               )

    
    # TODO: Dit is onbekend voor mij.   @@@
    def ShiftMouseDown(self, p):
        """Indicatie dat er een linker klik op punt p aanwezig was (wereld coördinaten) met de linker shift-toets ingedrukt.
        
        Args:
            p ([type]): [description]
        """
        self.mouseWorld = p

        if not self.mouseJoint:
            self.SpawnBomb(p)

    # TODO: Dit is onbekend voor mij.   @@@
    def MouseDown(self, p):
        """Indicatie dat er een linker klik op punt p aanwezig was (wereld coördinaten)
        
        Args:
            p ([type]): [description]
        """
        if self.mouseJoint is not None:
            return

        # Creeër en mouse joint op het geselecteerde lichaam (er van uit gaan dat het dynamisch is).
        # Maak een kleine doos.
        aabb = b2AABB(lowerBound=p - (0.001, 0.001),
                      upperBound=p + (0.001, 0.001))

        # Vraag de wereld voor overlappende figuren.
        query = fwQueryCallback(p)
        self.world.QueryAABB(query, aabb)

        if query.fixture:
            body = query.fixture.body
            # Een lichaam is geselecteerd. Creeër de mouse joint. 
            self.mouseJoint = self.world.CreateMouseJoint(
                bodyA=self.groundbody,
                bodyB=body,
                target=p,
                maxForce=1000.0 * body.mass)
            body.awake = True

    # TODO: Dit is onbekend voor mij.   @@@
    def MouseUp(self, p):
        """Linker muis knop omhoog.
        
        Args:
            p ([type]): [description]
        """
        if self.mouseJoint:
            self.world.DestroyJoint(self.mouseJoint)
            self.mouseJoint = None

        if self.bombSpawning:
            self.CompleteBombSpawn(p)

    # TODO: Dit is onbekend voor mij.   @@@
    def MouseMove(self, p):
        """Muis verschoven naar punt p, in wereld coördinaten.
        
        Args:
            p ([type]): [description]
        """
        self.mouseWorld = p
        if self.mouseJoint:
            self.mouseJoint.target = p

    # TODO: Dit is onbekend voor mij.   @@@

    def SpawnBomb(self, worldPt):
        """Begint de katapultbom door de beginpositie vast te leggen.
        Zodra de gebruiker de muis versleept en vervolgens loslaat
        zal CompleteBombSpawn worden opgeroepen en de werkelijke bom zal worden
        vrijgelaten.

        Args:
            worldPt ([type]): [description]
        """
        self.bombSpawnPoint = worldPt.copy()
        self.bombSpawning = True

    # TODO: Dit is onbekend voor mij.   @@@

    def CompleteBombSpawn(self, p):
        """Maak de katapultbom op basis van de twee punten
        (doorgegeven van de worldPt aan SpawnBomb naar p hier)

        Args:
            p ([type]): [description]
        """
        if not self.bombSpawning:
            return
        multiplier = 30.0
        vel = self.bombSpawnPoint - p
        vel *= multiplier
        self.LaunchBomb(self.bombSpawnPoint, vel)
        self.bombSpawning = False

    # TODO: Dit is onbekend voor mij.   @@@

    def LaunchBomb(self, position, velocity):
        """Een bom is een eenvoudige cirkel met de opgegeven positie en snelheid.
        Positie en snelheid moeten b2Vec2's zijn.

        Args:
            position ([type]): [description]
            velocity ([type]): [description]
        """
        if self.bomb:
            self.world.DestroyBody(self.bomb)
            self.bomb = None

        self.bomb = self.world.CreateDynamicBody(
            allowSleep=True,
            position=position,
            linearVelocity=velocity,
            fixtures=b2FixtureDef(
                shape=b2CircleShape(radius=0.3),
                density=20,
                restitution=0.1)

        )

    # TODO: Dit is onbekend voor mij.   @@@

    def LaunchRandomBomb(self):
        """Creëer een nieuwe bom en lanceer deze op het testbed.
        
        """
        p = b2Vec2(b2Random(-15.0, 15.0), 30.0)
        v = -5.0 * p
        self.LaunchBomb(p, v)

    def SimulationLoop(self):
        """De hoofd simulatie loop. Niet overschrijven, maar vervang Step in plaats daarvan.
        """ 

        # Reset the text line to start the text from the top
        self.textLine = self.TEXTLINE_START

        # Draw the name of the test running
        self.Print(self.name, (127, 127, 255))

        if self.description:
            # Draw the name of the test running
            for s in self.description.split('\n'):
                self.Print(s, (127, 255, 127))

        # Do the main physics step
        self.Step(self.settings)

    def ConvertScreenToWorld(self, x, y):
        """Geeft een b2Vec2 terug in wereld coördinaten van het doorgegeven scherm.

        Args:
            x (int): x cordinaat.
            y (int): y cordinaat.
        
        Raises:
            NotImplementedError: Error dat het nog niet is aangemaakt.
        """
        raise NotImplementedError()

    def DrawStringAt(self, x, y, str, color=(229, 153, 153, 255)):
        """Teken een string van tekst naar het scherm op de x,y coördinaten.
        NOTE: Renderer subklasses moeten dit implementeren.
        
        Args:
            x ([type]): [description]
            y ([type]): [description]
            str ([type]): [description]
            color (tuple, optional): [description]. Defaults to (229, 153, 153, 255).
        
        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError()

    def Print(self, str, color=(229, 153, 153, 255)):
        """Teken wat tekst op de bovenste statusregels
         en ga door naar de volgende regel.
        NOTE: Renderer subklasses moeten dit implementeren. 
        
        Args:
            str ([type]): [description]
            color (tuple, optional): [description]. Defaults to (229, 153, 153, 255).
        
        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError()

    def PreSolve(self, contact, old_manifold):
        """Dit is een kritieke functie wanneer er veel contacten zijn in de wereld.
        Deze moet zoveel mogelijk geoptimaliseerd worden.
        
        Args:
            contact ([type]): [description]
            old_manifold ([type]): [description]
        """
        if not (self.settings.drawContactPoints or
                self.settings.drawContactNormals or self.using_contacts):
            return
        elif len(self.points) > self.settings.maxContactPoints:
            return

        manifold = contact.manifold
        if manifold.pointCount == 0:
            return

        state1, state2 = b2GetPointStates(old_manifold, manifold)
        if not state2:
            return

        worldManifold = contact.worldManifold

        # TODO: find some way to speed all of this up.
        self.points.extend([dict(fixtureA=contact.fixtureA,
                                 fixtureB=contact.fixtureB,
                                 position=worldManifold.points[i],
                                 normal=worldManifold.normal.copy(),
                                 state=state2[i],
                                 )
                            for i, point in enumerate(state2)])

    # These can/should be implemented in the test subclass: (Step() also if necessary)
    # See empty.py for a simple example.
    def BeginContact(self, contact):
        """Deze functie wordt aangeroepen wanneer een er begonnen wordt met een contact, om nieuwe waardes te verversen.
        
        Args:
            contact ([type]): [description]
        """
        pass

    def EndContact(self, contact):
        """Deze functie wordt aangeroepen wanneer een het contact wordt beindigd, om nieuwe waardes te verversen.
        
        Args:
            contact ([type]): [description]
        """
        pass

    def PostSolve(self, contact, impulse):
        """Deze functie wordt aangeroepen om een vorige waarde te verversen.
        
        Args:
            contact ([type]): [description]
            impulse ([type]): [description]
        """
        pass

    def FixtureDestroyed(self, fixture):
        """Deze functie wordt aangeroepen als een vorm wordt verwijderd.
        
        Args:
            fixture ([type]): [description]
        """
        pass

    def JointDestroyed(self, joint):
        """Deze functie wordt aangeroepen als een verbinding wordt verwijderd.

        Args:
            joint ([type]): [description]
        """
        pass

    def Keyboard(self, key, settings):
        """Deze functie wordt aangeroepen als een toetsen wordt gebruikt.

        Args:
            key ([type]): [description]
            settings ([type]): [description]
        """
        pass

    def KeyboardUp(self, key):
        """Deze functie wordt aangeroepen als de pijl naar boven toets wordt gebruikt.

        Args:
            key ([type]): [description]
        """
        pass


def main(test_class):
    """Loads the test class and executes it.

    Args:
        test_class ([type]): [description]
    """
    print("Loading %s..." % test_class.name)
    test = test_class
    if fwSettings.onlyInit:
        return
    test.run()


if __name__ == '__main__':
    print('Please run one of the examples directly. This is just the base for '
          'all of the frameworks.')
    exit(1)


# # Your framework classes should follow this format. If it is the 'foobar'
# # framework, then your file should be 'backends/foobar_framework.py' and you
# # should have a class 'FoobarFramework' that subclasses FrameworkBase. Ensure
# # proper capitalization for portability.
#
try:
    framework_name = '%sFramework' % (fwSettings.backend.lower())
    __import__('src.Backend', globals(), fromlist=[framework_name], level=1)
    framework_module = getattr(src.Backend, framework_name)
    Framework = getattr(framework_module,
                        '%sFramework' % fwSettings.backend.capitalize())
except Exception as ex:
    print('Unable to import the back-end %s: %s' % (fwSettings.backend, ex))
    print('Attempting to fall back on the pygame back-end.')

    from .PygameFramework import PygameFramework as Framework
