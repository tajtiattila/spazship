#!/usr/bin/python
# vim: encoding=utf-8
from __future__ import print_function, division, unicode_literals

import pyglet, math, random
from pyglet.window import key, mouse
from pyglet.gl import *

import sys

import pymunk as pm

pm.init_pymunk()
vec = pm.Vec2d

FORGAS = math.radians(180) # fok/másodperc
GYORSULAS = 100 # pixel/másodperc
TOMEG = 10000 # kg
FORGAS_ERO = 20*TOMEG
GRAVITACIO = 9.81
TOLOERU_SULY_ARANY = 5
FUSTSEB = 30
GRAVITACIO = 30
FPS = 60
SCALE = 1/16
W,H,BORDER = 640,480,10
COLL_LIMIT = 10000

COLL_STATIC = 1
COLL_PLAYER = 2

config = pyglet.gl.Config(sample_buffers=1, samples=4)
#ablak = pyglet.window.Window(config=config, resizable=True) 
ablak = pyglet.window.Window(W,H)

jatekosKep = pyglet.image.load('img/spaceship.png')
thrustKep = pyglet.image.load('img/flame.png')
thrustSound = pyglet.media.load('img/thrust.mp3', streaming=False)
fustkepek = [pyglet.image.load('img/fust{0}.png'.format(n)) for n in [1,2]]

jatekosShapeSpecs = [
    [vec(9,0),vec(1,-4),vec(-3,-4),vec(-3,4),vec(1,4)],
    [vec(1,-4),vec(0,-6),vec(-3,-4),vec(-3,4),vec(0,6),vec(1,4)]
]

# anchor_x és _y egésznek kell legyen, ezért a // operátor
ax = jatekosKep.width // 2
ay = (jatekosKep.height * 6) // 16
for fustkep in fustkepek:
    fustkep.anchor_x, fustkep.anchor_y = ax, ay
jatekosKep.anchor_x, jatekosKep.anchor_y = ax, ay
thrustKep.anchor_x, thrustKep.anchor_y = thrustKep.width // 2, thrustKep.height

#

def hossz(vec):
    return math.sqrt(sum((a*a for a in vec)))
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
        self.doDrawSpace = 'drawspace' in sys.argv[1:]
    def add_line(self,p1,p2):
        body = pm.Body(pm.inf, pm.inf)
        shape = pm.Segment(body, p1, p2, 1.0)
        shape.friction = 0.99
        shape.collision_type = COLL_STATIC
        self.space.add_static(shape)
        self.coords += [p1.x, p1.y, p2.x, p2.y]
        self.vlist = pyglet.graphics.vertex_list(len(self.coords)//2, ('v2f', self.coords))
    def add(self, item):
        self.elements.add(item)
    def rajzol(self):
        if self.doDrawSpace:
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



def clamp(v, minv, maxv):
    return minv if v < minv else maxv if maxv < v else v
def clampabs(v, absv):
    return clamp(v, -absv, absv)
def normal(v):
    return vec(v[1], -v[0])

class Jatekos:
    POS = vec(50,50) # pozíció
    SEB = vec(0,10) # sebesség pixel/másodperc
    FORG = math.radians(90) # felfele
    jobbraForog = balraForog = hajtomu = False

    def __init__(self, kep, vilag):
        self.pos, self.seb, self.forg = self.POS, self.SEB, self.FORG
        self.sprite = pyglet.sprite.Sprite(kep)
        self.body = pm.Body(TOMEG,TOMEG)
        def mkshap(spec):
            shape = pm.Poly(self.body, [v*2 for v in spec])
            shape.friction = 0.5
            shape.elasticity = 0.5
            shape.collision_type = COLL_PLAYER
            return shape
        shapes = [mkshap(spec) for spec in jatekosShapeSpecs]
        self.rotbody = pm.Body(pm.inf,pm.inf)
        self.body.position = self.pos
        self.body.velocity = self.seb
        self.body.angle = self.forg
        self.rotbody.angle = self.forg
        self.sprite.scale = SCALE
        self.vilag = vilag
        self.vilag.space.add(self.body, *shapes)
        self.soundplayer = pyglet.media.Player()
        self.soundplayer.pause()
        self.soundplayer.queue(thrustSound)
        self.soundplayer.eos_action = pyglet.media.Player.EOS_LOOP
        self.vilag.space.add(self.rotbody)
        self.rotjoint = pm.SimpleMotor(self.body, self.rotbody, 0)
        self.vilag.space.add(self.rotjoint)
        self.rotjoint.max_force = FORGAS_ERO
        self.rotation_rate = 1.0
        self.vilag.space.add_collision_handler(COLL_PLAYER, COLL_STATIC, None, None, self.utkoz, None)
    def reset(self):
        self.pos, self.seb, self.forg = self.POS, self.SEB, self.FORG
        self.body.position = self.pos
        self.body.velocity = self.seb
        self.body.angle = self.forg
    def rajzol(self):
        self.sprite.draw()
    def mozog(self, dt):
        self.rotation_rate += dt
        self.rotjoint.max_force = clamp(self.rotation_rate, 0, 1) * FORGAS_ERO
        if self.jobbraForog:
            self.rotbody.angular_velocity = -FORGAS
        elif self.balraForog:
            self.rotbody.angular_velocity = FORGAS
        else:
            self.rotbody.angular_velocity = 0
        if self.hajtomu:
            f = self.body.rotation_vector
            self.body.apply_impulse(f*TOLOERU_SULY_ARANY*GRAVITACIO*TOMEG*dt)
            #self.vilag.add(Fust(self, fustkepek))
            self.soundplayer.play()
        else:
            self.soundplayer.pause()
        self.pos, self.forg = self.body.position, forg_pymunk_to_pyglet(self.body.angle)
        self.sprite.x, self.sprite.y = self.pos
        self.sprite.rotation = self.forg
    def halott(self):
        return False
    def utkoz(self, space, arbiter):
        imp = pm._chipmunk.cpArbiterTotalImpulse(arbiter._arbiter)
        if hossz(imp) > COLL_LIMIT:
            self.rotation_rate = -0.5
            print(imp)

class Thruster:
    def __init__(self, player, offset):
        self.player = player
        self.offset = offset
        self.sprite = pyglet.sprite.Sprite(thrustKep)
        self.sprite.scale = SCALE
        self.mozog(0)
    def rajzol(self):
        if self.player.hajtomu:
            self.sprite.x, self.sprite.y = self.pos
            self.sprite.draw()
    def mozog(self, dt):
        vx = self.player.body.rotation_vector
        vy = normal(vx)
        self.pos = self.player.pos + vx*self.offset.x + vy*self.offset.y
        self.forg = self.player.forg + random.randrange(-10,10)
        self.sprite.x, self.sprite.y = self.pos
        self.sprite.rotation = self.forg
        self.sprite.opacity = random.randint(128,255)
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
vilag.add(Thruster(jatekos, vec(-6,5)))
vilag.add(Thruster(jatekos, vec(-6,-5)))

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
    elif symbol == key.ENTER:
        jatekos.reset()

def frissit(dt):
    global vilag
    vilag.mozog(dt)

pyglet.clock.schedule_interval(frissit, 1/FPS)
pyglet.app.run()

