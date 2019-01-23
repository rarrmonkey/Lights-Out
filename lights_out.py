# The MIT License (MIT)
#
# Copyright (c) 2019 Tristan Campion (rarrmonkey @ hotmail . com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
Author Notes
 I intend to add beeps and boops but I would have to rip large chunks of code
 from another source because I don't know of a CircuitPython library for this.
 CircuitPlayground code might work but would need reformatting for the 
 NeoTrellis M4 Express.

"""

import time
from random import randint
import board
import busio
import adafruit_adxl34x
import adafruit_trellism4
 
i2c = busio.I2C(board.ACCELEROMETER_SCL, board.ACCELEROMETER_SDA)
accelerometer = adafruit_adxl34x.ADXL345(i2c)
trellis = adafruit_trellism4.TrellisM4Express()
trellis.pixels.brightness = 0.2

HEIGHT, WIDTH = 4, 8
BLACK = 0x000000 # black
#						0.Red		 1.Orange	 2.Yellow	 3.Green		4.Cyan		5.Blue	 6.Purple		7.Pink
COLOURS = [0xFF0000, 0xFF4400, 0xFFFF00, 0x00FF00, 0x00FFFF, 0x0000FF, 0x8800FF, 0xFF4444]
SETTINGS = [[1, 4, COLOURS[3], True],							# easy difficulty
						[4, 4, COLOURS[2], True],							# medium difficulty
						[16, 1, COLOURS[0], True],						# hard difficulty
						None, None, None, None,
						[4, 4, COLOURS[6], False],						# single colour mode
						None, None, None, None, None, None, None, None,
						None, None, None, None, None, None, None, None,
						[1, len(COLOURS), COLOURS[7], True]]	# children under 5

design = [[False for y in range(HEIGHT)] for x in range(WIDTH)]
grid = [[False for y in range(HEIGHT)] for x in range(WIDTH)]

level = 0
difficulty = -1
current_press = set() # current_press is a record of buttons already pressed
pol = -1	# polarity is used in resetting current level based on tilt

pattern = []
def setPattern():	# Hard Coded pattern for 4x8, this is the rainbow animation
	global pattern
	n = 0
	for i in range(8):
		pattern.append([i, 0])
	pattern.append([7, 1])
	pattern.append([7, 2])
	for i in range(8):
		pattern.append([7-i, 3])
	pattern.append([0, 2])
	for i in range(7):
		pattern.append([i, 1])
	for i in range(6):
		pattern.append([6-i, 2])
setPattern()

def pickColour(colour, rainbow=True):
	if (not rainbow): return SETTINGS[difficulty][2]	# This code makes it single coloured
	return COLOURS[colour % len(COLOURS)]

def displayPattern():
	trellis.pixels.fill(BLACK)
	trellis.pixels.auto_write = False
	for n in range(32):	# Hard Coded to match setPattern()
		for i in range(n+1):
			x, y = pattern[i]
			trellis.pixels[x, y] = pickColour(n-i)
		trellis.pixels.show()
		time.sleep(0.1)
	time.sleep(0.5)
	trellis.pixels.auto_write = True

def setDifficulty():
	global SETTINGS, difficulty
	for i in range(len(SETTINGS)):
		y, x = divmod(i, WIDTH)
		s = y * WIDTH + x
		if (SETTINGS[s] != None):
			trellis.pixels[x, y] = SETTINGS[s][2]
	while difficulty < 0:
		pushed = set(trellis.pressed_keys)
		for button in pushed - current_press:
			x, y = button
			s = y * WIDTH + x
			if (s < len(SETTINGS)) and (SETTINGS[s] != None):
				difficulty = s

def difficultySettings():																	# number of moves for difficulty
	start, progress, _, _ = SETTINGS[difficulty]
	return level // progress + start

def showLevel():
	global level
	if level >= HEIGHT*WIDTH*len(COLOURS): return False			# level out of displayable range
	lit = level // len(COLOURS)
	trellis.pixels.fill(BLACK)															# clear display
	trellis.pixels[divmod(lit, HEIGHT)] = pickColour(level)	# display level
	time.sleep(0.5)																					# delay
	trellis.pixels.fill(BLACK)															# clear display

def newLevel():																						# new level design
	global design
	moves = difficultySettings()
	design = [[False for y in range(HEIGHT)] for x in range(WIDTH)]
	for i in range(moves):																	# for number of moves repeat
		x, y = randint(0, WIDTH-1), randint(0, HEIGHT-1)			# + select random design position
		design[x][y] = not design[x][y]												# + toggle design position
	print("Level #", level, ", moves = ", moves, sep="")
	print(*design, sep="\r\n")

def drawGrid():																						# apply the design to the grid
	global design, grid
	grid = [[False for y in range(HEIGHT)] for x in range(WIDTH)]
	for y in range(HEIGHT):
		for x in range(WIDTH):																# for each grid position
			if design[x][y]: pressed([x, y], test=False)				# + implement design

def showGrid():
	global grid, level
	trellis.pixels.fill(BLACK)															# clear display
	trellis.pixels.auto_write = False
	rainbow = SETTINGS[difficulty][3]
	for y in range(HEIGHT):
		for x in range(WIDTH):																# for each grid position
			if grid[x][y]:																			# + if designed to be lit
				trellis.pixels[x, y] = pickColour(level, rainbow)	# + + light up button
	trellis.pixels.show()
	trellis.pixels.auto_write = True

def toggle(button):
	x, y = button
	grid[x][y] = not grid[x][y]															# grid[x,y] equals not grid[x,y]

def isCleared():																					# test for win condition
	for y in range(HEIGHT):
		for x in range(WIDTH):																# for each button in grid
			if grid[x][y]: return False													# + if button isLit then return failure
	return True																							# return success

def winner():
	global level
#	NOT IMPLEMENTED																					# play tune
	displayPattern()																				# display pattern
	print("Winner")
	level += 1																							# increment level
	setupLevel()																						# levelSetup

def pressed(button, test=True):
	x, y = button
	toggle(button)																					# toggle button
	if y > 0:					toggle([x, y-1])											# toggle button above
	if y < HEIGHT-1:	toggle([x, y+1])											# toggle button below
	if x > 0:					toggle([x-1, y])											# toggle button left
	if x < WIDTH-1:		toggle([x+1, y])											# toggle button right
	if test: showGrid() # condition stops display flickering
	if test and isCleared(): winner()												# if isCleared then winner

def setupLevel():
	showLevel()																							# display level number
	newLevel()																							# generate a new random design
	drawGrid()																							# applies design to grid
	showGrid()																							# show grid on display

# Initilisation
setDifficulty()
displayPattern()
setupLevel()

while True:
	# Button Detection
	pushed = set(trellis.pressed_keys)
	for button in pushed - current_press:
		pressed(button)
	current_press = pushed

	# Accelaromitor Detection
	if (round(accelerometer.acceleration[2]) * pol) < -2:
		pol = -1 * pol
		showLevel()
		drawGrid()
		showGrid()

	# Rest the CPU & debounce
	time.sleep(0.1)
