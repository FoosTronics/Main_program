"""
    Library of extra functionalities for the vision application. 
    Developed by third-party developers.         

    File:
        Extra.py
    Date:
        16-1-2020
    Version:
        1.0
    Modifier:
        Kelvin Sweere
    Used_IDE:
        Visual Studio Code (Python 3.6.7 64-bit)
    Schematic:
        -
    Version management:
        1.0:
            Headers aangepast
        
"""

import cv2 as cv
import numpy as np

def intersection(line1, line2):
    """Vindt de intersection tussen twee lijnen doormiddel van de Hesse normal form. 
    
    Args:
        line1: (tuple) x,y cordinaten van lijn 1. 
        line2: (tuple) x,y cordinaten van lijn 2.
    
    Returns:
        x,y: (tuple) tuple van de x & y snijpunten.
    """

    rho1, theta1 = line1
    rho2, theta2 = line2

    A = np.array([
        [np.cos(theta1), np.sin(theta1)],
        [np.cos(theta2), np.sin(theta2)]
    ])
    b = np.array([[rho1], [rho2]])
    x0, y0 = np.linalg.solve(A, b)
    x0, y0 = int(np.round(x0)), int(np.round(y0))
    return (x0, y0)


#teken rechte lijnen die voorkomen in de afbeelding.
def hough_line_transform(edges):
    """Voert het hough line transformatie algoritme uit.    
    
    Args:
        edges: (tuple) cordinaten die worden gebruikt voor cv.HoughLines transform.
    
    Returns:
        cpy: (np.array) getekende lijn op een zwart veld.
        cor: (tuple) rho & theta waarde van de lijn.
    """

    #maximale lengtes van de x,y cordianten.
    cdst = cv.cvtColor(edges, cv.COLOR_GRAY2BGR)
    #black frame
    cpy = np.zeros_like(cdst)

    #gevoeligheid van aantal lijnen.
    lines = cv.HoughLines(edges, 2, np.pi / 180, 150, None, 0, 0)
    cor = []

    #krijg cordinaten + plot image
    for line in lines:
        rho, theta = line[0]
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a * rho
        y0 = b * rho
        x1 = int(x0 + 1000 * (-b))
        y1 = int(y0 + 1000 * (a))
        x2 = int(x0 - 1000 * (-b))
        y2 = int(y0 - 1000 * (a))

        cv.line(cpy, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cor.append([(rho, theta)])
    return cpy, cor

def nothing(x):
    """Functienaam voor het aanmaken van de trackbar. De trackbar genereert een pointer
    die deze functie aanroept wanneer de slider van positie verandert.
    
    Args:
        x: (None) variablen die moet worden meegegeven van OpenCV.
    """
    pass
