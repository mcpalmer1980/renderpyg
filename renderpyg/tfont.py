'''
tfont.py: TextureFont renderer

Renders text string from a texture using the pygame._sdl2 GPU renderer

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
import pygame.gfxdraw
from pygame._sdl2 import Window, Renderer, Texture, Image
from .base import load_texture

char_map = ''' ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,?!-:'"_=+<>~@/\\|(%)'''
class TextureFont():
	'''
	Font renderer for use with pygame._sdl2
	'''
	def __init__(self, renderer, filename, size, shared=None):
		'''
		Initialize TextureFont for use with pygame._sdl2 GPU renderer

		:param renderer: pygame._sdl2.video.Renderer to draw on
		:param filename: path to a pygame.font.Font compatible file (ttf)
		:param size: point size for font
		'''
		self.renderer = renderer
		self.filename = filename

		'''
		Allow multi fonts in one texture using TextureFont.multi_font()
		'''
		if shared:
			self.cmap = shared
			self.height = size
			self.blank = shared[' ']
			return

		font = pg.font.Font(filename, size)
		self.cmap = {}
		tot = 0

		for c in char_map:
			tot += font.size(c)[0]
		if tot > 1024: # prevent overly wide textures
			width = 1024
			rows = int(tot // 1024) + 1
		else:
			width = tot
			rows = 1
		self.height = font.get_height()

		if shared:
			surface, texture, y = shared
		else:
			y = 0
			surface = pg.surface.Surface((width, font.get_height() * rows + rows), flags=pg.SRCALPHA)

		tot = x = 0
		for c in char_map:
			rend = font.render(c, 1, (255,255,255))
			wi = rend.get_width()
			if x + wi > 1024: # limit texture width
				x = 0
				y += self.height+1
			surface.blit(rend, (x, y))
			self.cmap[c] = pg.Rect(x, y, wi, self.height)
			tot += wi
			x += wi
		self.blank = self.cmap[' ']
		self.texture = Texture.from_surface(renderer, surface)

	@staticmethod
	def multi_font(renderer, fonts):
		"""
		STATIC method allows multiple fonts on a single shared texture by
		passing a list of (filename, size) tuples. Will raise an error if
		the texture height would exceed 1024

		:param renderer: pygame._sdl2.video.Renderer to draw on
		:param fonts: list of (filename, size) tuples for each font
		"""
		total_height = 0
		for filename, size in fonts: # determine height and is within limit
			font = pg.font.Font(filename, size)
			height = font.get_height()

			tot = 0
			for c in char_map:
				w = font.size(c)[0]
				tot += w
			rows = int(tot // 1024) + 1
			total_height += rows * height + rows
			if total_height > 1024:
				raise ValueError(
					'TextureFont cannot add {} to shared texture: too large'.format(
						filename))

		y = 0
		cmap = {}
		tfonts = []
		surface = pg.surface.Surface((1024, total_height), flags=pg.SRCALPHA)

		# Generate character maps and TextureFont objects
		for font, size in fonts:
			font = pg.font.Font(font, size)
			height = font.get_height()
			x = 0
			tot = 0
			cmap = {}
			for c in char_map:
				rend = font.render(c, 1, (255,255,255))
				wi = rend.get_width()
				if x+wi > 1024: # limit texture width
					x = 0
					y += height + 1
				surface.blit(rend, (x, y))
				cmap[c] = pg.Rect(x, y, wi, height)
				tot += wi
				x += wi
			y += height
			tfonts.append(TextureFont(filename, font, height, cmap))

		# Create texture and attach it to each font
		texture = Texture.from_surface(renderer, surface)
		for font in tfonts:
			font.texture = texture
		return tfonts


	def draw(self, text, x, y, color=None, alpha=None, align=False, valign=False):
		'''
		Draw text string onto pygame._sdl2 GPU renderer

		:param text: string to draw
		:param x: x coordinate to draw at
		:param y: y coordinate to draw at
		:param color: (r,g,b) color tuple
		:param alpha: alpha transparency value
		:param align: treat x as 'center' or 'right' pos (def left)
		:param valign: treat y as 'center' or 'bottom' pos (def top)
		:rvalue rect: actual area drawn into
		'''
		dest = pg.Rect(x, y, 1, self.height)
		self.texture.alpha = alpha or 255
		self.texture.color = color if color else (255,255,255,0)
		if align == 'right':
			dest.left -= self.width(text)
		elif align == 'center':
			dest.left -= self.width(text) // 2
		if valign == 'bottom':
			dest.top -= self.height
		elif valign == 'center':
			dest.top -= self.height // 2

		x, y = dest.x, dest.top
		width = 0
		for c in text:
			src = self.cmap.get(c, self.blank)
			dest.width = src.width
			self.texture.draw(srcrect=src, dstrect=dest)
			dest.x += src.width
			width += src.width
		return pg.Rect(x, y, width, self.height)

	def scale(self, text, x, y, scale, color=None, alpha=None, align=False, valign=False):
		'''
		Draw scaled text string onto pygame._sdl2 GPU renderer

		:param text: string to draw
		:param x: x coordinate to draw at
		:param y: y coordinate to draw at
		:param color: (r,g,b) color tuple
		:param alpha: alpha transparency value
		:param align: treat x as 'center' or 'right' pos (def left)
		:param valign: treat y as 'center' or 'bottom' pos (def top)
		:rvalue rect: actual area drawn into
		'''

		dest = pg.Rect(x, y, 1, self.height*scale)
		self.texture.alpha = alpha or 255
		self.texture.color = color if color else (255,255,255)
		if align == 'right':
			dest.left -= self.width(text, scale)
		elif align == 'center':
			dest.left -= self.width(text, scale) // 2
		if valign == 'bottom':
			dest.top -= self.height * scale
		elif valign == 'center':
			dest.top -= self.height * scale // 2

		#x, y = dest.x, dest.top

		width = 0
		for c in text:
			src = self.cmap.get(c, self.blank)
			dest.width = src.width*scale
			self.texture.draw(srcrect=src, dstrect=dest)
			#self.texture.renderer.draw_rect(dest)
			dest.x += src.width*scale
			width += src.width*scale
		self.get_rect(text, x, y, scale, center=False)
		return pg.Rect(x, y, width, self.height*scale)

	def get_rect(self, text, x, y, scale, center=False):
		'''
		Return rect for area of draw or scale call without drawing it

		:param text: string to draw
		:param x: x coordinate to draw at
		:param y: y coordinate to draw at
		:param scale: multiplier for text size

		:rvalue rect: actual area drawn into
		'''
		dest = pg.Rect(x, y, 1, self.height*scale)
		if center:
			dest.left -= self.width(text)*scale // 2

		x, y = dest.x, dest.top
		width = 0
		for c in text:
			src = self.cmap.get(c, self.blank)
			dest.width = src.width*scale
			dest.x += src.width*scale
			width += src.width*scale
		return pg.Rect(x, y, width, self.height*scale)

	def animate(
			self, text, x, y, color=(255,255,255), align=False, valign=False,
			duration=3000, scale=1, **kwargs):
		'''
		Draw animated text onto pygame._sdl2 GPU renderer

		:param text: text to draw
		:param x: x coordinate to draw at
		:param y: y coordinate to draw at
		:param color: base (r,g,b) color tuple to draw text
		:param align: treat x as 'center' or 'right' pos (def left)
		:param valign: treat y as 'center' or 'bottom' pos (def top)
		:param fade: amount to fade during duration
		:param duration: time in ms for complete animation cycle
		:param variance: percent to vary animation cycle between each character
		:param timer: optional start time from pygame.time.get_ticks()
			useful to differentiate multiple animations
		:param zoom: percent of size to zoom during animation cycle
		:param rotate: degrees to rotate during animation cycle
		:param colors: optional (r,g,b) amount to cycle color 
		:param move: optional x, y variance to move characters
		:param circle: optional radius to move characters (overrides move)
		:rvalue rect: rect area drawn into but animation may extrude the borders
		'''
		variance = kwargs.get('variance', 0)
		timer = kwargs.get('timer', 0)
		zoom = kwargs.get('zoom', 0)
		rotate = kwargs.get('rotate', 0)
		colors = kwargs.get('colors', False)
		movex, movey = kwargs.get('move', (0,0))
		circle = kwargs.get('circle', False)
		fade = kwargs.get('fade', 0)

		if align == 'right':
			x -= self.width(text, scale)
		elif align == 'center':
			x -= self.width(text, scale) // 2
		if valign == 'bottom':
			y -= self.height * scale
		elif valign == 'center':
			y -= self.height * scale // 2

		topleft = x, y

		ticks = pg.time.get_ticks()
		variance, change = duration * (variance/100), 0
		zoom = zoom / 100 if zoom else False
		r, g, b = color
		self.texture.color = color
		self.texture.alpha = 255
		rx, ry = x, y
		dest = pg.Rect(x, y, 1, self.height)
		for i, c in enumerate(text):
			percent = (ticks - timer + change) % duration / duration
			amount = 1 - abs(-1 + percent*2)

			if rotate:
				angle =  -rotate + (rotate*2) * amount
			else:
				angle = 0
			if colors:
				_r, _g, _b = colors
				color = (
					int(min(255, r+(_r*amount))),
					int(min(255, g+(_g*amount))),
					int(min(255, b+(_b)*amount)) )
				self.texture.color = color
			if fade:
				self.texture.alpha = 255 - amount
			
			if movex or movey:
				rx = x + (-movex + (movex*2) * amount)
				ry = y + (-movey + (movey*2) * amount)
			elif circle:
				ang = math.radians(360 * percent)
				rx = x + math.sin(ang) * circle
				ry = y + math.cos(ang) * circle
			else:
				rx = x
				ry = y

			src = self.cmap.get(c, self.blank)
			if zoom:
				sx = int((zoom * amount) * src.width)
				sy = int((zoom * amount) * self.height)
				dest.width = src.width + sx * 2
				dest.height = self.height + sy * 2
				dest.x = rx - sx
				dest.y = ry - sy
			else:
				dest.width = src.width
				dest.height = src.height
				dest.x = rx
				dest.y = ry

			dest.width *= scale
			dest.height *= scale

			origin = dest.width/2, dest.height/2
			self.texture.draw(
				srcrect=src, dstrect=dest, origin=origin, angle=angle)
			x += src.width * scale
			change += variance
		return pg.Rect(topleft[0], topleft[1], x, self.height*scale)

	def width(self, text, scale=1):
		'''
		Calculate width of given text not including motion or scaling effects

		:param text: text string to calculate width of
		:rvalue: width of string in pixels
		'''
		w = 0
		for c in text:
			w += self.cmap.get(c, self.blank).width * scale
		return w


class NinePatch():
	'''
	Nine Patch renderer for use with pygame._sdl2. Nine-patch images
	can be stretched 	to any size without warping the edge or corner
	sections.
	'''
	def __init__(self, source, borders, area=None):
		'''
		Initialize the nine patch for drawing

		:param source: texture, image, or (renderer, filename pair)
		:param borders: left, top, right, and bottom border that will
			not be stretched
		:param area: optional Rect area of texture to use, overrides
			srcrect when source Image is used
		'''
		if isinstance(source, Texture):
			self.texture = source
			area = area or source.get_rect()
		elif type(source) == Image:
			self.texture = source.texture
			area = area or source.srcrect

		elif hasattr(source, '__len__') and type(source[0]) == Renderer:
			self.texture = load_texture(source[0], source[1])
		else:
			raise ValueError(
				'Cannot parse {} as source of NinePatch'.format(source))

		self.area = pg.Rect(area)
		self.left, self.top, self.right, self.bottom = borders
		self.min_height = self.top+self.bottom+1
		self.min_width = self.left+self.right+1
		self.message = ''

	def draw(self, dstrect, hollow=False, color=None):
		'''
		Draw the ninepatch into target rect

		:param target: rect area to draw nine patch into
		:param hollow: center patch not drawn when set True
		:rvalue None:
		'''
		target = pg.Rect(dstrect)

		target.width = max(target.width, self.min_width)
		target.height = max(target.height, self.min_height)
		bounds = self.area
		texture = self.texture
		if color:
			texture.color, color = color, texture.color

		texture.draw( # TOP
			srcrect=(bounds.left, bounds.top, self.left, self.top),
			dstrect=(target.left, target.top, self.left, self.top) )	
		texture.draw( # LEFT
			srcrect=(bounds.left, bounds.top+self.top, self.left,
					bounds.height-self.top-self.bottom),
			dstrect=(target.left, target.top+self.top, self.left,
					target.height-self.top-self.bottom) )
		texture.draw( # BOTTOM-LEFT
			srcrect=(bounds.left, bounds.bottom-self.bottom,
					self.left, self.bottom),
			dstrect=(target.left, target.bottom-self.bottom,
					self.left, self.bottom) )	

		texture.draw( # TOP-RIGHT
			srcrect=(bounds.right-self.right, bounds.top,
					self.right, self.top),
			dstrect=(target.right-self.right, target.top,
					self.right, self.top) )		
		texture.draw( # RIGHT
			srcrect=(bounds.right-self.right, bounds.top+self.top,
					self.right,bounds.height-self.bottom-self.top),
			dstrect=(target.right-self.right, target.top+self.top,
					self.right, target.height-self.bottom-self.top) )
		texture.draw( # BOTTOM-RIGHT
			srcrect=(bounds.right-self.right, bounds.bottom-self.bottom,
					self.right, self.bottom),
			dstrect=(target.right-self.right, target.bottom-self.bottom,
					self.right, self.bottom) ) 
		'''
		texture.draw( # CENTER
			srcrect=(bounds.left+self.left, bounds.top+self.top,
					bounds.width-self.right-self.left,
					bounds.height-self.top-self.bottom),
			dstrect=(target.left+self.left, target.top+self.top,
					target.width-self.right-self.left,
					target.height-self.top-self.bottom) )	'''
		texture.draw( # TOP
			srcrect=(bounds.left+self.left, bounds.top,
					bounds.width-self.left-self.right, self.top),
			dstrect=(target.left+self.left, target.top,
					target.width-self.left-self.right, self.top) )
		texture.draw( # CENTER
			srcrect=(bounds.left+self.left, bounds.top+self.top,
					bounds.width-self.right-self.left,
					bounds.height-self.top-self.bottom),
			dstrect=(target.left+self.left, target.top+self.top,
					target.width-self.right-self.left,
					target.height-self.top-self.bottom) )
		texture.draw( # BOTTOM
			srcrect=(bounds.left+self.left, bounds.bottom-self.bottom,
					bounds.width-self.left-self.right, self.bottom),
			dstrect=(target.left+self.left, target.bottom-self.bottom,
					target.width-self.left-self.right, self.bottom) )		
		if color:
			texture.color = color
		return target

	def get_rect(self):
		return self.area

	def slider(self, target, amount, other, color=None):
		self.draw(target, color=color)
		return other.partial(target, amount, color)


	def partial(self, target, amount, color=None):
		target = pg.Rect(target)
		target.width = max(target.width, self.left+self.right+1)
		target.height = max(target.height, self.top+self.bottom+1)
		bounds = self.area
		texture = self.texture

		ssplit = int(self.area.width * amount)
		tsplit = int(target.width * amount)
		if color:
			texture.color, color = color, texture.color

		if tsplit < self.left:
			texture.draw(
				srcrect=(bounds.left+tsplit, bounds.top,
					self.left - tsplit, self.top),
				dstrect=(target.left+tsplit, target.top,
					self.left - tsplit, self.top) )
			texture.draw(
				srcrect=(bounds.left+tsplit, bounds.bottom-self.bottom,
					self.left - tsplit, self.bottom),
				dstrect=(target.left+tsplit, target.bottom-self.bottom,
					self.left - tsplit, self.bottom) )
			texture.draw(
				srcrect=(bounds.left+tsplit, bounds.top+self.top,
					self.left - tsplit, bounds.height-self.top-self.bottom),
				dstrect=(target.left+tsplit, target.top+self.top,
					self.left - tsplit, target.height-self.top-self.bottom) )

		if tsplit < target.width - self.right:
			tstart = max(tsplit, self.left)
			sstart = max(ssplit, self.left)
			texture.draw(
				srcrect=(bounds.left+sstart, bounds.top+self.top,
						bounds.width-self.right-sstart,
						bounds.height-self.top-self.bottom),
				dstrect=(target.left+tstart, target.top+self.top,
						target.width-self.right-tstart,
						target.height-self.top-self.bottom) )
			texture.draw(
				srcrect=(bounds.left+sstart, bounds.bottom-self.bottom,
						bounds.width-self.right-sstart, self.bottom),
				dstrect=(target.left+tstart, target.bottom-self.bottom,
						target.width-self.right-tstart, self.bottom) )		

			texture.draw(
				srcrect=(bounds.left+sstart, bounds.top,
						bounds.width-self.right-sstart, self.top),
				dstrect=(target.left+tstart, target.top,
						target.width-self.right-tstart, self.top) )

		tstart = max(target.right-self.right, target.left + tsplit)
		sstart = max(bounds.right-self.right, bounds.right - (target.width-tsplit))
		texture.draw(
			srcrect=(sstart, bounds.top,
					bounds.right-sstart, self.top),
			dstrect=(tstart, target.top,
					target.right-tstart, self.top) )

		texture.draw(
			srcrect=(sstart, bounds.top+self.top,
					bounds.right-sstart,bounds.height-self.bottom-self.top),
			dstrect=(tstart, target.top+self.top,
					target.right-tstart, target.height-self.bottom-self.top) )
		texture.draw(
			srcrect=(sstart, bounds.bottom-self.bottom,
					bounds.right-sstart, self.bottom),
			dstrect=(tstart, target.bottom-self.bottom,
					target.right-tstart, self.bottom) )
		if color:
			texture.color = color
		return target


	def surround(self, target, padding=0, pady=0, hollow=False, draw=True):
		"""
		Surround given rect with optional padding

		:param target: rect or 4-tupple to surround with ninepatch
		:param padding: int of extra space around the rect
		:rvale rect: the full area drawn
		"""
		try:
			padx, pady = padding
		except:
			padx = pady = padding
		rect = pg.Rect(target)
		rect.x -= self.left + padx
		rect.width += self.left + self.right + padx * 2
		rect.y -= self.top + pady
		rect.height += self.top + self.bottom + pady * 2
		if draw:
			self.draw(rect, hollow)
		return rect

def round_patch2(renderer, radius, color, sizes, colors):
	layers = list(zip(sizes, colors))
	full_radius = radius + sum(sizes[:len(layers)])
	surf = pg.Surface((full_radius*3, full_radius*3), pg.SRCALPHA)
	c_rad = full_radius
	
	r = pg.Rect(0,0,full_radius*3, full_radius*3)
	for size, _color in layers:
		print(c_rad)
		round_rect(surf, _color, r, radius)
		r.inflate_ip(-size, -size)
		c_rad -= size
	print(c_rad)
	round_rect(surf, color, r, radius)
	
	return NinePatch(Texture.from_surface(renderer, surf), (full_radius,)*4)

def round_patch(renderer, radius, color, sizes, colors):
	'''
	Generate a NinePatch object using a set of rounded rectangles of various
	thickness allowing multiple outlines of different colors.

	:param renderer: pygame._sdl2.video.Renderer to draw on
	:param radius: radius of circular edges of the rounded rectangles
	:param color: 3-tuple or color object for the central area
	:param sizes: list of int sizes of outline layers starting from the outside
	:param colors: list of 3-tuples or color objects for each outline layer
		starting from the outside
	'''
	layers = list(zip(sizes, colors))
	full_radius = radius + sum(sizes[:len(layers)])
	surf = pg.Surface((full_radius*3, full_radius*3), pg.SRCALPHA)
	c_rad = full_radius
	
	r = pg.Rect(0,0,full_radius*3, full_radius*3)
	for size, _color in layers:
		print(c_rad)
		pg.draw.rect(surf, _color, r,
			border_radius=radius)
		r.inflate_ip(-size, -size)
		c_rad -= size
	print(c_rad)
	pg.draw.rect(surf, color, r,
		border_radius=radius)
	
	return NinePatch(Texture.from_surface(renderer, surf), (full_radius,)*4)


def round_rect(surf, color, rect, rad, thick=0):
	trans = (255,255,1)
	if not rad:
		pg.draw.rect(surf, color, rect, thick)
		return
	elif rad > rect.width / 2 or rad > rect.height / 2:
		rad = min(rect.width/2, rect.height/2)

	if thick > 0:
		r = rect.copy()
		x, r.x = r.x, 0
		y, r.y = r.y, 0
		buf = pg.surface.Surface((rect.width, rect.height)).convert()
		buf.set_colorkey(trans)
		buf.fill(trans)
		round_rect(buf, r, rad, color, 0)
		r = r.inflate(-thick*2, -thick*2)
		round_rect(buf, r, rad, trans, 0)
		surf.blit(buf, (x,y))


	else:
		r  = rect.inflate(-rad * 2, -rad * 2)
		for corn in (r.topleft, r.topright, r.bottomleft, r.bottomright):
			pg.draw.circle(surf, color, corn, rad)
			#pg.gfxdraw.filled_circle(surf, *corn, rad, color)
			#pg.gfxdraw.aacircle(surf, *corn, rad, color)

		pg.draw.rect(surf, color, r.inflate(rad*2, 0))
		pg.draw.rect(surf, color, r.inflate(0, rad*2))


