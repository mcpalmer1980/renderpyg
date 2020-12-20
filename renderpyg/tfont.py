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
from pygame._sdl2 import Window, Renderer, Texture, Image
from .base import load_texture

char_map = ''' ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,?!-:'"=+<>~@/\\|'''
class TextureFont():
	'''
	Font renderer for use with pygame._sdl2
	'''
	def __init__(self, renderer, filename, size):
		'''
		Initialize TextureFont for use with pygame._sdl2 GPU renderer

		:param renderer: pygame._sdl2.video.Renderer to draw on
		:param filename: path to a pygame.font.Font compatible file (ttf)
		:param size: point size for font
		'''
		font = pg.font.Font(filename, size)
		self.cmap = {}
		self.renderer = renderer
		self.height = font.get_height()
		tot = 0
		for c in char_map:
			tot += font.size(c)[0]
		surf = pg.surface.Surface((tot, font.get_height()), flags=pg.SRCALPHA)
		self.height = font.get_height()
		tot = 0
		for c in char_map:
			rend = font.render(c, 1, (255,255,255))
			wi = rend.get_width()
			surf.blit(rend, (tot, 0))
			self.cmap[c] = pg.Rect(tot, 0, wi, self.height)
			tot += wi
		self.blank = self.cmap[' ']
		self.texture = Texture.from_surface(renderer, surf)

	def draw(self, text, x, y, color=None, alpha=None, center=False):
		'''
		Draw text string onto pygame._sdl2 GPU renderer

		:param text: string to draw
		:param x: x coordinate to draw at
		:param y: y coordinate to draw at
		:param color: (r,g,b) color tuple
		:param alpha: alpha transparency value
		:param center: treat x,y coordinate as center position
		'''
		dest = pg.Rect(x, y, 1, self.height)
		self.texture.alpha = alpha or 255
		self.texture.color = color if color else (255,255,255,0)
		if center:
			dest.left -= self.width(text) // 2
			dest.top -= self.height // 2
		for c in text:
			src = self.cmap.get(c, self.blank)
			dest.width = src.width
			self.texture.draw(srcrect=src, dstrect=dest)
			dest.x += src.width
	
	def animate(self, text, x, y, color=(255,255,255), center=False, duration=3000, **kwargs):
		'''
		Draw animated text onto pygame._sdl2 GPU renderer

		:param text: text to draw
		:param x: x coordinate to draw at
		:param y: y coordinate to draw at
		:param color: base (r,g,b) color tuple to draw text
		:param fade: amount to fade during duration
		:param duration: time in ms for complete animation cycle
		:param variance: percent to vary animation cycle between each character
		:param timer: optional start time from pygame.time.get_ticks()
			useful to differentiate multiple animations
		:param scale: percent of size to scale during animation cycle
		:param rotate: degrees to rotate during animation cycle
		:param colors: optional (r,g,b) amount to cycle color 
		:param move: optional x, y variance to move characters
		:param circle: optional radius to move characters (overrides move)
		'''
		variance = kwargs.get('variance', 0)
		timer = kwargs.get('timer', 0)
		scale = kwargs.get('scale', 0)
		rotate = kwargs.get('rotate', 0)
		colors = kwargs.get('colors', False)
		movex, movey = kwargs.get('move', (0,0))
		circle = kwargs.get('circle', False)
		fade = kwargs.get('fade', 0)

		if center:
			x = x - (self.width(text) / 2)

		ticks = pg.time.get_ticks()
		variance, change = duration * (variance/100), 0
		scale = scale / 100 if scale else False
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
			if scale:
				sx = int((scale * amount) * src.width)
				sy = int((scale * amount) * self.height)
				dest.width = src.width + sx * 2
				dest.height = self.height + sy * 2
				dest.x = rx - sx
				dest.y = ry - sy
			else:
				dest.width = src.width
				dest.x = rx
				dest.y = ry
			origin = dest.width/2, dest.height/2
			self.texture.draw(
				srcrect=src, dstrect=dest, origin=origin, angle=angle)
			x += src.width
			change += variance

	def width(self, text):
		'''
		Calculate width of given text not including motion or scaling effects

		:param text: text string to calculate width of
		:rvalue: width of string in pixels
		'''
		w = 0
		for c in text:
			w += self.cmap.get(c, self.blank).width
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
		if type(source) == Texture:
			self.texture = source
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

	def draw(self, target):
		'''
		Draw the ninepatch into target rect

		:param target: rect area to draw nine patch into
		:rvalue None:
		'''
		if not isinstance(target, pg.Rect):
			target = pg.Rect(target)
		target.width = max(target.width, self.left+self.right+1)
		target.height = max(target.height, self.top+self.bottom+1)
		bounds = self.area
		texture = self.texture
		
		texture.draw(
			srcrect=(bounds.left, bounds.top, self.left, self.top),
			dstrect=(target.left, target.top, self.left, self.top) )	
		texture.draw(
			srcrect=(bounds.left+self.left, bounds.top,
					bounds.width-self.left-self.right, self.top),
			dstrect=(target.left+self.left, target.top,
					target.width-self.left-self.right, self.top) )		
		texture.draw(
			srcrect=(bounds.right-self.right, bounds.top,
					self.right, self.top),
			dstrect=(target.right-self.right, target.top,
					self.right, self.top) )				
		texture.draw(
			srcrect=(bounds.left, bounds.top+self.top, self.left,
					bounds.height-self.top-self.bottom),
			dstrect=(target.left, target.top+self.top, self.left,
					target.height-self.top-self.bottom) )		
		texture.draw(
			srcrect=(bounds.left+self.left, bounds.top+self.top,
					bounds.width-self.right-self.left,
					bounds.height-self.top-self.bottom),
			dstrect=(target.left+self.left, target.top+self.top,
					target.width-self.right-self.left,
					target.height-self.top-self.bottom) )		
		texture.draw(
			srcrect=(bounds.right-self.right, bounds.top+self.top,
					self.right,bounds.height-self.bottom-self.top),
			dstrect=(target.right-self.right, target.top+self.top,
					self.right, target.height-self.bottom-self.top) )		
		texture.draw(
			srcrect=(bounds.left, bounds.bottom-self.bottom,
					self.left, self.bottom),
			dstrect=(target.left, target.bottom-self.bottom,
					self.left, self.bottom) )		
		texture.draw(
			srcrect=(bounds.left+self.left, bounds.bottom-self.bottom,
					bounds.width-self.left-self.right, self.bottom),
			dstrect=(target.left+self.left, target.bottom-self.bottom,
					target.width-self.left-self.right, self.bottom) )		
		texture.draw(
			srcrect=(bounds.right-self.right, bounds.bottom-self.bottom,
					self.right, self.bottom),
			dstrect=(target.right-self.right, target.bottom-self.bottom,
					self.right, self.bottom) )



