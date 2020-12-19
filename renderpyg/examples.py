'''
examples.py: A colletion of examples for renderpyg

You can call this script with the name of an example to launch it.
Each example is a single in this file listed in the following order.

sprite
tfont
tilemap
nine

This file is part of renderpyg

renderpyg is a python package providing higher level features for
pygame. It uses the pygame._sdl2.video API to provide hardware GPU
texture rendering.

renderpyg is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.
pytmx is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public
License along with renderpyg.

If not, see <http://www.gnu.org/licenses/>.
'''
import os, sys, random, math
import pygame as pg
from pygame._sdl2 import Window, Renderer, Texture, Image
from renderpyg import Sprite, TextureFont, keyrange
from random import randrange

# Set sdl2 for anisotropic filtering:
# (0 for no filtering, 1 for bilinear filtering, 2 for anisotropic)  

os.environ['SDL_RENDER_SCALE_QUALITY'] = '2'

EXAMPLE_DATA = os.path.join(os.path.dirname(__file__), 'data', '')
RENDER_RESOLUTION = (1600, 900)
WINDOW_RESOLUTION = (1600, 900)
SMALL_RESOLUTION = (800, 450)
FRAMES_PER_SECOND = 30
FONT = EXAMPLE_DATA+'font.ttf' 
FONT_SIZE = 72
SPRITE_COUNT = 30
FONT_PARAMS = dict(
	text='Dancing Font', x=10, y=10, color=(175,0,0), variance=30,
	circle=3, rotate=15, scale=.25, colors=(75,0,0))
EXAMPLES = ('sprites', )

def sprites():
	pg.init()
	clock = pg.time.Clock()
	window = Window("Renderpyg Example", size=WINDOW_RESOLUTION)
	renderer = Renderer(window, vsync=True)
	""" 
	We will draw into a buffer texture to allow easy resolution changes
	It will also make it easier to apply screen transitions and similar effects later

	When using pygame._sdl2.video you do not call pygame.display.setmode()
	Therefore calling surface.convert() or surface.convert_alpha() will throw an error
	When you create a Texture that needs alpha blending you must set its blend mode
	Alpha blending will be set automatically when loading from an image with transparency, such as PNG

	Remember to use the buffer size instead of the window size when drawing onto the offscreen buffer
	This will allow you to scale the screen to any window or fullscreen desktop size
	"""
	buffer = Texture(renderer, RENDER_RESOLUTION, target=True)
	buffer.blend_mode = 1 
	screensize = buffer.get_rect()
	""" 
	You can set fullscreen when creating the window by using Window(title, size, desktop_fullscreen=True)
	I prefer creating a window before going to fullscreen to avoid strange window placement that occurs
	if you exit fullscreen later on.
	"""
	FULLSCREEN = False
	if FULLSCREEN:
		window.set_fullscreen(True)
	"""
	Font features in pygame are design for blitting to a surface, not for GPU rendering
	It is possible to create a streaming texture and then using texture.update() to update the texture
	from a pygame surface, but accessing GPU memory is slow and this should be done sparingly.

	Therefore I created a simple TextureFont class. We will use the animation feature of this class
	for a little extra fun. We will also create some sprites and let them animate too.

	Also, for this example we use a Character class to move and rotate individual characters across
	the screen. This is very similar to how you will handle sprites later.
	"""
	tfont = TextureFont(renderer, FONT, FONT_SIZE)
	sprite = Sprite(
		(renderer, EXAMPLE_DATA+'aliens.png'), 7, 8, by_count=True)
	group = pg.sprite.Group()
	animations = [
		keyrange(0, 7, 200),
		keyrange(7, 14, 200),
		keyrange(14, 21, 200),
		keyrange(28, 35, 200)]

	for _ in range(SPRITE_COUNT):
		spr = Sprite(sprite.images)		
		spr.set_pos(
			randrange(0, RENDER_RESOLUTION[0]),
			randrange(0, RENDER_RESOLUTION[1]) )
		spr.set_animation(random.choice(animations), -1)
		spr.velocity = pg.Vector2(
			randrange(-10, 11),
			randrange(-10, 11))
		if randrange(10) < 2:
			spr.rotation = randrange(-10, 11)	
		group.add(spr)
	""" 
	Here starts a simple game loop
	Press SPACE to toggle between a large window, a small window, and fullscreen
	Press ENTER to add more characters to the screen

	At the beginning of each frame we must set the renderer target to our buffer Texture
	All the following draw calls will be drawn to the buffer instead of the screen
	After all of our drawing, we reset the target and draw the buffer onto the screen
	"""
	timer = pg.time.get_ticks()
	delta = 0
	running = True
	while running:
		renderer.target = buffer 
		for event in pg.event.get():
			if event.type == pg.QUIT:
				running = False
			elif event.type == pg.KEYDOWN:
				if event.key == pg.K_ESCAPE:
					running = False
				elif event.key == pg.K_SPACE:
					if FULLSCREEN:
						FULLSCREEN = False
						window.size = WINDOW_RESOLUTION
						window.set_windowed()
					elif window.size == WINDOW_RESOLUTION:
						window.size = SMALL_RESOLUTION
					else:
						FULLSCREEN = True
						window.size = WINDOW_RESOLUTION
						window.set_fullscreen(True)

		#Must set the draw color before clearing the scren or drawing lines and rectt

		renderer.draw_color = (0,0,0,255) 
		renderer.clear()
		"""
		Draw the background image if available. 
		By default Texture.draw() will fill the renderer unless you supply a destination Rect
		texture.draw( dstrect=Rect(x, y, width, height) )
		"""
		group.update(delta)
		group.draw()
		tfont.animate(**FONT_PARAMS)

		# Setting renderer.target = None will make following draw calls render to the underlying window
		# Since we don't provide a dstrect it will fill the renderer

		renderer.target = None
		buffer.draw()
		renderer.present() # all draw calls occur and the screen is updated here
		delta = clock.tick(FRAMES_PER_SECOND)

if __name__ == '__main__':
	if len(sys.argv) > 1:
		if sys.argv[1] in EXAMPLES:
			locals()[sys.argv[1]](*sys.argv[2:])
	else:
		print('AVAILABLE EXAMPLES')
		for name in EXAMPLES:
			print(name)
		print('\nTry python -m renderpyg.examples example name parameters')