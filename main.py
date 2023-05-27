import json
import math
import os
from random import randrange as rand
from time import time as t

import pygame

if os.getcwd() != os.path.dirname(os.path.realpath(__file__)):
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

GAMEDIR = 'assets\\FlappyBird\\'

TYPES = []

for folder in os.scandir(GAMEDIR):
    if folder.is_dir():
        TYPES.append(folder.name)

pygame.init()
pygame.mixer.init()

SOUNDS = {}

for n in ['fly', 'hit', 'point']:
    SOUNDS[n] = pygame.mixer.Sound(f'{GAMEDIR}{n}.mp3')
    SOUNDS[n].set_volume(0.5)


def playSound(s):
    pygame.mixer.Sound.play(s)


winWidth, winHeight = tuple(
    [i - 50 for i in pygame.display.get_desktop_sizes()[0]])

SCREEN = pygame.display.set_mode((winWidth, winHeight))
TIME = pygame.time.Clock()
ICON = pygame.image.load(GAMEDIR + 'icon.png').convert_alpha()

SCORE = 0

gameStart = False
gameEnd = False
endScreen = False
surface = pygame.Surface((winWidth, winHeight), pygame.SRCALPHA)

pygame.display.set_caption('FlappyBird')
pygame.display.set_icon(ICON)

GRAVITY = 0.384

BG = pygame.image.load(
    f'{GAMEDIR}Classic\\bg.png').convert_alpha()
BG = pygame.transform.scale(BG, (winWidth, winHeight))
FLOOR = pygame.image.load(
    f'{GAMEDIR}Classic\\floor.png').convert_alpha()
FLOOR = pygame.transform.scale(FLOOR, (winWidth, 0.125 * winHeight))
PLATE = pygame.image.load(f'{GAMEDIR}plate.png').convert_alpha()
PIPE = pygame.image.load(
    f'{GAMEDIR}Classic\\pipe_up.png').convert_alpha()

BIRDLIST = pygame.sprite.Group()
PIPELIST = pygame.sprite.Group()
FLOORLIST = pygame.sprite.Group()
BUTTONLIST = pygame.sprite.Group()
TEXTLIST = pygame.sprite.Group()
PLATELIST = pygame.sprite.Group()


class Velocity:
    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y


WORLDVELOCITY = Velocity(5, 0)

SCOREBOARD = 0


class Button(pygame.sprite.Sprite):
    def __init__(self, height, imPath, Funct, pos, addIndex=None, hasRoot=None) -> None:

        super().__init__()

        self.image = pygame.image.load(imPath)
        self.function = Funct

        self.rect = self.image.get_rect()
        self.image = pygame.transform.scale(
            self.image, (self.rect.width * (height / self.rect.height), height))
        self.rect = self.image.get_rect()

        self.rect.center = pos

        self.addIndex = addIndex
        self.index = 0
        self.hasRoot = hasRoot

        BUTTONLIST.add(self)

    def checkClicks(self, mouse):
        if self.rect.x <= mouse[0] <= self.rect.x + self.rect.width and \
                self.rect.y <= mouse[1] <= self.rect.y + self.rect.height:
            if self.hasRoot:
                self.function(self.addIndex)
            else:
                self.function()


class Text(pygame.sprite.Sprite):
    def __init__(self, fontPath, pos, base, scale) -> None:
        super().__init__()

        self.font = pygame.font.Font(fontPath, 100)
        self.image = self.font.render(base, True, (0, 0, 0))
        self.rect = self.image.get_rect()
        self.pos = pos

        self.scale = scale

        self.image = pygame.transform.scale(
            self.image, (self.rect.width * self.scale // 1.5, self.rect.height * self.scale // 1.5))
        self.rect = self.image.get_rect()
        self.rect.center = self.pos

        TEXTLIST.add(self)

    def updateText(self, val):
        self.image = self.font.render(val, True, (0, 0, 0))
        self.rect = self.image.get_rect()

        self.image = pygame.transform.scale(
            self.image, (self.rect.width * self.scale // 1.5, self.rect.height * self.scale // 1.5))

        self.rect = self.image.get_rect()
        self.rect.center = self.pos


class TextPlate(pygame.sprite.Sprite):
    def __init__(self, width, height, pos) -> None:
        super().__init__()

        self.width = width
        self.width //= height / PLATE.get_height()

        self.image = pygame.Surface(
            (self.width, PLATE.get_height()), pygame.SRCALPHA)
        self.image.blit(
            PLATE, (0, 0), (0, 0, PLATE.get_width() // 3, PLATE.get_height()))

        self.body = pygame.Surface((PLATE.get_width() // 3, PLATE.get_height()), pygame.SRCALPHA, 32)
        self.body.blit(PLATE, (0, 0), (PLATE.get_width() // 3, 0,
                                       PLATE.get_width() // 3, PLATE.get_height()))

        if self.width - 2 * PLATE.get_width() // 3 > 0:
            self.image.blit(pygame.transform.scale(
                self.body, (self.width - 2 * PLATE.get_width() // 3, PLATE.get_height())
            ), (PLATE.get_width() // 3, 0))
        self.image.blit(PLATE, (self.width - PLATE.get_width() // 3, 0),
                        (2 * PLATE.get_width() // 3, 0, PLATE.get_width() // 3, PLATE.get_height()))

        self.image = pygame.transform.scale(self.image, (width, height))
        self.rect = self.image.get_rect()
        self.rect.center = pos

        PLATELIST.add(self)


class ButtonSet:
    def __init__(self, scale, command, pos, width, rootList) -> None:

        self.command = command
        self.pos = pos
        self.width = width
        self.index = 0
        self.root = rootList

        self.text = Text(
            f'{GAMEDIR}FlappyBirdy.ttf', pos, rootList[0], scale)
        self.textPlate = TextPlate(self.width, self.text.rect.height + 60, self.pos)
        self.buttonRight = Button(self.textPlate.rect.height, f'{GAMEDIR}btnR.png', lambda val: self.command(
            self.updateIndex(val) or self.root[self.index]
        ) or self.text.updateText(self.root[self.index]),
                                  (self.pos[0] + self.width // 2 + self.textPlate.rect.height // 2, self.pos[1]), 1,
                                  True)
        self.buttonLeft = Button(self.textPlate.rect.height, f'{GAMEDIR}btnL.png', lambda val: self.command(
            self.updateIndex(val) or self.root[self.index]
        ) or self.text.updateText(
            self.root[self.index]
        ), (self.pos[0] - self.width // 2 - self.textPlate.rect.height // 2, self.pos[1]), -1, True)

    def updateIndex(self, change):
        self.index += change
        if self.index < 0:
            self.index = len(self.root) - 1
        elif self.index >= len(self.root):
            self.index = 0


class Bird(pygame.sprite.Sprite):
    def __init__(self, path, x_offset, jKey) -> None:

        super().__init__()

        self.spriteSheet = []

        with open(path + 'birdConfig.json', 'r') as file:
            f = json.load(file)
            self.frames = f['frames']
            self.frameSpeed = f['speed']

        tempImage = pygame.image.load(path + 'bird.png').convert_alpha()
        frameWidth = tempImage.get_width() // self.frames

        for f in range(self.frames):
            frame = pygame.Surface(
                (frameWidth, tempImage.get_height()), pygame.SRCALPHA)
            frame.blit(tempImage, (0, 0), (f * frameWidth, 0,
                                           frameWidth, tempImage.get_height()))
            self.spriteSheet.append(frame)

        self.frame = 0

        self.originalImage = self.spriteSheet[0]

        self.width = 0.05 * winWidth
        self.height = self.originalImage.get_height() * self.width / \
                      self.originalImage.get_width()

        self.originalImage = pygame.transform.scale(
            self.originalImage, (self.width, self.height))
        self.rect = self.originalImage.get_rect()

        self.rect.center = (winWidth // 2 + x_offset, winHeight // 2)
        self.rect.width *= 0.5
        self.rect.height *= 0.5

        self.buttonSet = ButtonSet(0.6, lambda x: self.changeSprite(
            x), (self.rect.center[0], self.rect.y + 100), 150, TYPES)

        self.vel = Velocity(WORLDVELOCITY.x, 0)
        self.rotation = 0
        self.image = self.originalImage

        self.jKey = jKey

        self.hit = False

        BIRDLIST.add(self)

    def update(self) -> None:
        if self.rect.y + self.rect.height < winHeight - FLOOR.get_height():

            self.frame += self.frameSpeed
            self.frame %= len(self.spriteSheet)

            self.originalImage = self.spriteSheet[math.floor(self.frame)]

            self.originalImage = pygame.transform.scale(
                self.originalImage, (self.width, self.height))

            self.vel.y += GRAVITY

            if self.rect.y >= winHeight // 2 and not gameStart and not self.hit:
                self.vel.y = -rand(6, 10)

            self.rect.y += self.vel.y
            self.rotation = 0.35 * math.degrees(math.atan(6 / 6)) if self.vel.y < 8 else self.rotation + (
                    (-90 - self.rotation) / (math.sqrt(2 * (winHeight - self.rect.x - FLOOR.get_height()) / GRAVITY)))
            self.image = pygame.transform.rotate(
                self.originalImage, self.rotation)
            self.rect = self.image.get_rect(center=self.rect.center)

            if not self.hit and (pygame.sprite.spritecollideany(self, PIPELIST) or pygame.sprite.spritecollideany(self,
                                                                                                                  FLOORLIST) or self.rect.y <= 0):
                self.hit = True
                playSound(SOUNDS['hit'])
                self.vel.y = 0
                WORLDVELOCITY.x = 0
                SCOREBOARD.kill()
                BUTTONLIST.empty()

    def changeSprite(self, root):

        self.spriteSheet = []

        with open(f'{GAMEDIR}{root}\\' + 'birdConfig.json', 'r') as file:
            f = json.load(file)
            self.frames = f['frames']
            self.frameSpeed = f['speed']

        temp_image = pygame.image.load(
            f'{GAMEDIR}{root}\\' + 'bird.png').convert_alpha()
        frame_width = temp_image.get_width() // self.frames

        for f in range(self.frames):
            frame = pygame.Surface(
                (frame_width, temp_image.get_height()), pygame.SRCALPHA)
            frame.blit(temp_image, (0, 0), (f * frame_width, 0,
                                            frame_width, temp_image.get_height()))
            self.spriteSheet.append(frame)

    def bounce(self) -> None:
        if not self.hit:
            playSound(SOUNDS['fly'])
            self.vel.y = -8


class Pipe(pygame.sprite.Sprite):
    def __init__(self, file, posy, type, height=None, posx=winWidth, immovable=False):
        super().__init__()
        self.type = type

        self.image = pygame.image.load(
            f'{GAMEDIR}{file}\\{type}.png').convert_alpha()

        self.width = 0.07 * winWidth
        self.height = height if height else \
            self.image.get_height() * self.width / self.image.get_width()

        self.image = pygame.transform.scale(
            self.image, (self.width, self.height))

        self.rect = self.image.get_rect()
        self.rect.x = posx
        self.rect.y = posy
        self.rect.height *= 0.95
        self.rect.width *= 0.7

        self.immovable = immovable

        self.passed = False

        PIPELIST.add(self)

    def update(self):
        global SCORE, WORLDVELOCITY

        if not self.immovable:
            self.rect.x -= WORLDVELOCITY.x
            if self.rect.x + self.width <= 0:
                removePipes.append(self)

            for b in BIRDLIST:
                if not self.passed and self.rect.x + self.width < b.rect.x and self.type == 'pipe_up':
                    self.passed = True
                    playSound(SOUNDS['point'])
                    global SCOREBOARD
                    SCORE += 1
                    SCOREBOARD.updateText(str(SCORE))

                    WORLDVELOCITY.x += 1 if not SCORE % 50 and WORLDVELOCITY.x < 8 else 0
                    break

    def changeSprite(self, file):
        global PIPE

        self.image = pygame.image.load(
            f'{GAMEDIR}{file}\\{self.type}.png').convert_alpha()
        PIPE = self.image
        self.image = pygame.transform.scale(
            self.image, (self.width, self.height))


class Floor(pygame.sprite.Sprite):
    def __init__(self, check, pos: int = False):
        super().__init__()

        self.image = FLOOR
        self.check = check

        self.rect = self.image.get_rect()
        self.rect.x = pos if pos else winWidth
        self.rect.y = winHeight - self.rect.height

        FLOORLIST.add(self)

    def update(self):
        self.rect.x -= WORLDVELOCITY.x
        if self.rect.x + self.rect.width - WORLDVELOCITY.x <= 0:
            removeFloors.append(self)
        if self.rect.x + self.rect.width - WORLDVELOCITY.x <= winWidth and self.check:
            spawnFloor()
            self.check = False


Bird(f'{GAMEDIR}Classic\\', 0, pygame.K_SPACE)


def changeBG(root):
    global BG

    BG = pygame.image.load(
        f'{GAMEDIR}{root}\\bg.png').convert_alpha()
    BG = pygame.transform.scale(BG, (winWidth, winHeight))


def changeFloor(root):
    global FLOOR

    FLOOR = pygame.image.load(
        f'{GAMEDIR}{root}\\floor.png').convert_alpha()
    FLOOR = pygame.transform.scale(FLOOR, (winWidth, 0.125 * winHeight))

    for f in FLOORLIST:
        f.image = FLOOR


ButtonSet(1, lambda x: changeBG(x), (winWidth // 2, 200), 400, TYPES)
ButtonSet(0.7, lambda x: changeFloor(x),
          (winWidth // 2, winHeight - 50), 140, TYPES)

pipeRoot = 'Classic'


def changePipes(root):
    global pipeRoot
    pipeRoot = root
    for p in PIPELIST:
        p.changeSprite(root)


ButtonSet(0.5, lambda x: changePipes(x), (winWidth - 300,
                                          winHeight - FLOOR.get_height() - 50), 150, TYPES)
Pipe('Classic', winHeight - FLOOR.get_height() - 200,
     'pipe_down', posx=winWidth - 300, immovable=True)


def createPipe(y):
    pipe_height = PIPE.get_height() * (0.07 * winWidth) / PIPE.get_width()
    pipe_opening = rand(150, 300)
    Pipe(pipeRoot, 0, 'pipe', height=(y - pipe_height if y - pipe_height > 0 else 10)),
    Pipe(pipeRoot, y - pipe_height, 'pipe_up'),
    Pipe(pipeRoot, y + pipe_opening, 'pipe_down'),
    Pipe(pipeRoot, y + pipe_opening + pipe_height, 'pipe', height=(winHeight - (y + pipe_opening + pipe_height +
                                                                                FLOOR.get_rect().height) if winHeight - (
            y + pipe_opening + pipe_height + FLOOR.get_rect().height) > 0 else 10))


def spawnFloor(pos: int = False, check=True):
    Floor(check, pos)


spawnFloor(1, False)
spawnFloor(winWidth)

availableKeys = set()

pipeTime = 0

while not gameEnd:

    # Endgame
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            gameEnd = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            for b in BUTTONLIST:
                b.checkClicks(pygame.mouse.get_pos())

    # Drawing
    SCREEN.blit(BG, (0, 0))

    if WORLDVELOCITY.x * (t() - pipeTime) > 10 and gameStart:
        pipeTime = t()
        createPipe(rand(10, winHeight - 210 - FLOOR.get_rect().height))

    keys = pygame.key.get_pressed()
    for b in BIRDLIST:
        if keys[b.jKey]:
            if not gameStart and not endScreen:
                gameStart = True
                BUTTONLIST.empty()
                TEXTLIST.empty()
                PLATELIST.empty()
                PIPELIST.empty()

                SCOREBOARD = Text(
                    f'{GAMEDIR}Patrick.ttf', (winWidth // 2, 150), str(SCORE), 0.5)

                Button(SCOREBOARD.rect.height + 30, f'{GAMEDIR}score.png', lambda: True,
                       SCOREBOARD.rect.center)

            if b.jKey not in availableKeys:
                b.bounce() if not b.hit else False
                availableKeys.add(b.jKey)
        else:
            availableKeys.remove(b.jKey) if b.jKey in availableKeys else False

        b.update()


    def endGame():
        global gameEnd
        gameEnd = True


    if len([b for b in BIRDLIST if not b.hit]) == 0:
        if not endScreen:
            gameOverText = Text(f'{GAMEDIR}FlappyBirdy.ttf',
                                (winWidth // 2, winHeight // 2), 'Game Over', 2)
            TextPlate(gameOverText.rect.width + 60, gameOverText.rect.height + 60, gameOverText.rect.center)
            scoreText = Text(f'{GAMEDIR}Patrick.ttf',
                             (winWidth // 2, winHeight // 2 + 100), f'SCORE: {SCORE}', 0.6)
            TextPlate(scoreText.rect.width + 30, scoreText.rect.height + 30, scoreText.rect.center)
            Button(100, f'{GAMEDIR}close.png',
                   lambda: endGame(), (winWidth // 2, winHeight // 2 + 200))
            endScreen = True
            gameStart = False

    removePipes = []
    removeFloors = []

    for p in PIPELIST:
        p.update()

    for f in FLOORLIST:
        f.update()

    for i in range(len(removePipes)):
        removePipes.pop().kill()

    for i in range(len(removeFloors)):
        removeFloors.pop().kill()

    PIPELIST.draw(SCREEN)
    FLOORLIST.draw(SCREEN)
    BIRDLIST.draw(SCREEN)
    BUTTONLIST.draw(SCREEN)
    PLATELIST.draw(SCREEN)
    TEXTLIST.draw(SCREEN)

    pygame.display.flip()

    TIME.tick(60)
