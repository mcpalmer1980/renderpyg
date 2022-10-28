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
import renderpyg as pyg
from renderpyg import Sprite, TextureFont, keyrange, load_texture
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
FONT_SIZE = 64
SPRITE_COUNT = 64
FONT_PARAMS = dict(
	text='Dancing Font', x=10, y=10, color=(175,0,0), variance=30,
	circle=3, rotate=15, scale=.25, colors=(75,0,0))
EXAMPLES = dict(
	sprites='animates alien sprites',
	tilemap='scroll and zoom a garden',
	tfont='select animated fonts from a list',
	nine='scale nine patch images',
	packed='animate frames from given TexturePacker xml',
	menu='interact with a few example menus')

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
	sprite = Sprite((renderer, EXAMPLE_DATA+'texture.xml'))
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
			randrange(-20, 20),
			randrange(-20, 20))
		if randrange(10) < 2:
			spr.scaling = 1.0001
		
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


def tilemap():
	from .tilemap import load_tilemap_string, load_tileset, render_tilemap, tile_background, Tilemap, scale_tilemap
	pg.init()
	window = Window('Testing', (1600,900))
	renderer = Renderer(window)
	clock = pg.time.Clock()
	tfont = TextureFont(renderer, None, 48)
	"""
	We could load the tilemap and its images by loading the included
	tmx file, but we'll load the tilemap from the map_data string and
	the images from tile.png with load_tileset().

	A pygame.Vector2 is used for the camera
	"""
	#tilemap = load_tmx(renderer, path+'tilemap.tmx')
	loaded_map = load_tilemap_string(map_data)
	loaded_cells = load_tileset(renderer, EXAMPLE_DATA+'tiles.png', 64,64)
	tilemap = Tilemap(loaded_map, loaded_cells)
	#tilemap.update_tilemap(loaded_map, 0)
	#tilemap.add_layer(loaded_map)
	background = load_texture(renderer, EXAMPLE_DATA+'grass.png')
	camera = pg.Vector3(800,450,1)
	scale = 1

	texture = load_texture(renderer, EXAMPLE_DATA+'aliens.png')
	group = pg.sprite.Group()
	for _ in range(10):
		spr = Sprite(texture, 7, 8, by_count=True)
		spr.set_pos(
			random.randint(0, tilemap.width * tilemap.tilewidth),
			random.randint(0, tilemap.height * tilemap.tileheight))
		spr.set_transform(camera)
		group.add(spr)

	delta = 0
	running = True
	while running:
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

			elif event.type == pg.MOUSEMOTION:
				x, y = pg.mouse.get_rel()
				if pg.mouse.get_pressed()[0]:
					camera.x -= x*2
					camera.y -= y*2
			elif event.type == pg.MOUSEBUTTONUP:
				if event.button == 4:
					scale += 0.01
				elif event.button == 5:
					scale -= 0.01

		camera[2] = scale
		
		scale_tilemap(tilemap, camera, scale, center=False, clamp=True, background=background)
		#group.update(delta)
		#group.draw()
		tfont.draw('Click and drag to scroll, wheel to zoom', 10, 10)
		tfont.draw('Camera {} Scale: {:.1f}%'.format(camera, scale*100), 10, 60)
		renderer.present()
		renderer.draw_color = (0,0,0,255)
		renderer.clear()
		delta = clock.tick(FRAMES_PER_SECOND)

def tfont():
	from .tfont import NinePatch
	examples = {
			'Radiantly Red': dict(color=(220,0,0), colors=(-100,0,0),
					circle=3, zoom=5, duration=5000, rotate=25, variance=10),
			'Blistering Blue': dict(color=(0,0,255), move=(8,0), fade=200,
					spread=25, duration=200),
			'Vividly Violet': dict(color=(238,130,238), colors=(-30,-30,-30),
					move=(10,10), rotate=5, zoom=5, duration=3000),
			'Garishly Green': dict(color=(0,100,0), colors=(0,-50,0), zoom=20,
					duration=5000, variance=33),
			'Whispy White': dict(color=(255,255,255), fade=100, circle=10,
					variance=5, duration=9000)
			}
	example_list = list(examples.keys())
	default = dict(color=(255,255,0), move=(5,2), rotate=4, duration=3000)

	pg.init()
	clock = pg.time.Clock()
	window = Window("TextureFont Test", size=SMALL_RESOLUTION)
	renderer = Renderer(window, vsync=True)
	font = EXAMPLE_DATA+'font.ttf'
	tfont = TextureFont(renderer, font, FONT_SIZE)

	selected = 0
	running = True
	while running:
		for event in pg.event.get():
			if event.type == pg.QUIT:
				running = False
			elif event.type == pg.KEYDOWN:
				if event.key == pg.K_UP:
					selected -= 1
					if selected < 0:
						selected = len(examples) - 1
				elif event.key == pg.K_DOWN:
					selected += 1
					if selected >= len(examples):
						selected = 0
				else:
					running = False

		renderer.draw_color = (0,0,0,255) 
		renderer.clear()

		x = SMALL_RESOLUTION[0] // 2
		y = 20
		for i, item in enumerate(example_list):
			if i==selected:
				tfont.animate(
					item, x, y, align='center', **examples[item])
			else:
				tfont.animate(item, x, y, align='center', **default)
			y += tfont.height * 1.2

		renderer.present()
		clock.tick(30)

def nine():
	from .tfont import NinePatch
	pg.init()
	clock = pg.time.Clock()
	window = Window("NinePatch Test", size=RENDER_RESOLUTION)
	renderer = Renderer(window, vsync=True)
	screen_size = renderer.get_viewport()

	tfont = TextureFont(renderer, EXAMPLE_DATA+'font.ttf', 64)
	texture = load_texture(renderer, EXAMPLE_DATA+'nine.png')
	patches = (
		NinePatch(texture, (20, 20, 20, 20), (0, 0, 320, 167)),
		NinePatch(texture, (52,52,52,52), (0, 168, 320, 173)),
		NinePatch(texture, (32, 32, 32, 32), (0, 345, 320, 223)),
		NinePatch(texture, (32, 32, 32, 32), (0, 572, 320, 160)))

	selected = 0
	running = True
	while running:
		for event in pg.event.get():
			if event.type == pg.QUIT:
				running = False
			elif event.type == pg.KEYDOWN:
				if event.key == pg.K_UP:
					selected -= 1
					if selected < 0:
						selected = len(patches) - 1
				elif event.key == pg.K_DOWN:
					selected += 1
					if selected >= len(patches):
						selected = 0
				else:
					running = False
			elif event.type == pg.MOUSEBUTTONDOWN:
				selected += 1
				if selected >= len(patches):
					selected = 0

		renderer.draw_color = (0,0,0,255) 
		renderer.clear()

		x, y = pg.mouse.get_pos()
		rect = pg.Rect(10, 10, x, y)
		patches[selected].draw(rect)
		center = max(rect.centerx, tfont.width('Move or click mouse') // 2)
		tfont.draw('Move or click mouse', center, rect.centery, color=(255,0,0),
				align='center', valign='center')

		renderer.present()
		clock.tick(30)

def packed(*args):
	from .base import load_xml_images, scale_rect

	if args:
		filename = args[0]
	else:
		filename = EXAMPLE_DATA+'texture.xml'

	pg.init()
	clock = pg.time.Clock()
	window = Window("TexturePacker Test", size=SMALL_RESOLUTION)
	renderer = Renderer(window, vsync=True)
	clock = pg.time.Clock()

	images = load_xml_images(renderer, filename)
	dst = scale_rect(images[0].get_rect(), 2)
	dst.center = renderer.get_viewport().center
	for image in images:
		image.draw(dstrect=dst)
		renderer.present()
		clock.tick(5)
		renderer.clear()
		pg.event.pump()


def menu():
	from renderpyg import fetch_images, NinePatch, Menu, keyframes

	os.environ['SDL_RENDER_SCALE_QUALITY'] = '2'

	pg.init()
	clock = pg.time.Clock()
	window = Window("NinePatch Test", size=(900,600))
	renderer = Renderer(window, vsync=True)

	font, tfont = TextureFont.multi_font(renderer, (
		(EXAMPLE_DATA+'font.ttf', 32),
		(EXAMPLE_DATA+'font2.ttf', 32)))

	texture = load_texture(renderer, EXAMPLE_DATA+'nine.png')
	button = NinePatch(texture, (20,20,20,20), (0, 0, 320, 167))
	dialog = NinePatch(texture, (32,32,32,32), (0,169, 320, 161))
	box = NinePatch(texture, (22,24,22,24), (0, 332, 320, 106))
	box_fill = NinePatch(texture, (22,24,22,24), (0, 439, 320, 106))
	arrow_r, arrow_l, circle, bar = fetch_images(
		texture, rects=(
			(11, 559, 42, 42),
			(11, 559, 42, 42),
			(64, 547, 62, 62),
			(373,225, 222, 18)))
	arrow_l.flipX = True
	spinner = Sprite((circle,), 0,0 )
	spinner.set_animation(keyframes((0,), 500, rotation=60))
	spinner.set_clock(clock)
	alien = Sprite(
		(renderer, EXAMPLE_DATA+'texture.xml'), 7, 8, by_count=True)
	alien.set_animation(keyrange(0, 7, 200))
	alien.set_clock(clock)
	selection = ['button {}'.format(n) for n in range(29)]
	good_sound = pg.mixer.Sound(EXAMPLE_DATA+'click.ogg')
	bad_sound = pg.mixer.Sound(EXAMPLE_DATA+'cancel.ogg')
	background = load_texture(renderer, EXAMPLE_DATA+'grass.png')
	title = 'RenderPyg'
	anim_light = dict(move=(2,0), rotate=7)
	anim_heavy = dict(circle=2, rotate=15, variance=20, zoom=5)

	joy = None
	if pg.joystick.get_count() > 0:
		joy = (pg.joystick.Joystick(0), 0, 1)
		if joy.init():
			joy = None

	menu_basic = Menu(
		renderer, font, clock=clock,
		box=((255,255,255), (0,0,0), 4),
		color=(150,150,150), label=(200,200,200),
		sel_color=(255,255,255),
		position = 6,
		text_scale=.6,
	)
	menu_basic = Menu(renderer, font)

	menu_classic = Menu(
		renderer, font, clock=clock,
		sel_color=(255,255,255), sel_left=spinner,
		color=(150,150,150), label=(200,200,200),
		box=box, box_fill=circle,
		text_scale=.6,
	)

	menu_spinner = Menu(
		renderer, font, clock=clock, spacing=6,
		patch=dialog, but_patch=button, but_padding=(30, 30),
		sel_left=spinner,
		opt_left=arrow_l, opt_right=arrow_r,
		box=box, box_fill=box_fill, box_textc=(0,50,50),
		text_font=tfont, text_scale	=.5,
		title_font=tfont, title_scale=1.25, title_color=(0,0,200)
	)

	menu_full = Menu(
		renderer, font, clock=clock, spacing=6,
		patch=dialog, but_patch=button, but_padding=(40, 15),
		sel_patch=button,
		opt_left=arrow_l, opt_right=arrow_r,
		box=box, box_fill=box_fill, box_textc=(0,50,50),
		text_font=tfont, text_scale	=.4,
		title_font=tfont, title_scale=1.25, title_color=(0,0,200)
	)
	menu = menu_basic
	menu.title_anim = anim_light

	options = dict(
		type=('blank', 'oldschool', 'spinner', 'full', ('menu: ','')),
		back=('off', 'on', ('back: \t','')),
		lab1=('left\tright'),
		test={'type': 'SPACER', 'amount': '2'},
		color=('white', 'red', 'blue'),
		anim=('none', 'some', 'lots', ('anim: ', '')),
		anim_speed={'type': 'SLIDER', 'label': 'speed', 'min': 1, 'max': 9, 'step': 1} )

	def set_options():
		global menu
		new_menu = options['type']['value']
		menu = {'blank': menu_basic,
			'oldschool': menu_classic,
			'spinner': menu_spinner,
			'full': menu_full}[new_menu]

		back = background if options['back']['value'] == 'on' else (0,0,0)
		menu.set_background(back)

		color = options['color']['value']
		if color == 'red':
			menu.color = (255,0,0)
			menu.label = (150,0,0)
			menu.sel_color = (0,0,255)
		elif color == 'blue':
			menu.color = (0,0,255)
			menu.label = (0,0,150)
			menu.sel_color = (255,0,0)
		else:
			menu.color = (150,150,150)
			menu.label = (150,150,150)
			menu.sel_color = (255,255,255)

		anim, speed = options['anim']['value'], options['anim_speed']['value']
		anim_light['duration'] = (7 - speed) * 1000
		anim_heavy['duration'] = (7 - speed) * 1000
		if anim == 'some':
			menu.sel_anim = menu.title_anim = anim_light
			menu.anim = menu.text_anim = None
		elif anim == 'lots':
			menu.sel_anim = menu.title_anim = anim_heavy
			menu.anim = menu.text_anim = anim_light
		else:
			menu.sel_anim = menu.title_anim = None
			menu.anim = menu.text_anim = None
		return menu

	running = True
	while running:
		if menu == menu_classic:
			menu.position = random.choice((1, 6, 8))
		result = menu.select(('list', 'dialog', 'input', 'options', 'quit'), title)[1]
		if result == 'list':
			menu.select(selection, None)
		elif result == 'dialog':
			menu.dialog(text_data, title, ('Okay',), 600)
		elif result == 'input':
			text, i, button = menu.input('New Title', ('Okay', 'Cancel'))
			title = text if button == 'Okay' else title
		elif result == 'options':
			_, clicked, new = menu.options(options, title)#, buttons=('Okay', 'Cancel'))
			if clicked == 'Okay' or True:
				options = new
				menu = set_options()
		else:
			running = False

	'''
	# Here is how to use a modeless menu
	menu.input('Type Me', buttons=('Okay', 'Cancel'), modeless=True)
	while menu.alive:
		# Do Your Work here
		results = menu.handle()
		renderer.present()
		clock.tick(30)
	print(results)
	'''


text_data = """Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions."""
map_data = """
7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,
7,0,0,0,0,0,0,0,0,0,34,31,0,0,0,0,4,4,0,0,0,0,0,0,0,0,51,0,0,0,0,0,40,0,0,0,33,29,29,29,29,29,29,29,29,29,29,29,29,26,26,26,26,26,26,26,26,28,0,0,0,7,7,0,0,51,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,14,0,0,0,50,0,0,0,0,50,0,0,0,0,0,0,0,51,0,0,0,0,0,4,0,0,0,0,6,1,1,1,1,1,1,1,1,1,1,1,7,
7,0,0,0,0,0,0,0,0,34,26,26,31,0,0,0,4,4,0,0,0,0,0,0,51,0,0,0,0,0,0,0,40,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,26,26,26,26,26,26,26,28,0,0,0,7,7,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,51,0,14,0,0,8,4,9,0,50,0,0,0,0,0,0,0,0,0,0,50,0,0,0,0,4,0,0,0,51,6,1,1,1,1,1,1,1,1,1,1,1,7,
7,0,0,0,0,0,0,0,0,33,26,26,32,0,0,0,4,4,50,0,0,0,0,0,0,0,0,0,0,51,0,51,40,0,0,0,34,27,27,27,27,27,27,27,27,27,27,31,0,30,26,26,26,26,26,26,29,32,0,51,0,7,7,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,51,14,0,51,4,4,4,0,50,6,6,6,1,6,6,6,12,7,12,7,12,7,12,7,4,0,0,0,0,6,1,1,1,6,1,1,1,6,1,1,1,7,
7,0,0,0,0,0,0,0,0,0,33,32,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,40,0,0,0,30,26,26,26,26,26,26,26,26,26,26,28,0,30,26,26,26,26,26,28,0,0,0,0,0,7,7,0,0,50,0,50,0,51,0,0,0,0,0,0,0,0,0,0,0,0,0,14,0,0,4,4,4,0,0,6,1,1,1,1,1,6,7,0,7,0,7,0,7,0,4,0,0,0,0,6,1,1,1,6,1,1,1,6,1,1,1,7,
7,0,0,0,0,0,0,0,0,0,51,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,40,0,0,0,30,26,26,26,29,29,29,29,29,29,29,28,0,30,26,26,26,26,26,28,0,35,0,0,0,7,7,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,51,0,0,0,14,0,0,4,4,4,0,0,6,1,1,1,1,1,6,0,0,0,0,0,0,0,0,1,50,0,0,0,6,1,1,1,6,1,1,1,6,1,1,1,7,
7,51,0,0,0,0,0,0,0,0,0,0,0,0,0,51,4,4,0,50,51,0,0,0,0,0,51,0,0,0,0,51,40,51,0,50,30,26,26,28,0,0,0,0,0,0,0,40,0,30,26,26,26,26,26,28,0,40,51,0,0,7,7,0,0,0,0,51,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,14,0,51,4,4,4,0,0,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,4,0,0,0,0,6,1,1,1,6,1,1,1,6,1,1,1,7,
7,0,0,0,0,0,0,0,0,0,50,0,0,0,0,0,4,4,49,0,0,0,0,0,0,0,0,0,0,0,51,0,40,0,0,0,30,26,26,28,0,34,27,27,27,27,27,28,0,30,26,26,26,26,26,28,0,40,0,0,0,7,7,0,0,0,0,0,0,0,0,0,51,0,0,0,51,0,0,0,0,0,0,14,51,0,10,4,11,0,0,6,1,1,1,1,1,6,0,0,0,0,0,0,0,0,4,0,51,0,0,6,1,1,1,6,1,1,1,6,1,1,1,7,
7,0,0,51,0,0,0,0,0,0,0,0,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,40,0,50,0,30,26,29,32,0,33,26,26,26,26,26,28,0,33,29,29,29,29,29,32,0,40,50,0,0,7,7,0,0,0,0,0,0,51,0,0,0,0,51,0,0,0,0,0,0,0,0,14,0,0,0,0,0,0,0,6,1,1,1,1,1,6,0,0,0,0,0,0,0,0,4,9,0,0,0,6,1,1,1,6,1,1,1,6,1,1,1,7,
7,0,34,31,0,50,0,0,0,0,0,0,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,40,0,0,0,30,28,0,0,50,0,30,26,26,26,26,28,0,0,0,0,0,0,50,0,0,40,0,0,51,7,7,0,0,51,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,15,13,13,13,13,13,13,13,6,6,6,6,6,6,6,0,51,0,0,0,0,0,0,10,4,0,0,0,6,1,1,1,6,1,1,1,6,1,1,1,7,
7,34,26,26,31,0,0,0,0,0,0,0,51,0,0,0,4,4,0,0,0,0,0,51,0,0,0,0,0,0,0,0,40,0,0,0,30,28,0,0,0,0,30,26,26,26,26,28,0,34,27,27,27,27,27,31,0,40,0,0,0,7,7,50,0,0,0,0,0,0,51,51,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,51,0,0,0,0,51,0,0,4,0,0,0,6,1,1,1,6,1,1,1,6,1,1,1,7,
7,33,26,26,32,0,0,0,51,0,0,0,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,40,0,0,0,30,28,0,50,0,0,30,26,26,26,26,28,0,30,26,26,26,26,26,28,51,40,0,0,0,7,7,0,0,0,0,0,0,0,0,0,0,51,0,0,0,0,0,0,0,0,0,0,0,0,50,0,0,51,0,50,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,0,0,0,6,1,1,1,6,1,1,1,6,1,1,1,7,
7,0,33,32,0,0,0,0,0,0,0,0,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,50,0,0,0,40,0,0,0,30,28,0,0,0,0,33,29,29,29,29,32,0,30,26,26,26,26,26,28,0,40,50,0,0,7,7,0,0,0,0,0,0,6,6,6,6,6,6,6,13,13,13,18,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,50,0,0,0,0,0,0,0,0,0,4,9,0,0,6,6,6,6,6,6,1,6,6,6,6,6,7,
7,0,50,0,0,51,0,51,0,0,0,0,0,0,0,0,4,4,0,0,0,51,0,0,0,0,0,0,0,51,0,0,30,27,27,27,26,28,0,0,0,0,0,0,0,0,0,0,0,30,26,26,26,26,26,28,0,40,0,0,0,7,7,13,13,13,13,13,13,6,1,1,1,1,1,6,1,1,1,14,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,50,0,0,0,0,50,0,10,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,7,
7,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,9,0,0,0,0,0,0,0,0,0,0,0,0,0,30,26,26,26,26,26,27,27,27,27,27,27,27,27,27,31,0,30,26,26,26,26,26,28,0,40,0,0,0,7,7,0,0,0,0,0,0,6,1,1,1,1,1,6,1,1,1,14,51,0,0,51,0,0,0,0,0,0,0,51,0,0,0,0,0,0,0,0,0,0,0,0,0,0,51,0,4,0,51,51,0,51,0,0,0,51,50,0,0,50,0,7,
7,0,0,0,0,34,31,0,0,0,0,0,51,0,0,0,10,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,33,29,29,29,29,29,29,29,29,29,29,29,29,29,26,28,0,30,26,26,26,26,26,28,0,40,0,0,0,7,7,0,0,0,0,0,0,6,1,1,1,1,1,1,1,1,1,14,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,7,
7,51,0,0,34,26,26,31,0,0,0,0,0,0,51,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,50,0,0,0,0,50,0,0,30,28,0,30,26,26,26,26,26,28,0,40,0,0,0,7,7,0,0,0,0,0,0,6,1,1,1,1,1,6,1,1,1,14,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,50,51,0,0,0,0,0,0,0,0,4,0,0,51,0,0,0,0,0,0,0,0,0,0,0,7,
7,0,0,0,33,26,26,32,0,51,0,0,0,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,34,27,27,27,27,27,27,27,31,0,0,0,0,0,30,28,51,30,26,26,26,26,26,28,0,40,0,0,0,7,7,0,51,0,0,0,0,6,1,1,1,1,1,6,1,1,1,14,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0,0,0,50,0,0,0,0,0,7,
7,0,0,0,0,33,32,0,0,0,0,0,0,0,0,0,0,4,4,50,0,0,0,0,0,51,0,0,0,0,0,0,30,26,26,26,26,26,26,26,28,0,0,0,0,0,30,28,0,30,26,26,26,26,26,28,0,40,0,0,0,7,7,0,0,0,0,0,0,6,6,6,1,6,6,6,13,13,13,16,51,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,0,0,0,0,0,50,0,0,0,0,0,0,0,0,7,
7,0,0,0,0,0,0,0,0,0,0,34,31,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,30,26,26,26,26,26,26,26,28,49,0,0,51,0,30,28,0,30,26,26,26,26,26,28,0,40,0,0,0,7,7,0,0,0,0,0,0,51,14,0,50,0,0,0,0,0,0,0,0,51,0,0,0,0,0,0,0,0,0,51,0,0,0,0,0,0,0,0,0,0,0,0,51,0,0,0,4,51,0,0,0,0,0,0,0,0,0,0,0,0,0,7,
7,0,0,0,0,0,0,0,0,0,34,26,26,31,0,0,0,4,4,0,0,0,0,0,0,0,50,0,0,0,0,0,33,29,29,29,29,29,29,26,28,0,0,0,0,0,30,28,0,30,26,26,26,26,26,28,0,40,0,0,51,7,7,0,0,0,0,0,0,0,14,0,0,0,0,0,0,0,0,0,0,0,0,51,0,51,0,0,51,0,0,0,0,0,0,0,0,0,0,0,51,0,0,0,0,0,0,0,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,7,
7,0,0,0,0,0,0,0,0,0,33,26,26,32,0,0,0,4,4,0,50,0,51,0,0,0,0,0,0,50,0,50,0,0,0,0,0,0,0,30,26,27,27,27,27,27,26,32,0,33,26,26,26,26,26,28,0,40,0,0,0,7,7,0,51,0,0,0,0,0,14,0,0,0,51,0,0,0,0,0,51,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,51,0,0,0,0,0,4,0,0,0,0,0,0,0,51,0,0,0,0,0,0,7,
7,0,0,0,34,31,0,51,0,0,0,33,32,0,0,0,0,4,4,0,51,0,0,0,0,0,0,0,0,0,0,0,0,7,0,7,0,7,0,30,26,26,26,26,29,29,32,0,0,0,33,29,26,26,26,28,0,40,0,0,0,7,7,0,0,0,0,0,50,0,14,0,0,0,0,0,0,0,0,0,0,51,50,0,0,0,0,0,0,0,0,0,0,0,0,50,0,0,0,0,0,0,0,0,0,0,8,4,4,4,4,4,4,9,0,51,0,0,0,0,0,0,0,7,
7,0,0,0,30,28,0,0,0,0,0,0,0,0,0,0,0,4,4,0,0,0,0,0,0,50,0,51,0,0,0,0,7,12,7,12,7,50,0,30,26,26,26,28,0,0,0,0,0,0,0,0,30,26,26,28,50,40,0,51,0,7,7,0,0,0,0,0,0,0,14,0,0,0,0,51,0,0,0,51,0,0,0,0,0,0,50,0,0,0,0,0,0,51,0,0,0,0,0,0,0,0,50,50,0,0,4,4,4,4,4,4,4,4,0,0,0,0,0,0,0,0,0,7,
7,0,0,34,26,26,31,0,0,0,0,0,0,0,0,0,0,4,4,9,0,0,0,0,0,0,0,0,0,0,0,0,0,7,12,7,12,7,0,30,26,26,26,28,0,0,0,0,0,51,0,0,30,26,26,28,0,40,0,0,0,7,7,0,0,6,6,6,6,6,6,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,0,0,0,0,0,0,0,51,0,7,
7,0,0,33,26,26,32,0,50,0,0,0,0,0,0,0,0,10,4,4,0,0,0,0,0,0,0,0,0,0,51,0,7,12,7,12,7,0,0,33,29,29,29,32,0,0,0,0,0,0,0,0,30,26,26,28,50,40,0,0,0,7,7,0,0,6,1,1,1,1,1,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,51,0,51,0,0,0,50,0,0,0,0,0,51,0,0,0,4,4,4,4,4,4,4,4,0,0,50,51,0,0,0,0,0,7,
7,0,0,0,30,28,0,0,0,0,0,0,0,0,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,7,12,7,12,7,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,26,26,28,51,40,0,0,51,7,7,0,0,6,1,1,1,1,1,6,0,0,0,0,0,51,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,0,0,0,0,0,0,51,0,0,7,
7,0,0,0,33,32,0,0,0,0,0,51,0,0,0,0,50,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,7,12,7,12,7,0,0,34,27,27,27,31,0,0,0,0,0,0,0,0,30,26,29,32,0,40,0,0,0,7,7,0,0,6,1,1,1,1,1,1,0,0,0,0,6,6,1,6,6,6,6,6,1,6,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,0,0,0,0,0,0,0,0,0,7,
7,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,7,12,7,12,7,0,30,26,26,26,28,0,0,0,0,0,0,0,0,30,28,0,0,0,37,0,0,0,7,7,0,0,6,1,1,1,1,1,6,0,0,0,0,6,1,1,1,1,1,1,1,1,1,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,0,0,0,0,51,0,51,0,0,7,
7,0,0,0,0,0,0,0,34,31,0,0,0,0,0,0,0,0,4,4,0,0,0,0,50,0,0,0,0,0,0,0,7,12,7,12,7,0,0,30,26,26,26,28,0,0,0,51,0,0,0,0,30,28,0,35,0,0,0,0,0,7,7,0,0,6,1,1,1,1,1,6,0,0,0,0,6,1,1,1,1,1,1,1,1,1,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,51,4,4,4,4,4,4,4,4,0,0,0,51,0,0,0,0,0,7,
7,0,0,0,0,0,0,34,26,26,31,0,0,0,0,0,0,0,4,4,50,51,0,0,0,0,0,0,0,0,0,0,0,7,0,7,0,7,0,30,26,26,26,26,27,27,27,27,27,27,27,27,26,28,0,40,0,35,0,0,0,7,7,0,0,6,1,1,1,1,1,6,50,0,0,0,6,1,1,1,1,1,1,1,1,1,6,0,0,0,50,0,0,0,51,0,0,0,0,0,0,0,0,0,50,0,4,4,4,4,4,4,4,4,0,0,0,0,0,51,0,0,0,7,
7,0,50,0,0,0,0,33,26,26,32,0,0,0,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,51,0,0,0,30,26,29,29,29,29,29,29,29,29,26,26,26,26,28,51,40,0,40,0,0,0,7,7,0,0,6,1,1,1,1,1,6,0,0,0,0,6,1,1,1,1,1,1,1,1,1,6,51,0,0,0,0,0,0,0,0,0,51,50,0,0,0,0,0,0,0,10,4,4,4,4,4,4,11,0,0,0,0,0,0,0,0,0,7,
7,0,0,0,0,0,0,0,33,32,0,0,0,0,0,51,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,34,27,27,27,27,27,27,26,28,0,0,51,0,0,0,0,0,30,26,26,26,28,0,40,0,40,0,0,0,7,7,0,50,6,1,1,1,1,1,6,0,0,0,0,6,6,6,6,6,6,6,6,6,6,6,0,0,6,6,1,6,6,6,6,6,6,6,6,6,1,6,6,0,0,0,0,0,0,0,10,4,0,51,0,0,0,0,0,0,0,0,7,
7,0,34,31,50,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,30,26,26,26,26,26,26,26,28,0,0,0,0,0,51,0,0,33,29,29,29,32,0,40,0,40,0,0,51,7,7,0,0,6,1,1,1,1,1,6,0,0,0,0,51,0,0,0,0,0,0,0,0,0,0,0,0,6,1,1,1,1,1,1,6,1,1,1,1,1,1,6,51,0,0,0,0,0,0,0,4,0,51,0,0,0,0,0,0,0,0,7,
7,34,26,26,31,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,0,0,0,50,0,0,0,0,0,0,0,0,30,26,26,26,26,26,26,26,28,0,0,0,0,0,0,0,0,0,0,0,0,0,0,40,0,40,0,0,0,7,7,0,0,1,1,1,1,1,1,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,1,1,1,1,1,1,6,1,1,1,1,1,1,6,0,0,0,0,0,0,0,0,1,51,0,0,0,0,0,50,0,0,0,7,
7,33,26,26,32,0,0,0,0,51,0,0,0,0,0,0,0,0,4,4,0,0,0,0,0,0,51,0,0,0,0,0,30,26,26,26,26,26,26,26,28,0,0,0,0,0,0,0,0,38,39,39,39,39,39,32,0,40,0,0,0,7,7,0,0,6,1,1,1,1,1,6,0,0,0,50,0,0,0,0,0,0,0,0,51,0,0,0,0,6,1,1,1,1,1,1,6,1,1,1,1,1,1,6,0,0,0,0,0,0,0,51,4,51,0,0,0,0,0,0,0,0,50,7,
7,50,33,32,0,0,0,0,0,0,51,0,51,0,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,30,26,26,26,26,26,26,26,28,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,40,0,0,0,7,7,0,0,6,6,6,6,6,6,6,0,0,0,0,0,51,0,0,0,0,0,0,0,51,0,0,0,6,1,1,1,1,1,1,6,1,1,1,1,1,1,6,0,0,0,0,0,0,0,0,4,0,0,0,0,0,50,0,0,0,0,7,
7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,
7,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0,0,7,7,0,0,0,0,0,0,0,50,0,34,31,0,0,0,0,4,4,51,0,0,0,0,0,0,0,0,0,0,0,0,0,40,0,0,0,33,29,29,29,29,29,29,29,29,29,29,29,29,26,26,26,26,26,26,26,26,28,0,0,0,7,
7,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0,0,7,7,0,0,0,0,0,0,0,0,34,26,26,31,0,0,0,4,4,0,0,0,0,0,0,0,51,0,0,0,0,0,51,40,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,51,30,26,26,26,26,26,26,26,28,0,0,0,7,
7,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,11,0,0,0,10,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0,0,7,7,0,0,0,0,0,0,0,0,33,26,26,32,0,0,50,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,40,51,0,0,34,27,27,27,27,27,27,27,27,27,27,31,0,30,26,26,26,26,26,26,29,32,0,0,0,7,
7,4,4,4,4,4,4,4,11,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,10,4,4,4,4,4,4,4,4,51,0,51,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,7,7,0,0,0,0,0,0,0,0,0,33,32,0,0,0,50,4,4,0,0,0,0,0,0,0,0,0,0,0,51,0,51,40,0,0,0,30,26,26,26,26,26,26,26,26,26,26,28,0,30,26,26,26,26,26,28,0,0,0,0,0,7,
7,4,4,4,4,4,4,4,0,0,0,0,0,0,0,0,0,0,50,0,0,0,51,0,0,0,0,0,4,4,4,4,4,4,4,4,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0,0,7,7,0,0,0,51,0,51,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,51,0,0,0,40,0,0,0,30,26,26,26,29,29,29,29,29,29,29,28,0,30,26,26,26,26,26,28,0,35,0,0,0,7,
7,4,4,4,4,4,4,4,0,0,0,0,0,0,0,0,0,0,0,0,50,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,9,0,0,50,0,50,0,7,7,0,51,0,0,0,0,0,0,0,0,51,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,40,0,0,0,30,26,26,28,0,0,0,0,0,0,0,40,0,30,26,26,26,26,26,28,0,40,0,0,0,7,
7,4,4,11,51,10,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,9,0,0,0,8,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,7,7,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,49,0,0,0,0,51,0,0,0,0,0,0,0,0,40,0,51,0,30,26,26,28,0,34,27,27,27,27,27,28,0,30,26,26,26,26,26,28,0,40,51,0,0,7,
7,4,4,0,0,0,4,4,0,0,0,0,0,0,51,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,7,7,0,0,0,0,0,0,0,0,0,0,0,0,0,0,51,4,4,0,50,0,0,0,0,0,0,0,0,0,0,0,0,40,0,0,0,30,26,29,32,0,33,26,26,26,26,26,28,0,33,29,29,29,29,29,32,0,40,0,0,0,7,
7,4,4,50,0,0,1,1,0,0,0,0,0,0,0,0,0,51,0,0,0,0,0,0,0,51,0,8,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,7,7,0,34,31,0,0,0,0,0,0,0,0,0,0,0,0,4,4,0,0,0,0,51,0,0,0,51,0,0,0,0,0,40,0,51,51,30,28,0,0,0,0,30,26,26,26,26,28,0,0,51,0,0,0,0,0,0,40,0,51,51,7,
7,4,4,9,0,8,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,7,7,34,26,26,31,0,0,0,0,0,51,0,51,51,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,40,0,0,0,30,28,0,0,0,0,30,26,26,26,26,28,0,34,27,27,27,27,27,31,0,40,0,0,0,7,
7,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,7,7,33,26,26,32,0,0,0,0,0,51,0,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,40,0,0,0,30,28,0,0,0,0,30,26,26,26,26,28,0,30,26,26,26,26,26,28,0,40,0,0,0,7,
7,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,7,7,0,33,32,0,0,0,0,0,0,0,0,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,40,0,0,51,30,28,0,0,0,0,33,29,29,29,29,32,0,30,26,26,26,26,26,28,0,40,0,0,0,7,
7,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,7,7,0,0,0,0,0,0,0,0,51,0,0,0,0,50,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,51,0,30,27,27,27,26,28,0,0,0,0,0,0,0,0,51,0,0,30,26,26,26,26,26,28,0,40,0,0,0,7,
7,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,11,0,0,0,10,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,7,7,0,0,0,0,50,0,0,0,0,0,0,0,0,0,0,4,4,9,0,0,0,0,0,0,0,0,0,0,0,0,0,30,26,26,26,26,26,27,27,27,27,27,27,27,27,27,31,0,30,26,26,26,26,26,28,0,40,0,0,0,7,
7,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,0,0,0,0,0,4,4,4,4,4,4,11,0,0,0,0,0,51,0,0,0,0,0,10,4,4,4,7,7,0,0,0,0,34,31,0,0,50,0,0,51,0,0,0,10,4,4,0,51,0,51,0,0,0,0,0,0,0,0,0,33,29,29,29,29,29,29,29,29,29,29,29,29,29,26,28,0,30,26,26,26,26,26,28,0,40,0,0,0,7,
7,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,51,0,0,0,0,4,4,4,4,4,4,0,7,0,0,0,0,0,0,51,0,0,0,0,4,4,4,7,7,0,0,0,34,26,26,31,0,0,0,0,0,0,0,0,0,4,4,0,0,51,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,28,51,30,26,26,26,26,26,28,0,40,0,0,0,7,
7,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,7,0,4,4,4,7,7,0,0,0,33,26,26,32,0,0,0,0,0,0,0,0,0,4,4,0,0,0,0,0,0,0,0,51,50,0,0,0,34,27,27,27,27,27,27,27,31,0,0,0,0,0,30,28,0,30,26,26,26,26,26,28,0,40,0,0,0,7,
7,0,0,0,50,0,0,0,0,10,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,9,0,0,0,8,4,4,4,4,4,4,0,0,0,0,7,0,0,0,0,0,0,0,0,4,4,4,7,7,0,0,0,0,33,32,0,0,0,0,0,0,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,30,26,26,26,26,26,26,26,28,0,0,0,0,0,30,28,0,30,26,26,26,26,26,28,0,40,0,0,0,7,
7,0,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,4,7,7,0,0,0,0,0,0,0,0,0,0,34,31,0,0,0,50,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,30,26,26,26,26,26,26,26,28,49,0,0,0,0,30,28,0,30,26,26,26,26,26,28,0,40,0,0,0,7,
7,0,50,0,0,0,0,51,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,0,7,51,0,0,0,0,51,0,0,0,0,0,4,4,4,7,7,0,0,0,0,0,0,0,0,0,34,26,26,31,0,0,0,4,4,51,0,0,0,0,0,0,0,0,0,0,0,51,33,29,29,29,29,29,29,26,28,50,0,0,0,0,30,28,0,30,26,26,26,26,26,28,0,40,0,0,0,7,
7,0,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,11,0,0,0,0,0,0,0,10,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,4,7,7,0,50,0,0,0,0,0,0,0,33,26,26,32,0,51,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,26,27,27,27,27,27,26,32,0,33,26,26,26,26,26,28,50,40,50,0,0,7,
7,0,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,50,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0,0,0,0,51,0,0,0,4,4,4,7,7,0,0,0,34,31,0,0,51,51,0,33,32,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,7,0,7,0,7,0,30,26,26,26,26,29,29,32,0,51,0,33,29,26,26,26,28,0,40,0,0,0,7,
7,0,0,0,0,0,50,0,0,0,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,4,1,51,0,0,51,0,51,0,0,7,0,0,50,0,4,4,4,7,7,0,0,0,30,28,0,0,51,0,51,0,0,0,0,0,0,4,4,0,0,0,0,0,51,0,0,0,0,0,0,0,7,12,7,12,7,0,0,30,26,26,26,28,50,0,0,0,0,0,0,0,30,26,26,28,0,40,0,0,0,7,
7,0,50,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,7,0,0,0,51,0,0,0,4,4,4,7,7,0,0,34,26,26,31,0,0,0,0,0,0,0,0,0,0,4,4,9,0,0,0,0,51,0,0,0,0,0,0,0,0,7,12,7,12,7,0,30,26,26,26,28,0,0,0,0,0,0,0,0,30,26,26,28,0,40,0,0,0,7,
7,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,9,0,0,0,0,0,0,0,0,0,0,0,8,4,4,4,7,7,0,0,33,26,26,32,0,0,0,0,0,0,0,0,0,0,10,4,4,0,0,0,0,0,0,0,0,0,0,0,0,7,12,7,12,7,0,0,33,29,29,29,32,51,0,51,0,0,0,0,0,30,26,26,28,0,40,0,0,0,7,
7,0,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,0,51,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,7,7,0,0,0,30,28,0,0,0,0,0,0,51,0,0,0,0,0,4,4,0,0,50,0,51,0,0,0,0,0,0,0,0,7,12,7,12,7,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,26,26,28,0,40,0,0,0,7,
7,0,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0,0,0,50,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,7,7,0,0,0,33,32,0,0,0,0,0,0,0,0,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,7,12,7,12,7,0,0,34,27,27,27,31,0,0,0,0,0,0,0,0,30,26,29,32,51,40,0,0,0,7,
7,0,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,0,0,51,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,7,7,51,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,7,12,7,12,7,0,30,26,26,26,28,0,0,0,0,0,0,0,0,30,28,0,0,0,37,0,0,0,7,
7,0,0,50,0,0,0,0,0,50,4,4,4,4,4,4,4,4,4,4,4,9,0,0,0,50,0,0,0,8,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,7,7,0,0,0,0,0,0,0,34,31,0,0,0,0,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,51,0,0,7,12,7,12,7,0,0,30,26,26,26,28,0,0,0,0,0,0,0,0,30,28,0,35,0,0,0,0,0,7,
7,0,0,0,0,0,0,0,50,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,7,7,0,0,0,0,0,0,34,26,26,31,0,0,0,51,0,0,0,4,4,0,0,0,0,0,50,0,0,0,0,0,0,0,7,0,7,0,7,0,30,26,26,26,26,27,27,27,27,27,27,27,27,26,28,0,40,0,35,0,51,0,7,
7,51,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,7,7,0,0,50,0,0,51,33,26,26,32,0,0,0,0,0,51,0,4,4,0,51,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,26,29,29,29,29,29,29,29,29,26,26,26,26,28,51,40,0,40,0,0,0,7,
7,0,0,0,0,0,51,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,1,4,4,4,4,4,4,7,7,0,0,0,0,0,0,0,33,32,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,50,0,0,0,34,27,27,27,27,27,27,26,28,0,0,0,0,0,0,0,0,30,26,26,26,28,0,40,0,40,0,0,0,7,
7,0,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,11,0,0,51,0,0,0,0,0,0,0,0,0,0,51,0,0,0,0,10,4,4,4,4,4,4,4,4,4,0,0,49,4,4,4,4,4,7,7,0,34,31,0,0,0,0,0,0,0,0,0,51,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,0,0,30,26,26,26,26,26,26,26,28,0,0,0,0,0,0,0,0,33,29,29,29,32,0,40,0,40,0,0,0,7,
7,0,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,11,0,0,51,0,0,0,0,50,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,51,0,0,1,1,1,1,1,7,7,34,26,26,31,0,0,0,0,0,0,51,0,0,0,0,0,0,4,4,51,0,0,51,0,0,0,0,0,0,0,0,30,26,26,26,26,26,26,26,28,0,0,0,0,0,0,0,0,0,0,0,0,0,0,40,0,40,0,0,0,7,
7,0,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,51,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,7,7,33,26,26,32,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,51,0,0,0,0,0,0,0,0,0,0,0,30,26,26,26,26,26,26,26,28,0,0,0,0,0,0,0,0,38,39,39,39,39,39,32,0,40,0,0,51,7,
7,0,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,0,51,0,0,0,0,0,0,0,0,0,0,0,0,0,0,49,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,7,7,0,33,32,51,0,0,0,0,0,0,0,0,0,0,0,0,0,4,4,0,0,0,0,0,0,0,0,0,0,51,0,30,26,26,26,26,26,26,26,28,0,0,0,0,51,0,0,0,0,0,0,0,0,0,0,0,40,0,0,0,7,
7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,"""


if __name__ == '__main__':
	if len(sys.argv) > 1:
		if sys.argv[1] in EXAMPLES:
			locals()[sys.argv[1]](*sys.argv[2:])
	else:
		print('AVAILABLE EXAMPLES')
		for name, desc in EXAMPLES.items():
			print('{:10s}:  {}'.format(name, desc))
		print('\nTry python -m renderpyg.examples example_name parameters')
