# ![pageres](https://github.com/FoosTronics/Main_program/blob/master/Windows%2010/extra/promo.jpg)

# FoosTronics
> AI besturing van tafelvoetbal

FoosTronics is een NLE minor project waarbij de keeper van een fysieke voetbaltafel wordt bestuurd doormiddel van een AI. Hierbij is beeldherkenning gebruikt om de bal te detecteren. 

Jetson Nano is de main applicatie waarop de motoren, gyroscoop, etc. op kunnen worden aangesloten.

De Windows applicatie gaat over het testen van bijvoorbeeld AI en simulatie of voor test runnen.

# Motivatie
Het project is gekozen om meer inzicht te verkrijgen in: AI, beeldherkenning, mechanica en hardware. 

## Applicatie starten 

```python
activate py36

python main.py
```

## Packages
| Package       | Versie              | 
| ------------- | -------------       | 
| OpenCV (cv2)  | 4.1.1               |              
| TensorFlow    | 1.14.1-dev20190625  | 
| numpy         | 1.16.5              |               
| matplotlib    | 3.1.1               |                
| Box2D         | 2.3.2               |               
| smbus         |                     |               
| usb1          |                     |               
| imutils       | 0.5.3               |               
| numba         | 0.45.1              |               
| pygame        | 1.9.6               |               
