#!/usr/bin/python
# vim: encoding=utf-8
from __future__ import print_function, division, unicode_literals

import pyglet, math, random
from pyglet.window import key, mouse
from pyglet.gl import *

import pymunk as pm

pm.init_pymunk()
vec = pm.Vec2d

FORGAS = math.radians(180) # fok/másodperc
GYORSULAS = 100 # pixel/másodperc
TOMEG = 10000 # kg
GRAVITACIO = 9.81
TOLOERU_SULY_ARANY = 5
FUSTSEB = 30
GRAVITACIO = 30
FPS = 60
SCALE = 1/16
W,H,BORDER = 640,480,10

config = pyglet.gl.Config(sample_buffers=1, samples=4)
#ablak = pyglet.window.Window(config=config, resizable=True) 
ablak = pyglet.window.Window(W,H)

jatekosKep = pyglet.image.load('img/spaceship.png')
fustkepek = [pyglet.image.load('img/fust{0}.png'.format(n)) for n in [1,2]]

jatekosShapeSpecs = [
    [vec(9,0),vec(1,-4),vec(1,4)],
    [vec(1,-4),vec(0,-6),vec(-3,-4),vec(-3,4),vec(0,6),vec(1,4)]
]

# anchor_x és _y egésznek kell legyen, ezért a // operátor
ax = jatekosKep.width // 2
ay = (jatekosKep.height * 6) // 16
for fustkep in fustkepek:
    fustkep.anchor_x, fustkep.anchor_y = ax, ay
jatekosKep.anchor_x, jatekosKep.anchor_y = ax, ay

#

def hossz(vec):
    return math.sqrt(sum((a*a for a in vec.v)))
def iranyszog(v):
    return math.degrees(math.atan2(v.y,v.x))
def irany(d):
    return vec(math.sin(d), math.cos(d))
def forg_pymunk_to_pyglet(rotation):
    "Kiszámítja a pyglet-nek megadandó forgási szöget pymunk rendszerből"
    return 90-math.degrees(rotation)

#

class Vilag:
    def __init__(self):
        self.elements = set()
        self.coords = []
        self.space = pm.Space()
        self.space.gravity = vec(0,-GRAVITACIO)
        self.add_line(vec(BORDER,BORDER),vec(W-BORDER,BORDER))
        self.add_line(vec(BORDER,BORDER),vec(BORDER,H-BORDER))
        self.add_line(vec(W-BORDER,BORDER),vec(W-BORDER,H-BORDER))
        self.add_line(vec(BORDER,H-BORDER),vec(W-BORDER,H-BORDER))
        px, py = W/2,H/2
        self.add_line(vec(px-100,py+20),vec(px-50,py))
        self.add_line(vec(px-50,py),vec(px+50,py))
        self.add_line(vec(px+50,py),vec(px+100,py+20))
        self.drawSpaceMap = {}
    def add_line(self,p1,p2):
        body = pm.Body(pm.inf, pm.inf)
        shape = pm.Segment(body, p1, p2, 2.0)
        shape.friction = 0.5
        self.space.add_static(shape)
        self.coords += [p1.x, p1.y, p2.x, p2.y]
        self.vlist = pyglet.graphics.vertex_list(len(self.coords)//2, ('v2f', self.coords))
    def add(self, item):
        self.elements.add(item)
    def rajzol(self):
        self.drawSpace()
        self.vlist.draw(GL_LINES)
        for valami in self.elements:
            valami.rajzol()
    def mozog(self, dt):
        self.space.step(dt)
        for valami in list(self.elements):
            valami.mozog(dt)
            if valami.halott():
                self.elements.remove(valami)
    def drawSpace(self):
        for shape in self.space.shapes:
            if type(shape) == pm.Poly:
                self.drawPoly(shape)
    def drawPoly(self,poly):
        if id(poly) not in self.drawSpaceMap:
            vf = reduce(lambda x,y: x+y, ([float(v.x),float(v.y)] for v in poly.verts), [])
            self.drawSpaceMap[id(poly)] = pyglet.graphics.vertex_list(len(vf)//2, ('v2f', vf))
        glPushMatrix()
        glTranslatef(poly.body.position.x, poly.body.position.y, 0)
        glRotatef(math.degrees(poly.body.angle), 0,0,1)
        vl = self.drawSpaceMap[id(poly)]
        vl.draw(GL_LINE_LOOP)
        glPopMatrix()



class Jatekos:
    pos = vec(50,50) # pozíció
    seb = vec(0,10) # sebesség pixel/másodperc
    forg = math.radians(90) # felfele
    jobbraForog = balraForog = hajtomu = False

    def __init__(self, kep, vilag):
        self.sprite = pyglet.sprite.Sprite(kep)
        self.body = pm.Body(TOMEG,TOMEG)
        def mkshap(spec):
            shape = pm.Poly(self.body, [v*2 for v in spec])
            shape.friction = 0.5
            shape.elasticity = 0.5
            return shape
        shapes = [mkshap(spec) for spec in jatekosShapeSpecs]
        self.body.position = self.pos
        self.body.velocity = self.seb
        self.body.angle = self.forg
        self.sprite.scale = SCALE
        self.vilag = vilag
        self.vilag.space.add(self.body, *shapes)
    def rajzol(self):
        self.sprite.draw()
    def mozog(self, dt):
        if self.jobbraForog:
            self.body.angle -= FORGAS*dt
        elif self.balraForog:
            self.body.angle += FORGAS*dt
        if self.hajtomu:
            f = self.body.rotation_vector
            self.body.apply_impulse(f*TOLOERU_SULY_ARANY*GRAVITACIO*TOMEG*dt)
            self.vilag.add(Fust(self, fustkepek))
        self.sprite.x = self.body.position[0]
        self.sprite.y = self.body.position[1]
        self.sprite.rotation = forg_pymunk_to_pyglet(self.body.angle)
    def halott(self):
        return False

class Fust:
    def __init__(self, j, kepek):
        self.pos = vec(j.body.position)
        iranyvec = j.body.rotation_vector
        rndvec = irany(math.radians(random.uniform(0,360))) * random.uniform(0, FUSTSEB/4)
        self.seb = j.body.velocity - iranyvec*FUSTSEB + rndvec
        self.sprite = pyglet.sprite.Sprite(random.choice(kepek))
        self.sprite.scale = SCALE
        self.sprite.rotation = j.sprite.rotation
        self.sprite.x = self.pos[0]
        self.sprite.y = self.pos[1]
        self.ido = self.teljesido = random.uniform(.2,1)
    def mozog(self, dt):
        self.pos += self.seb*dt
        self.sprite.x = self.pos[0]
        self.sprite.y = self.pos[1]
        self.ido -= dt
        self.sprite.opacity = int(255*max(0,self.ido/self.teljesido))
        if self.ido < 0:
            self.sprite.delete()
    def halott(self):
        return self.ido < 0
    def rajzol(self):
        self.sprite.draw()

vilag = Vilag()
jatekos = Jatekos(jatekosKep, vilag)
vilag.add(jatekos)

@ablak.event
def on_draw():
    global vilag
    ablak.clear()
    vilag.rajzol()

@ablak.event
def on_key_press(symbol, modifiers):
    global jatekos
    if symbol == key.RIGHT:
        jatekos.jobbraForog = True
        jatekos.balraForog = False
    elif symbol == key.LEFT:
        jatekos.balraForog = True
        jatekos.jobbraForog = False
    elif symbol == key.UP:
        jatekos.hajtomu = True
        jatekos.fek = False
    elif symbol == key.DOWN:
        jatekos.fek = True
        jatekos.hajtomu = False

@ablak.event
def on_key_release(symbol, modifiers):
    global jatekos
    if symbol == key.RIGHT:
        jatekos.jobbraForog = False
    elif symbol == key.LEFT:
        jatekos.balraForog = False
    elif symbol == key.UP:
        jatekos.hajtomu = False
    elif symbol == key.DOWN:
        jatekos.fek = False

def frissit(dt):
    global vilag
    vilag.mozog(dt)

pyglet.clock.schedule_interval(frissit, 1/FPS)
pyglet.app.run()

