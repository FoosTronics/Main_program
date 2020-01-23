# AI_Foosball_Simulation
AI Foosball Simulation

Installatie instructies Windows. Hierbij wordt vanuit gegaan dat je al conda en pip kan gebruiken in je CMD (of Anaconda Prompt):
1. Zorg voor een nieuwe environment in conda (dit is niet noodzakelijk, maar zorgt wel dat je python versiebeheer niet in de komt).
Tikkel hiervoor in je CMD (python 3.6 is noodzakelijk):

    ```bash
    conda create -n py36 python=3.6
    ```
2. Activeer deze environment (deze moet iedere keer in je CMD in tikkelen als je de simulatie wilt opstarten):

    ```bash
    conda activate py36
    ```

3. Nu moet pyBox2D gecloned en gebuild worden. Zet de CMD in de map waar je de lib wilt bouwen:
    ```bash
    CD C:\de\locatie\van\de\map\die\je\hebt\gekozen
    ```
4. Clone pyBox2D:
    ```bash
    git clone https://github.com/pybox2d/pybox2d
    ```
5. Ga die map in:
    ```bash
    cd pybox2d
    ```
6. Build die hele handel:
    ```bash
    python setup.py build
    ```
7. Installeer die gebuilde handel:
    ```bash
    python setup.py install
    ```
8.installeer dan de volgende benodigde libs (de versie nummer die Daniël gebruikt staat erbij, maar is niet noodzakelijk te gebruiken als al werkt):

    | Backend        | Install                                                       | Homepage                             |
    | -------------  | ------------------------------------------------------------- | ------------------------------------ |
    | pygame (2.0.0) | `pip install pygame`                                          | http://pygame.org                    |  
    | pyqt4 (4.10.4) | `conda install pyqt=4`                                        | https://www.riverbankcomputing.com/  |
    | pyglet         | `pip install pyglet`                                          | http://pyglet.org                    |
    | opencv-python  | `pip install opencv-python`                                   | http://opencv.org                    |
    | (3.4.6.27)     |                                                               |                                      |
    |  swig-3.0.12   | `conda install swig`                                          | http://www.swig.org/                 |


9. Clone nu de repo met de simulatie als dat nog niet gedaan is (het gebruik van een Git GUI is hiervoor geadviseerd)

10. Zet de CMD in de map waar de simulatie repo staat:
    ```bash
    CD C:\de\locatie\van\de\map\waarin\de\simulatie\staat
    ```
11. ga dan naar deze map:
    ```bash
    CD keeper_sim
    ```
12. Als alle stappen van hierboven hebt doorgeworsteld, zou zou de simulatie moeten draaien met deze laatste commando:
    ```bash
    python keeper_sim.py
    ```
13. Als de bovenstaande commando werkt, zal de simulatie ook werken in je Python IDE naar voorkeur (als je gemaakte conda environment in kan werken)
