'''
tilemap: Tilemap Renderer

Renderer tilemaps loaded with pytmx or built in functions. Uses
the pygame._sdl2 GPU renderer.

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
import pygame as pg
from functools import partial
from pygame._sdl2 import Window, Renderer, Texture, Image
from array import array
from .base import fetch_images, load_images, load_texture
import math

buffer = None

try:
	import pytmx
	_PYTMX = True
except ImportError:
	_PYTMX = False

def scale_tilemap(tilemap, camera=(0,0), scale=1, **kwargs):
	'''
	Draw pytmx or inbuilt tilemap onto pygame GPU renderer

	:param tilemap: pytmx or internal tilemap class
	:param camera: pg.Vector2 for top left camera location
	:param scale: float scale value defaults to 1.0
	:param center: pg.Vector2 to set center camera location
			True to adjust camera for center
			Overides camera
	:param srcrect: area to render in world coordinates overides scale
			Ignores height to maintain aspect ratio
	:param dstrect: screen area to render into
			defaults to entire renderer area
	:param smooth: for smoother scaling transition but less accurate
	:param clamp: True to adjust camera to fit world coordinates
	:rvalue (camx, camy, scale): for adjusting other images

	TODO:
		impliment smoothing
	'''

	'''
	Setup renderer and viewport
	'''
	global buffer
	renderer = tilemap.images[1].texture.renderer
	old_viewport = renderer.get_viewport()
	old_target = renderer.target
	rend_width, rend_height = renderer.target.get_rect().size if\
			renderer.target else old_viewport.size

	'''
	Parse options
	'''
	smooth = kwargs.get('smooth', False)
	clamp = kwargs.get('clamp', False)
	cam_x = int(camera[0])
	cam_y = int(camera[1])
	scale = camera[2]

	dstrect = kwargs.get('dstrect', None)
	try:
		if dstrect:
			if not hasattr(dstrect, 'width'):
				dstrect = pg.Rect(*dstrect)
			renderer.set_viewport(dstrect)
			rend_width = dstrect.width
			rend_height = dstrect.height
	except Exception:
		raise ValueError(
			'render_tilemap() cannot parse "{}" as dest_rect'.format(dstrect))

	tile_w = int(tilemap.tilewidth * scale)
	tile_h = int(tilemap.tileheight * scale)
	cell_count = len(tilemap.images)
	cells_wide = rend_width // tile_w + 2
	cells_high = rend_height // tile_h + 2

	start_cellx, offset_x = divmod(int(cam_x), tile_w)
	start_celly, offset_y = divmod(int(cam_y), tile_h)	

	layer = tilemap.layers[0].data
	dest_rect = pg.Rect(-offset_x, -offset_y, tile_w, tile_h) 

	if 'background' in kwargs:
		tile_background(renderer, kwargs['background'], (cam_x, cam_y), scale)
	'''
	Render Tilemap
	'''

	width = rend_width * scale
	height = rend_height * scale

	for row in layer[start_celly: start_celly + cells_high]:
		for frame in row[start_cellx: start_cellx + cells_wide]:
			if frame > 0:
				tilemap.images[frame].draw(dstrect=dest_rect)
			dest_rect.x += tile_w
		dest_rect.y += tile_h
		dest_rect.x = -offset_x


	return cam_x, cam_y, scale

def tile_background(renderer, background, camera=(0,0), scale=1):
	'''
	background: image or texture to be tiled across the screen
	camera: Vector2 representing the top left corner of the screen
	screensize: Rect representing the size of the buffer we will render to

	This function fills the background by tiling a background image across the screen
	It works similarly to RenderTilemap, except each 'cell' is the same larger background image
	'''
	rend_width, rend_height = renderer.target.get_rect().size if\
			renderer.target else renderer.get_viewport().size
	brect = background.get_rect()
	brect.w *= scale
	brect.h *= scale

	px = int(camera[0])
	py = int(camera[1])
	ox = -int(px % brect.width)
	oy = -int(py % brect.height)

	for y in range(oy, rend_height, brect.height):
	 	for x in range(ox, rend_width, brect.width):
	 	 	brect.x = x
	 	 	brect.y = y
	 	 	background.draw(dstrect=brect)   

def render_tilemap(tilemap, camera=(0,0,1), scale=1, **kwargs):
	'''
	Draw pytmx or inbuilt tilemap onto pygame GPU renderer

	:param tilemap: pytmx or internal tilemap class
	:param camera: pg.Vector2 for top left camera location
	:param scale: float scale value defaults to 1.0
	:param center: pg.Vector2 to set center camera location
			True to adjust camera for center
			Overides camera
	:param srcrect: area to render in world coordinates overides scale
			Ignores height to maintain aspect ratio
	:param dstrect: screen area to render into
			defaults to entire renderer area
	:param smooth: for smoother scaling transition but less accurate
	:param clamp: True to adjust camera to fit world coordinates
	:rvalue (camx, camy, scale): for adjusting other images

	TODO:
		impliment smoothing
	'''

	'''
	Setup renderer and viewport
	'''
	global buffer
	renderer = tilemap.images[1].texture.renderer
	old_viewport = renderer.get_viewport()
	old_target = renderer.target
	rend_width, rend_height = renderer.target.get_rect().size if\
			renderer.target else old_viewport.size

	'''
	Parse options
	'''
	smooth = kwargs.get('smooth', False)
	clamp = kwargs.get('clamp', False)
	cam_x = int(camera[0])
	cam_y = int(camera[1])
	scale = camera[2]

	dstrect = kwargs.get('dstrect', None)
	try:
		if dstrect:
			if not hasattr(dstrect, 'width'):
				dstrect = pg.Rect(*dstrect)
			renderer.set_viewport(dstrect)
			rend_width = dstrect.width
			rend_height = dstrect.height
	except Exception:
		raise ValueError(
			'render_tilemap() cannot parse "{}" as dest_rect'.format(dstrect))

	srcrect = kwargs.get('srcrect')
	try:
		if hasattr(srcrect, 'width'):
			renderer.set_viewport(srcrect)
			camera = srcrect.pos
			scale = rend_width / srcrect.width
			center = False
		elif srcrect:
			srcrect = pg.Rect(srcrect)
	except:
		raise ValueError(
			'render_tilemap() cannot parse "{}" as src_rect'.format(dstrect))

	center = kwargs.get('center', False)
	try:
		if center and center != True:
			cam_x = int(center[0])
			cam_y = int(center[1])
			center = True
	except:
		raise ValueError(
			'render_tilemap() cannot parse "{}" as center pos'.format(center))

	if center:
		cam_x = (cam_x*scale) - (rend_width / 2)
		cam_y =  (cam_y*scale) - (rend_height / 2)
	else:
		cam_x = cam_x * scale
		cam_y = cam_y * scale

	'''
	Prepare to render the tilemap
	'''
	cell_count = len(tilemap.images)
	tile_w = int(tilemap.tilewidth * scale)
	tile_h = int(tilemap.tileheight * scale)
	cells_wide = rend_width // tile_w + 2
	cells_high = rend_height // tile_h + 2

	if clamp:
		cam_x = min(max(0, cam_x), tile_w*tilemap.width - rend_width)
		cam_y = min(max(0, cam_y), tile_h*tilemap.height - rend_height)

	start_cellx, offset_x = divmod(int(cam_x), tile_w)
	start_celly, offset_y = divmod(int(cam_y), tile_h)	

	if start_cellx < 0: # Handle negative values
		offset_x += start_cellx * tile_w
		start_cellx = 0
	if start_celly < 0:
		offset_y += start_celly * tile_h
		start_celly = 0

	dest_rect = pg.Rect(-offset_x, -offset_y, tile_w, tile_h) 
	layer = tilemap.layers[0].data

	if 'background' in kwargs:
		tile_background(renderer, kwargs['background'], (cam_x, cam_y), scale)
	'''
	Render Tilemap
	'''
	for row in layer[start_celly: start_celly + cells_high]:
		for frame in row[start_cellx: start_cellx + cells_wide]:
			if frame > 0:
				tilemap.images[frame].draw(dstrect=dest_rect)
			dest_rect.x += tile_w
		dest_rect.y += tile_h
		dest_rect.x = -offset_x

	#camera[0] = cam_x
	#camera[1] = cam_y

	'''
	Cleanup
	'''
	#camera = cam_x, cam_y, scale
	return cam_x, cam_y, scale
	

def pgvideo_image_loader(renderer, filename, colorkey, **kwargs):
	'''
	Loads an image file into a Texture and holds a reference to it
	Returns a generator function that creates Images based on the
	texture and given rects

	:param renderer: active video.Renderer
	:param filename: path to Tiled tmx tilemap file
	:param colorkey: unused surface colorkey unused in GPU rendering
	:rvalue: generator function
	'''
	from pygame._sdl2 import video
	flag_names = (
		'flipped_horizontally',
		'flipped_vertically',
		'flipped_diagonally',)
	def convert(surface): # convert pygame surface to a video.Texture
		texture_ = video.Texture.from_surface(renderer, surface)
		texture_.blend_mode = 1
		del surface
		return texture_

	def load_image(rect=None, flags=None):
		if rect:
				rect = pg.Rect(*rect)
				image = video.Image(texture)
				image.srcrect = rect
				
				if flags.flipped_horizontally:
					image.flipX = True
				elif flags.flipped_vertically:
					image.flipY = True
				elif flags.flipped_diagonally:
					image.flipX = True
					image.flipY = True
				return image
		else:
			return video.Image(texture)

	texture = convert(pg.image.load(filename))
	return load_image

def load_tmx(renderer, filename, *args, **kwargs):
	'''
	This function simplifies loading tilemaps from tiled tmx files
	It uses a partial function to provide a renderer reference to pytmx

	:param renderer: active video.Renderer
	:param filename: path to Tiled tmx tilemap file
	:rvalue pytmx.TiledMap
	'''
	kwargs['image_loader'] = partial(pgvideo_image_loader, renderer)
	tilemap = pytmx.TiledMap(filename, *args, **kwargs)
	print('tilemap loaded from {}\n\tSIZE: map={}, tile={}, world={}'.format(
			filename, (tilemap.width, tilemap.height),
			(tilemap.tilewidth, tilemap.tileheight),
			(tilemap.width * tilemap.tilewidth, tilemap.height *
			tilemap.tileheight) ))
	return tilemap


def load_tilemap_string(
		data, delimit=',', line_break='\n', default=0, fill=True):
	'''
	Load data from a string into a tilemap. A tilemap is a python list
	of arrays with unsigned int values. Tilemap data can be accessed as
	tilemap[y_cell][x_cell] where x_cell < width, y_cell < height, and
	the highest value is returned as highest_value.

	:param data: a single python string of int values for each cell in map
	:param delimit: delimiter separating int values, def = ','
	:param line_break: delimiter separaing each row, def = '\\n'
	:param default: value to replace invalid or missing cell values
	:param fill: fill short rows with default if true(def),
			else trim lines to shortest
	:rvalue: tilemap, (width, height, highest_value)
	'''
	tilemap = []
	rows = []
	longest_row = 0
	shortest_row = not 0
	highest_value = 0
	for line in data.strip(' \n').split(line_break):
		row = line.strip(' ,').split(delimit)
		longest_row = max(longest_row, len(row))
		shortest_row = min(shortest_row, len(row))
		data = []
		for item in row:
			try:
				highest_value = max(highest_value, int(item))
				data.append(max(0, int(item)))
			except:
				data.append(default)
		rows.append(data)
	width = longest_row if fill else shortest_row
	for row in rows:
		tilemap.append(array('H', row[:width]))

	print('tilemap loaded from string\n\tSIZE: map={}'.format(
			(width, len(tilemap)) ))
	return tilemap, (width, len(tilemap), highest_value)


def load_tileset(
		renderer, filename, width, height, spacing=0, margin=0,
		texture=None, by_count=False):
	'''
	Load a tileset from given filename using tiles with given width and
	height.The tileset can be attached to a Tilemap object and then
	rendered with the render_tilemap() function.

 	:param renderer: renderer to attach texture to
 	:param filename: image file to load images from
 	:param width: width of images, or number of columns if by_count=True
 	:param height: height of images, or number of rows if by_count=True
 	:param spacing: space between each image in the texture
 	:param margin: margin of empty space around the edge of texture
 	:param by_count: set True to use width and height value to
 	 	 	calculate frame size from width and height of spritesheet
 	:param texture: fetch images from this texture instead of filename
 	:rvalue: list of pygame._sdl2.video.Image objects
	'''
	if texture:
		fetch_images(texture, width, height, spacing, margin, by_count)
	else:
		return load_images(
			renderer, filename, width, height, spacing, margin, by_count)


class Tilemap:
	'''
	Simple tilemap class available as replacement for the recommended
	pytmx module
	'''
	def __init__(self, _map, cells):
		'''
		Initialize inbuilt Tilemap object for drawing with pygame
		GPU renderer.

		:param tuple _map: tilemap returned from load_tilemap_string()
		:param list cells: tileset loaded with the load_tileset()
		'''
		self.layers = []
		self.images = []
		self.width = 0
		self.height = 0
		self.tilewidth = 0
		self.tileheight = 0

		tile_data, info = _map
		width, height, highest = info
		self.layers.append(self.Layer(_map))
		self.images = cells
		self.width = width
		self.height = height
		self.tilewidth = cells[1].get_rect().width
		self.tileheight = cells[1].get_rect().height
		self.worldwidth = width * cells[1].get_rect().width
		self.worldheight = height * cells[1].get_rect().height
		self.highest_value = highest
		if len(cells) < highest+1:
			self.clean_tilemap(0)

	def add_layer(self, _map):
		'''
		Add a layer to the Tilemap

		:param tuple _map: tilemap returned by the load_tilemap_string()
		:rvalue: None
		'''
		if self.verify_tilemap(_map):
			self.layers.append(self.Layer(_map))

	def clean_tilemap(self, layer, default=0):
		'''
		Remove invalid values from the tilemap.

		:param layer: index of layer in self.layers list
		:param default: value to replace invalid entries in the layer, def=0
		:rvalue: None
		'''
		data = self.layers[layer].data
		tile_count = len(self.images)
		if default > 0 and int(default) < tile_count:
			default = default
		else:
			default = 0

		for row in data:
			for x, cell in enumerate(row):
				if cell < 0 or cell > tile_count-1:
					row[x] = default

	def update_tileset(self, replacement):
		'''
		Replace the images in the Tilemap or the texture they reference

		:param replacement: texture or list of image
		:rvalue: None
		'''
		if type(replacement) == Texture:
			for image in self.images:
				image.texture = replacement
		else:
			try:
				tiles = len(replacement)
			except Exception as e:
				raise ValueError(
					'Tilemap.update_texture cannot parse "{}" '+
					'as texture or tileset'.format(replacement))	
			if self.highest_value < tiles:
				self.images = replacement
			else:
				print('tileset too small for current tilemap: ignoring update')

	def update_tilemap(self, _map, layer=0):
		'''
		Replace given layer with new tilemap data

		:param _map: tilemap loaded by load_tilemap_string() function
		:param layer: index of layer in self.layers to replace, def = 0
		:rvalue: None
		'''
		if self.verify_tilemap(_map) and layer < len(self.layers):
			self.layers[layer] = self.Layer(_map)

	def verify_tilemap(self, _map):
		'''
		Verify tilemap layer validity

		:param _map: tilemap returned by load_tilemap_string() function
		:rvalue: True if tilemap is valid
		'''
		try:
			tile_data, info = _map
			width, height, highest = info
			if (len(tile_data) == height == self.height and
					len(tile_data[0]) == width == self.width and 
					len(self.images) >= highest):
				return True
			else:
				print('tilemap not valid with current tileset')
				return False
		except Exception as e:
			raise ValueError('Tilemap.update_tilemap cannot parse '+
					'"{}" as tilemap'.format(_map))

	class Layer:
		'''
		Simple class used to maintain layout used by pytmx module
		'''
		def __init__(self, _map):
			tile_data, info = _map
			width, height, highest = info
			self.data = tile_data
			self.width = width
			self.height = height
			self.highest_value = highest
