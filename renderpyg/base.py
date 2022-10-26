"""
base.py: basic texture handling

Loads textures from image files and creates Image objects.

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
"""
import pygame as pg
from pygame._sdl2 import Renderer, Texture, Image

loaded_textures = {}

def fetch_images(texture, width=0, height=0, spacing=0, margin=0, by_count=False, rects=None):
	"""
	Returns an image list generated from a given texture and either the
	image size or the number of images in a sprite sheet.

	:param textue: texture to fetch images from
	:param width: width of images, or number of columns if by_count=True
	:param height: height of images, or number of rows if by_count=True
	:param spacing: space between each image in the texture
	:param margin: margin of empty space around the edge of texture
	:param by_count: set True to use width and height value to
		calculate frame size from width and height of spritesheet
	:rvalue: list of pygame._sdl2.video.Image objects
	"""
	tex_width, tex_height = texture.get_rect().size
	if isinstance(texture, Image):
		marginx = margin + image.srcrect.x
		marginy = margin + image.srcrect.y
	else:
		marginx = marginy = margin

	if by_count:
		width = tex_width // width
		height = tex_height // height

	tiles = []
	if rects:
		for rect in rects:
			im = Image(texture, srcrect=rect)
			tiles.append(im)
		return tiles		

	r = pg.Rect(0, 0, width, height)
	for y in range(margin, tex_height+margin-height+1, height+spacing):
		for x in range(margin, tex_width+margin-width+1, width+spacing):
			r.x = x
			r.y = y
			im = Image(texture, srcrect=r)
			tiles.append(im)
	return tiles


def load_xml_images(renderer, filename, _filter=[], by_name=False):
	"""
	Load images from a TextureAtlas XML file. Images may be filtered
	and are return in a list, or optionally, a dict images indexed by
	the name found in the xml file.

	:param renderer: renderer to attach texture to
	:param filename: path to a valid TextureAtlas XML file
	:param fiter: list of file names or numbers to include in the list
	:param by_name: set true to return a dict with image names
	:rvalue: list of images as ordered in filename by default
		optionally returns dict with image names instead
	"""
	import xml.etree.ElementTree as ET
	import os

	root = ET.parse(filename).getroot()
	if root.tag != 'TextureAtlas':
		raise ValueError("'{}' is not a TextureAtlas XML file".format(filename))

	path = os.path.join(os.path.dirname(filename), root.attrib['imagePath'])
	if path in loaded_textures.get(renderer, {}):
		texture = loaded_textures[renderer][path]
	else:
		texture = load_texture(renderer, path)
		if renderer not in loaded_textures:
			loaded_textures[renderer] = {}
		loaded_textures[renderer][path] = texture

	numbers = []
	names = {}
	for n, child in enumerate(root):
		if not _filter or n in _filter or child.attrib.get('n') in _filter:
			rect = pg.Rect(
				int(child.attrib['x']), int(child.attrib['y']),
				int(child.attrib['w']), int(child.attrib['h']))
			img = Image(texture, srcrect=rect)
			numbers.append(img)
			names[child.attrib.get('n')] = img

	return names if by_name else numbers


def load_texture(renderer, filename, scale=None):
	"""
	Returns an texture loaded from given image file and attached to
	given renderer.

	:param renderer: active pygame._sdl2.video.Renderer object
	:param filename: path to image file
	:rvalue: texture object
	"""
	try:
		surf = pg.image.load(str(filename))
	except Exception as e:
		raise FileNotFoundError('[Error] {}: cannot open: {}'.format(
			type(e).__name__, filename))
	if scale:
		surf = pg.transform.smoothscale(surf, (surf.get_width()*scale, surf.get_height()*scale))
	return Texture.from_surface(renderer, surf)


def load_images(
		renderer, filename, width=0, height=0, spacing=0, margin=0, by_count=False, rects=None):
	"""
	Load a texture from given image file and generate a series of
	images from it with the given width and height.

	:param renderer: renderer object for loading texture into
	:param filename: name of image file to load or xml file to process
	:param width: width of each image, or column count if by_count=True
	:param height: height of each cell, or row count if by_count=True
	:param spacing: space between each tile of the image
	:param margin: margin of empty space around edge of the image
	:param by_count: set True to use width and height value to
		calculate frame size from width and height of spritesheet
	:rvalue: list of pygame._sdl2.video.Image objects
	"""
	if filename.endswith('.xml'):
		self.fetch_xml_images(texture, filename)
	texture = load_texture(renderer, filename)
	return fetch_images(texture, width, height, spacing, margin, by_count, rects=None)

def scale_rect(rect, amount):
	"""
	Return new Rect scaled by given multiplier where 1.0 is 100%

	:param rect: the rect you want to scale
	:param amount: < 1.0 will shrink the rect, above 1.0 will enlarge it
	:rvalue Rect: new scaled Rect
	"""
	c = rect.center
	w = rect.width * amount
	h = rect.height * amount
	new = pg.Rect(0,0,w,h)
	new.center = c
	#print(f'scale={amount}, rect={rect}, new={new}')
	return new

def scale_rect_ip(rect, amount):
	"""
	Scale given rect by given multiplier where 1.0 is 100%

	:param rect: the rect you want to scale
	:param amount: < 1.0 will shrink the rect, above 1.0 will enlarge it
	:rvalue None:
	"""
	c = rect.center
	rect.width *= amount
	rect.height *= amount
	rect.center = c
	return rect

def sr(*args):
	if hasattr(sr, 'amount'):
		amount = sr.amount
	else:
		amount = args[-1]
		args = args[:-1]
	return [int(a*amount) for a in args]