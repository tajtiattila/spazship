#!/usr/bin/python
# vim: encoding=utf-8
from __future__ import print_function, division, unicode_literals

import pyglet, math, random
from pyglet.window import key, mouse
from pyglet.gl import *

FORGAS = 180 # fok/másodperc
GYORSULAS = 100 # pixel/másodperc
FUSTSEB = 30
GRAVITACIO = 30
FPS = 60
SCALE = 1/16

config = pyglet.gl.Config(sample_buffers=1, samples=4)
#ablak = pyglet.window.Window(config=config, resizable=True) 
ablak = pyglet.window.Window()

jatekosKep = pyglet.image.load('spaceship.png')
fustkepek = [pyglet.image.load('fust{0}.png'.format(n)) for n in [1,2]]

# anchor_x és _y egésznek kell legyen, ezért a // operátor
ax = jatekosKep.width // 2
ay = (jatekosKep.height * 6) // 16
for fustkep in fustkepek:
    fustkep.anchor_x, fustkep.anchor_y = ax, ay
jatekosKep.anchor_x, jatekosKep.anchor_y = ax, ay

#

class vec(object):
    def __init__(self,*args):
        self.v = tuple(args)
    def __add__(self,other):
        assert type(other) == vec
        return vec(*[a+b for a,b in zip(self.v, other.v)])
    def __sub__(self,other):
        assert type(other) == vec
        return vec(*[a-b for a,b in zip(self.v, other.v)])
    def __mul__(self,other):
        return vec(*[a*other for a in self.v])
    def __div__(self,other):
        return vec(*[a/other for a in self.v])
    def __getitem__(self, n):
        return self.v[n]
    def __repr__(self):
        return "vec(" + ",".join([repr(x) for x in self.v]) + ")"
def hossz(vec):
    return math.sqrt(sum((a*a for a in vec.v)))
def irany(d):
    return vec(math.sin(d), math.cos(d))

#

class Jatekos:
    pos = vec(50,50) # pozíció
    seb = vec(0,10) # sebesség pixel/másodperc
    forg = 0 # felfele
    jobbraForog = balraForog = hajtomu = False

    def __init__(self, kep, vilag):
        self.sprite = pyglet.sprite.Sprite(kep)
        self.sprite.scale = SCALE
        self.vilag = vilag
    def rajzol(self):
        self.sprite.draw()
    def mozog(self, dt):
        if self.jobbraForog:
            self.forg += FORGAS*dt
        elif self.balraForog:
            self.forg -= FORGAS*dt
        if self.hajtomu:
            iranyvec = irany(math.radians(self.forg))
            self.seb += iranyvec*GYORSULAS*dt
            self.vilag += [Fust(self, fustkepek)]
        self.seb -= vec(0,GRAVITACIO*dt)
        self.pos += self.seb*dt
        self.sprite.x = self.pos[0]
        self.sprite.y = self.pos[1]
        self.sprite.rotation = self.forg
    def halott(self):
        return False

class Fust:
    def __init__(self, j, kepek):
        self.pos = j.pos
        iranyvec = irany(math.radians(jatekos.forg))
        rndvec = irany(math.radians(random.uniform(0,360))) * random.uniform(0, FUSTSEB/4)
        self.seb = j.seb - iranyvec*FUSTSEB + rndvec
        self.sprite = pyglet.sprite.Sprite(random.choice(kepek))
        self.sprite.scale = SCALE
        self.sprite.rotation = j.forg
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

vilag = []
jatekos = Jatekos(jatekosKep, vilag)
vilag += [jatekos]

@ablak.event
def on_draw():
    global fust
    ablak.clear()
    for valami in vilag:
        valami.rajzol()

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
    for valami in vilag[:]:
        valami.mozog(dt)
        if valami.halott():
            vilag.remove(valami)

pyglet.clock.schedule_interval(frissit, 1/FPS)
pyglet.app.run()

