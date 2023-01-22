'''
menu.py: menu system renderer

Displays simple menus with pygame2 GPU renderer and returns the
results

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
import os, pygame as pg
from pygame._sdl2.video import Window, Renderer, Texture, Image
from .tfont import NinePatch, TextureFont, char_map
from .base import load_texture, scale_rect, fetch_images
from .tilemap import tile_background
from collections import OrderedDict
AXIS_MOD = 2 ** 15

class Menu:
	buffer = None
	"""
	Simple menuing system for use with pygame2 GPU renderer
	"""
	def __init__(self, target, font, **kwargs):
		"""
		REQUIRED
		:param target: renderer to draw menu into
		:param font: default font to use

		OPTIONAL
		:param anim: dict of parameters for animated text as used in
			TextureFont.animate() method
		:param background: optional Image, color, or callable for background
			callables should be a 3-tuple (func, args, kwargs)
		:param color: (r,g,b) color for default font
		:param joystick: (joystick, but_select, but_cancel)
		:param label: (r,g,b) color for label font used in option menu
		:param patch: NinePatch object to wrap around menu defaults blank
		:param title_offset: offset to draw title in upper area of patch
		:param frame: draw solid frame in lue of patch, using
			(outline color, fill color, outline thickness)

		:param position: position of menu defaults to center  
			uses numbers 1-9, with 1 at top-left corner and 9 at bottom right
			set to 'mouse' to center around mouse position
		:param scale: scaling multiplier for default font
		:param spacing: vertical spacing between menu items

		:param box: NinePatch object for text input and sliders, or 
			(outline color, fill color, outline thickness)
		:param box_fill: color for text or slider fill
		:param bot_textc: color for text when using NinePatch for box

		:param but_padding: (x, y) padding for but_patch drawing
		:param but_patch: NinePatch object for buttons and selected
			item in select menus

		:param opt_left: image for left arrow in option list menus  
			also used for page icons in multipage select menus
		:param opt_right: image for right arrow in option list menus  
			also used for page icons in multipage select menus

		:param press_color: color modifier for patch of selected button
		:param press_patch: NinePatch for selected button
			overrides press_color 

		:param sel_anim: dict of parameters for animating selected item
			as used in TextureFont.animate() method
		:param sel_color: font color for selected item
		:param sel_stretch: stretch button patch for selected item
			across entire select menu
		:param sel_left: int space at left of selected items, or Image
			to draw left of selected item (also effects spacing)
		:param sel_right: int space at right of selected items, or Image
			to draw right of selected item (also effects spacing)

		:param sound: sound played when new item is selected
			may be a pygame.Sound object or a 3-Tuple (func, args, kwargs)
		:param sound_bad: sound played when input error occurs
		:param sound_key: sound played when key pressed during text input

		:param text_anim: dict of parameters for animating dialog text
			as used in TextureFont.animate() method
		:param text_font: optional font for dialog text
		:param text_scale: scaling multiplier for dialog text

		:param title_anim: dict of parameters for animating menu titles
			as used in TextureFont.animate() method
		:param title_color: color of title text
		:param title_font: optional font for title
		:param title_scale: scaling multiplier for title text

		Create a menu object that can create lists, dialogs, text inputs
		and option menus. 

		Add a tab to the begining of an option string to align left or right
		"""
		self.target = target
		self.font = font
		self.anim = kwargs.get('anim')
		background = kwargs.get('background')
		self.clock = kwargs.get('clock', pg.time.Clock())
		self.color = kwargs.get('color', (255,255,255))
		self.joystick = kwargs.get('joystick', None)
		self.label = kwargs.get('label', self.color)
		self.patch = kwargs.get('patch', None)
		self.position = kwargs.get('position', 5)
		self.reg_scale = kwargs.get('scale', 1)
		self.spacing = kwargs.get('spacing', 0)
		self.spacingx = kwargs.get('spacing_x', self.spacing)
		self.frame = kwargs.get('frame', None)

		self.box = kwargs.get('box', ((255,255,255), (0,0,0),  8))
		self.box_fill = kwargs.get('box_fill', self.box)
		self.box_textc = kwargs.get('box_textc', self.color)

		self.but_padding = kwargs.get('but_padding', (0,0))
		self.but_patch = kwargs.get('but_patch')

		self.opt_left = kwargs.get('opt_left')
		self.opt_right = kwargs.get('opt_right')

		self.press_color = kwargs.get('press_color', (200,200,200))
		self.press_patch = kwargs.get('press_patch')

		self.sel_anim = kwargs.get('sel_anim', self.anim)
		self.sel_color = kwargs.get('sel_color', (255,255,0))
		left = kwargs.get('sel_left', 0)
		right = kwargs.get('sel_right', 0)
		self.sel_patch = kwargs.get('sel_patch')
		self.sel_stretch = kwargs.get('sel_stretch')

		self.sound = kwargs.get('sound')
		self.sound_bad = kwargs.get('sound_bad')
		self.sound_key = kwargs.get('sound_key')

		self.text_font = kwargs.get('text_font', self.font)
		self.text_scale = kwargs.get('text_scale', 1)
		self.text_anim = kwargs.get('text_anim')

		self.title_anim = kwargs.get('title_anim')
		self.title_scale = kwargs.get('title_scale', 1.25)
		self.title_color = kwargs.get('title_color', self.color)
		self.title_font = kwargs.get('title_font', self.font)
		self.title_offset = kwargs.get('title_offset', 0)
		self.alpha = kwargs.get('alpha', 255)

		buffer = kwargs.get('buffer', None)
		if buffer:
			Menu.buffer = buffer
		elif not Menu.buffer:
			Menu.buffer = Texture(target, target.get_viewport().size, target=True)
		
		if hasattr(left, 'get_rect'):
			self.left = left
			self.l_space = left.get_rect().width
		else:
			self.l_space=left
			self.left = None
		if hasattr(right, 'get_rect'):
			self.right = right
			self.r_space = left.get_rect().width
		else:
			self.r_space = right
			self.right = None

		if self.frame:
			outline = self.frame[2] * 2
			self.r_space += outline
			self.l_space += outline

		self.area = pg.Rect(0,0,1,1)
		self.viewport = target.get_viewport()
		self.window = kwargs.get('window', self.viewport)

		self.editing = 0
		self.selected = self.bselected = 0
		self.joy_pressed = False
		self.alive = False
		self.but_rects = []
		self.set_background(background)

	def _draw_frame(self):
		color, outline, thick = self.frame
		self.target.draw_color = outline + (100,)
		self.target.fill_rect(self.area.inflate(thick*2, thick*2))
		self.target.draw_color = 100,0,0,100
		self.target.fill_rect(self.area)

	def _break_text_lines(self, text, width, max_height):
		final_lines = []
		font = self.text_font
		scale = self.text_scale
		requested_lines = text.splitlines()

		# Create a series of lines that will fit on the provided
		# rectangle.
	
		for requested_line in requested_lines:
			if font.width(requested_line, scale) > width:
				words = requested_line.split(' ')
				#for word in words:
					#if font.width(word, scale) >= width:
					#	raise Exception	(
					#		"The word " + word + 
					#		" is too long to fit in the rect passed.")

				# Start a new line
				accumulated_line = ""
				for word in words:
					if font.width(word, scale) >= width:
						for i, _ in enumerate(word):
							if font.width('...'+word[i:], scale) < width:
								word = '...' + word[i:]
								break

					test_line = accumulated_line + word + " "
					# Build the line while the words fit.
					if font.width(test_line, scale) < width:
						accumulated_line = test_line
					else:
						final_lines.append(accumulated_line)
						accumulated_line = word + " "
				final_lines.append(accumulated_line)
			else:
				final_lines.append(requested_line)

		if len(final_lines) * font.height * scale > max_height:
			max_lines = int(max_height / (font.height * scale))
			final_lines = final_lines[:max_lines]
			'''
			Quietly truncating long text for now

			print(f'long text was trimmed:', final_lines[0])
			raise Exception	("The text is to long to fit in text area.")'''		
		self.lines = final_lines
		return

	def _change_option(self, direct):
		if not self.changeable:
			self._play_sound('bad')
			return
		self._play_sound()
		option = self.changeable

		r = self.rects[self.selected]
		pos = self._get_mouse_pos()
		if option.get('type') == 'OPTION':
			if pg.mouse.get_pressed()[0] and r.collidepoint(pos):
				x = pos[0] - r.left
				direct = 1 if x > r.width / 2 else -1

			sel = option['selected'] + direct
			options = option.get('options', ('',))
			option['selected'] = int(sel % len(options))
			option['value'] = option['options'][option['selected']]
			return option['value']
		elif option.get('type') == 'SLIDER':
			if pg.mouse.get_pressed()[0] and r.collidepoint(pos):
				x = pos[0] - r.left
				f = x / r.width
				v = option['min'] + (option['max'] - option['min']) * f
			else:
				v = option['value'] + option['step'] * direct
			high, low = option['max'], option['min']
			option['value'] = round(min(max(round(v), low), high))
			return option['value']

	def _draw_box(self, x, y):
		rect = pg.Rect(x+self.spacingx, y,
				self.area.width-self.spacingx*2 -self.spacingx,
				self.font.height*self.reg_scale)
		if isinstance(self.box, NinePatch):
			rect.height += self.but_padding[1]
			self.box.draw(rect)
			return (rect, rect.left + self.but_padding[0] / 2,
					rect.width - self.but_padding[0])
		else:
			outer, inner, thick = self.box
			rect.height += thick * 2
			self.target.draw_color = outer + (255,)
			self.target.fill_rect(rect)
			self.target.draw_color = inner + (255,)
			self.target.fill_rect(rect.inflate(-thick, -thick))
			return rect, rect.x + thick * 2, rect.width - thick * 4

	def _draw_buttons(self):
		right, left, mid, *_ = self.buttons + (None, None, None)
		self.but_rects = []

		if right:
			self.but_rects.append(self._draw_button(right, 0))
		if left:
			self.but_rects.append(self._draw_button(left, 1))
		if mid:
			self.but_rects.append(self._draw_button(mid, 2))

	def _draw_button(self, text, which):
		r = self.font.get_rect(
			text, 0,0, self.reg_scale).inflate((self.but_padding))
		if self.but_patch:
			r.height = max(r.height, self.but_patch.min_height)

		if which == 0:
			r.right = self.area.right - self.spacingx
		elif which == 1:
			r.left = self.area.left + self.spacingx
		elif which == 2:
			r.centerx = self.area.centerx

		if len(self.rects) > 0 and self.selected != len(self.rects) :
			which = -1 # hide selection when button row not selected

		text_color = self.sel_color if self.bselected == which else self.color
		press_color = self.press_color if self.bselected == which else None
		anim = self.sel_anim if self.bselected == which else self.anim

		r.bottom = self.area.bottom
		if self.but_patch:
			self.but_patch.draw(r, False, press_color) #press_color)

		if anim:
			self.font.animate(
				text, r.centerx, r.centery, text_color, scale=self.reg_scale,
				align='center', valign='center', **anim)
		else:
			self.font.scale(
				text, r.centerx, r.centery, self.reg_scale,
				text_color, align='center', valign='center')
		return r

	def _draw_dialog(self):
		self._draw_background()
		if self.patch:
			self.patch.texture.alpha = self.alpha
			self.patch.surround(self.area)
		elif self.frame:
			self._draw_frame()
		self.rects = []
		scale = self.text_scale
		height = self.text_font.height * scale

		y = self._draw_title()
		x = self.area.left + self.spacingx

		if self.text_anim:
			for line in self.lines:
				self.text_font.animate(line, x, y, scale=scale, **self.text_anim)
				y += height
		else:
			for line in self.lines:
				self.text_font.scale(line, x, y, scale)
				y += height
		self._draw_buttons()

	def _draw_input(self):
		self._draw_background()
		if self.patch:
			self.patch.texture.alpha = self.alpha
			self.patch.surround(self.area)
		elif self.frame:
			self._draw_frame()
		x = self.area.centerx
		y = self._draw_title()
		self.rects = []
		
		r, x, max_width = self._draw_box(self.area.left, y)
		y = r.centery
		text = self.textinput or ''
		for part in range(len(self.textinput)):
			if self.font.width(self.textinput[part:], self.reg_scale) < max_width:
				text = self.textinput[part:]
				break
		if self.editing % 15 < 10:
			if self.cur_char:
				text += char_map[self.cur_char % len(char_map)]
			else: text += '?'
		self.font.scale(text,x, y, self.reg_scale, self.box_textc, valign='center')

		if self.buttons: 
			self._draw_buttons()

	def _draw_slider(self, y, option, i):
		if self.selected == i:
			if isinstance(self.box, NinePatch) and self.sel_patch:
				pass
				#y += self.but_padding[1] // 2
			self.changeable = option
			color = self.sel_color
		else:
			color = self.color

		label = option.get('label', '') + ' '
		rect = self.font.get_rect(
				label, self.area.x + self.l_space, y, self.reg_scale)
		_range = option['max'] - option['min']
		value = (option['value'] - option['min']) / _range

		if isinstance(self.box, NinePatch):
			rect.width = self.area.right - rect.right - self.r_space - self.spacingx
			rect.right = self.area.right - self.r_space - self.spacingx
			if self.selected == i and self.sel_patch:
				pass
				#rect.inflate_ip(0, self.but_padding[1])			
			self.rects.append(rect.copy())
			color = self.press_color if self.selected == i else None
			
			if self.box_fill.get_rect().width < self.box.get_rect().width:
				# draw with cursor
				rect = self.box.draw(rect)
				r = self.box_fill.get_rect()
				r.center = rect.left + rect.width * value, rect.centery
				self.box_fill.draw(dstrect=r)
			else:
				rect = self.box.slider(rect, value, self.box_fill, color=color)

			where = rect.centerx + self.but_padding[0] // 2
			scale = (rect.height - self.but_padding[1]) / self.font.height
			self.font.scale(
				str(option['value']), rect.centerx, rect.centery,
				scale, color=self.box_textc, align='center', valign='center')

		else:
			rect.width = self.area.right - rect.right - self.spacingx * 2
			rect.right = self.area.right - self.spacingx
			self.rects.append(rect.copy())
			self._draw_box_slider(option, rect, value)

		if self.selected == i:
			if self.left: # draw selection buttons
				r = self.left.get_rect()
				r.left = self.area.left
				r.centery = rect.centery
				self.left.draw(dstrect=r)
			if self.right:
				r = self.right.get_rect()
				r.right = self.area.right
				r.centery = rect.centery
				self.left.draw(dstrect=r)
		self.font.scale(
				label, self.area.x + self.l_space, rect.centery, self.reg_scale,
				color=color, valign='center')

		return rect.height

	def _draw_box_slider(self, option, rect, value):
		outer, inner, thick = self.box
		rect.inflate(thick*2, thick*2)
		self.target.draw_color = outer + (255,)
		self.target.fill_rect(rect)
		self.target.draw_color = inner + (255,)
		r = rect.inflate(-thick, -thick)
		thick *= 2
		right = r.right
		r.width = r.width - (r.width * value)
		r.right = right
		self.target.fill_rect(r)

		if (self.font.width(str	(option['value']),scale=self.reg_scale)
				+ thick < rect.width * value):
			where = rect.left + thick
			self.font.scale(
				str(option['value']), where, rect.centery,
				self.reg_scale, color=inner, valign='center')
		else:
			where = rect.left + rect.width * value + thick
			self.font.scale(
				str(option['value']), where, rect.centery,
				scale=self.reg_scale, color=outer, valign='center')


	def _draw_option(self, x, y, option, i):
		_type = option['type']

		if _type == 'LABEL':
			w = (self.area.right - self.r_space) - (self.area.left + self.l_space)
			x = self.area.left + self.l_space + w//2

			text, _, split  = option['text'].partition('\t')
			if split:
				x = self.area.left + self.l_space
				where = 'left'
			else:
				x = self.area.left + self.l_space + w // 2
				where = 'center'

			scale = option.get('size', self.reg_scale)
			color = option.get('color', self.label)
			if self.anim:
				height = self.font.animate(
					text, x, y, scale, color=color,
					align=where, **self.anim).height
			else:
				height = self.font.scale(
					text, x, y, scale, color=color,
					align=where).height
			
			if split:
				x = self.area.right - self.r_space
				if self.anim:
					return self.font.animate(
						split, x, y, scale, color=color,
						align='right', **self.anim).height
				else:
					return self.font.scale(
						split, x, y, scale, color=color,
						align='right').height
			return height


		elif _type == 'SPACER':
			return option['amount'] * self.font.height * self.reg_scale

		elif _type == 'ITEM':
			text = option['text']
			rect = self.font.get_rect(text, x, y, self.reg_scale, True)

			if self.sel_patch and self.selected == i:
				drect = rect.inflate(*self.but_padding)
			else:
				drect = rect
			stretched = rect.copy()
			stretched.x = self.area.x + self.l_space
			stretched.width = self.area.width - self.l_space - self.r_space
			self.rects.append(stretched)

			text, _, split  = option['text'].partition('\t')
			if self.selected == i:
				if self.left: # draw selection buttons
					r = self.left.get_rect()
					r.left = self.area.left
					r.centery = rect.centery
					self.left.alpha = self.alpha
					self.left.draw(dstrect=r)
				if self.right:
					r = self.right.get_rect()
					r.right = self.area.right
					r.centery = rect.centery
					self.right.alpha = self.alpha
					self.right.draw(dstrect=r)

				self.rvalue = len(self.rects), text
				if self.sel_patch:
					if self.sel_stretch or split:
						rect = stretched
					self.sel_patch.texture.alpha = self.alpha
					self.sel_patch.draw(drect)
				color = self.sel_color
			else:
				color = self.color

			if split:
				x = self.area.left + self.l_space
				where = 'left'
			else:
				x = stretched.centerx #self.area.left + self.l_space + w // 2
				where = 'center'

			if self.anim:
				self.font.animate(
					text, x, y, scale=self.reg_scale, align=where,
					color=color, **self.anim).height
			else:
				self.font.scale(
					text, x, y, scale=self.reg_scale, align=where,
					color=color).height
			if split:
				x = self.area.right - self.r_space
				if self.anim:
					self.font.animate(
						split, x, y, scale=self.reg_scale, align='right',
						color=color, **self.anim).height
				else:
					self.font.scale(
						split, x, y, scale=self.reg_scale, align='right',
						color=color).height

			return rect.height

		
		elif _type == 'OPTION':
			sel = option.get('selected', 0)
			pre, post = option.get('pre', ''), option.get('post', '')
			options = option.get('options',('',))
			text = pre + options[sel] + post
			rect = self.font.get_rect(text, x, y, self.reg_scale, True)
			irect = rect.inflate(*self.but_padding)
			
			if self.sel_patch and self.selected == i:
				#y += self.but_padding[1] // 2
				drect = irect
				
			else:
				drect = rect

			stretched = rect.copy()
			stretched.x = self.area.x + self.l_space
			stretched.width = self.area.width - self.l_space - self.r_space
			self.rects.append(stretched)
			left = stretched.left
			right = stretched.right

			if self.opt_left and self.opt_right:
				r = self.opt_left.get_rect().fit(rect)
				r.centery = rect.centery
				r.left = self.area.left + self.l_space + self.spacingx
				left = r.right + self.spacingx
				self.opt_left.alpha = self.alpha
				self.opt_left.draw(dstrect=r)
				r.right = self.area.right - self.r_space - self.spacingx
				right = r.left - self.spacingx
				self.opt_right.alpha = self.alpha
				self.opt_right.draw(dstrect=r)

			if pre.endswith('\t'):
				pre = pre[:-1]
				text = pre
				x = left
				where = 'left'
				split = True
				stretched = stretched.copy()
				stretched.x = left
				stretched.w = right - left
			else:
				x = stretched.centerx
				where = 'center'
				split = False

			if self.selected == i:
				self.rvalue = len(self.rects), text
				self.changeable = option
				if self.sel_patch:
					if split or (self.sel_stretch and not self.opt_left
							and not self.opt_right):
						drect = stretched
					self.sel_patch.draw(drect)
				color = self.sel_color
				if self.left:
					r = self.left.get_rect()
					r.centery = rect.centery
					r.left = self.area.left
					self.left.draw(dstrect=r)	
				if self.right:
					r = self.right.get_rect()
					r.centery = rect.centery
					r.right = self.area.right
					self.right.draw(dstrect=r)
			else:
				color = self.color
			
			if self.anim:
				height = self.font.animate(
					text, x, y, scale=self.reg_scale, color=color,
					align=where, **self.anim).height
			else:
				height = self.font.scale(
					text, x, y, self.reg_scale, color = color,
					align=where).height
			if split:
				text = options[sel]
				if self.anim:
					height = self.font.animate(
						text, right, y, scale=self.reg_scale, color=color,
						align='right', **self.anim).height
				else:
					height = self.font.scale(
						text, right, y, self.reg_scale, color = color,
						align='right').height

			height = rect.height
			if self.opt_left:
				height = max(height, self.opt_left.get_rect().height)
				height = rect.height # FIX disabled pre fit icons
			return height

		elif _type == 'SLIDER':
			return self._draw_slider(y, option, i)
		return 0
	
	def _draw_options(self, options):
		self.changeable = False
		self.rects = []
		self._draw_background()
		if self.patch:
			self.patch.texture.alpha = self.alpha
			self.patch.surround(self.area)
		elif self.frame:
			self._draw_frame()
		#if self.sel_patch:
		#	self.sel_patch.texture.alpha = self.alpha
		x = self.area.centerx
		y = self._draw_title()

		i = 0
		for option in options.values():
			y += self._draw_option(
				x, y, option, i) + self.spacing
			if option['type'] in ('ITEM', 'OPTION', 'SLIDER'):
				i += 1
		if self.buttons:
			self._draw_buttons()

	def _draw_page_icons(self, r):
		y = self.area.top + (self.title_font.height * self.title_scale) / 2
		x = self.area.left

		if self.opt_left and self.opt_right:
			rect = self.opt_left.get_rect().fit(r)
			rect.left = self.area.left
			rect.centery = y
			self.opt_left.draw(dstrect=rect)
			left_icon = rect.copy()
			rect.right = self.area.right
			self.opt_right.draw(dstrect=rect)
			self.page_icons = left_icon, rect

		else:
			left_icon = self.title_font.scale(
				'<', x, y, self.title_scale, color=self.sel_color, valign='center')
			x = self.area.right
			w = self.font.width('>', self.reg_scale)
			right_icon = self.title_font.scale(
				'>', x-w, y, self.title_scale, color=self.sel_color, valign='center')
			self.page_icons = left_icon, right_icon


	def _draw_select(self, options):
		self.rects = []
		scale = self.reg_scale
		self._draw_background()
		if self.patch:
			self.patch.texture.alpha = self.alpha
			self.patch.surround(self.area)
			
		elif self.frame:
			self._draw_frame()

		y = self._draw_title()
		x = self.area.left + (self.area.width - self.l_space - self.r_space)/2

		for i, item in enumerate(options): # enumerate items
			rect = self.font.get_rect(item, x, y, scale, True)
			stretched = rect.copy()
			stretched.left = self.area.left + self.l_space
			stretched.width = self.area.width - self.l_space - self.r_space
			self.rects.append(stretched)
			if self.sel_stretch:
				rect = stretched
			x = stretched.centerx

			if i == self.selected: # handle selected item
				if self.sel_patch:
					r = rect.inflate(*self.but_padding)
					#r.y	+= self.but_padding[1] // 2
					self.sel_patch.draw(r)
				if self.anim:
					self.font.animate(
						item, x, rect.centery, align='center', scale=scale,
						color=self.sel_color, valign='center', **self.sel_anim)
				else:
					self.font.scale(
						item, x, rect.centery, scale, align='center',
						color=self.sel_color, valign='center')

				if self.left: # draw selection buttons
					r = self.left.get_rect()
					r.left = self.area.left
					r.centery = rect.centery
					self.left.draw(dstrect=r)
				if self.right:
					r = self.right.get_rect()
					r.right = self.area.right
					r.centery = rect.centery
					self.left.draw(dstrect=r)

			else: # draw normal item
				if self.anim:
					rect = self.font.animate(
						item, x, y, align='center', scale=scale, color=self.color,
						**self.anim)
				else:
					rect=self.font.scale(item, x, y, scale, align='center', color=self.color)
			y += rect.height + self.spacing

		if options != self.items:
			self._draw_page_icons(r)


	def _draw_title(self):
		y = self.area.top - self.title_offset
		if self.title:
			w = (self.area.right - self.r_space) - (self.area.left + self.l_space)
			x = self.area.left + self.l_space + w//2
			if self.title_anim:
				y += self.title_font.animate(
					self.title, x, y,
					scale=self.title_scale, align='center',
					color=self.title_color, **self.title_anim).height
			else:
				y += self.title_font.scale(self.title, x, y,
				scale=self.title_scale, align='center', color=self.title_color).height

		return max(y, self.area.top) + self.spacing

	def _get_box_size(self, x, y):
		if isinstance(self.box, NinePatch):
			return pg.Rect(
				x, y,
				self.area.width,
				self.box.top + self.box.bottom + self.but_padding[1])
		else:
			return pg.Rect(
				x, y,
				self.area.width,
				self.font.height * self.reg_scale + self.but_padding[1])

	def _get_input(self, events=None):
		select = False
		move = pg.Vector2()
		if self.ignore_input:
			self.ignore_input = False
			return move, select, events
	
		if events == None:
			events = pg.event.get()
		for event in events:
			if event.type == pg.QUIT and self.can_cancel:
				select = -1
			elif event.type == pg.TEXTINPUT and self.editing:
				inp = event.text
				if self.input_length and len(self.textinput) >= self.input_length:
					inp = None
				elif self.input_type == 'int' and event.text not in ('1234567890'):
					inp = None
				elif (self.input_type == 'float'):
					if event.text in ('1234567890') or (
							inp == '.' and '.' not in self.textinput):
						pass
					else:
						inp = None
				if inp:
					self.textinput += event.text
					self._play_sound()
				else:
					self._play_sound('bad')

			elif event.type == pg.KEYDOWN:
				if not self.rects and not self.buttons:
					select = True
				elif event.key == pg.K_UP:
					move.y = -1
				elif event.key == pg.K_DOWN:
					move.y = 1
				elif event.key == pg.K_LEFT:
					move.x = -1
				elif event.key == pg.K_RIGHT:
					move.x = 1
				elif event.key in (pg.K_KP_ENTER, pg.K_RETURN):
					select = True
				elif event.key == pg.K_SPACE and not self.editing:
					select = True
				elif event.key == (pg.K_ESCAPE) and	self.can_cancel:
					if not self.first_shown:
						select = -1
				elif event.key == (pg.K_BACKSPACE):
					self._play_sound('key')
					self.textinput = self.textinput[:-1]

			elif event.type == pg.MOUSEMOTION:
				pointer = self._get_mouse_pos()
				for r in self.rects:
					if r.collidepoint(pointer):
						if self.selected != self.rects.index(r):
							self.selected = self.rects.index(r)
							self._play_sound()
				for r in self.but_rects:
					if r.collidepoint(pointer):
						if (self.bselected != self.but_rects.index(r) or 
								self.selected != len(self.rects) - 1):
							self.selected = len(self.rects) - 1
							self.bselected = self.but_rects.index(r)
							self._play_sound()	

			elif event.type == pg.MOUSEBUTTONDOWN:
				pointer = self._get_mouse_pos()
				if event.button == 1:
					if self.page_icons:
						left, right = self.page_icons
						if left.collidepoint(pointer):
							move.x = -1
							continue
						elif right.collidepoint(pointer):
							move.x = 1
							continue

					if self.rects and self.rects[self.selected].collidepoint(pointer):
						select = True
					elif not self.area.collidepoint(pointer) and self.can_cancel:
						select = -1
					elif (self.buttons and  # changed from but_rects
							self.but_rects[self.bselected].collidepoint(pointer)):
						self.rvalue = self.buttons[self.bselected]
						self.changeable = None
						select = True
					elif not self.rects and not self.buttons:
						select = True

			
		if self.joystick:
			joystick, joy_sel, joy_cancel = self.joystick
			joy_sel = joystick.get_button(joy_sel) or -joystick.get_button(joy_cancel)

			x = int(joystick.get_axis(0) / AXIS_MOD * 1.99) #copysign without math
			y = int(joystick.get_axis(1) / AXIS_MOD * 1.99)
			if joystick.get_button(pg.CONTROLLER_BUTTON_DPAD_UP):
				y = -1
			elif joystick.get_button(pg.CONTROLLER_BUTTON_DPAD_DOWN):
				y = 1
			if joystick.get_button(pg.CONTROLLER_BUTTON_DPAD_LEFT):
				x = -1
			elif joystick.get_button(pg.CONTROLLER_BUTTON_DPAD_RIGHT):
				x = 1

			if joy_sel or x or y:
				if not self.joy_pressed or (
						self.joy_pressed > 20 and not self.joy_pressed % 5):
					move.x = move.x or x
					move.y = move.y or y
					if joystick.get_button(joy_cancel):
						if self.can_cancel or self.editing:
							select = -1
					else:
						select = select or joy_sel
				else:
					joy_sel = 0
				self.joy_pressed += 1
			
			else:
				self.joy_pressed = 0

			if self.editing:
				self.editing += 1
				if move.y:
					if self.textinput and self.cur_char == None:
						self.cur_char = char_map.index(self.textinput[-1])
					else:
						cc = self.cur_char or 0
						self.cur_char = int(cc + move.y*-1)
				if self.cur_char:
					if select > 0 or move.x > 0:
						self.textinput += char_map[self.cur_char % len(char_map)]
						self.cur_char = None
						joy_sel = select =  0
				elif move.x > 0:
					self.textinput += ' '
					self.cur_char = None
					joy_sel = select =  0
				if (joy_sel < 0 or move.x < 0) and len(self.textinput) > 0:
					self.textinput = self.textinput[:-1]
					self.cur_char = None
					joy_sel = select =  0
				select = max(select, 0)			

		self.first_shown = False
		self.page_icons = None #make sure it's cleared when unused
		return move, select, events


	def _get_mouse_pos(self):
		x, y = pg.mouse.get_pos()
		x = int(x * (self.viewport.w / self.window.size[0]))
		y = int(y * (self.viewport.h / self.window.size[1]))
		return (x, y)

		x, y = pg.mouse.get_pos()
		if self.target.target:
			wx, wy = self.target.target.get_rect().size
			vx, vy = self.target.get_viewport().size
			x = int(x * (vx / wx))
			y = int(y * (vy / wy))
		return(x, y)

	def _get_options_width(self, options):
		width = 0
		opt_width = 0
		if self.opt_left:
			opt_width += self.opt_left.get_rect().width
		if self.opt_right:
			opt_width += self.opt_right.get_rect().width
		for option in options.values():
			if option['type'] in ('LABEL', 'ITEM'):
				if 'text' not in option:
					option['text'] = ''
				scale = option.get('size', self.reg_scale)
				width = max(self.font.width(option['text'], scale), width)
			elif option['type'] == 'OPTION':
				items = option.get('options', [])
				pre, post = option.get('pre', ''), option.get('post', '')
				for item in items:
					if not isinstance(item, str):
						print(item,str)
						raise ValueError('invalid option: {}'.format(option))
					width = max(
						self.font.width(pre + item + post,
						self.reg_scale)+opt_width, width)
		if self.buttons:
			wi = 0
			for b in self.buttons:
				wi += self.font.width(b, self.reg_scale) + self.but_padding[0]
			width = max(wi, width)


		return width + self.spacingx*2

	def _play_sound(self, which='good'):
		sound = {
			'good': self.sound,
			'bad': self.sound_bad,
			'key': self.sound_key}.get(which, self.sound)
		if not sound:
			return
		elif isinstance(sound, pg.mixer.Sound):
			sound.play()
		else:
			try:
				func, args, kwargs = sound
				func(*args, **kwargs)
			except Exception as e:
				print('menu cannot execute {} in _play_sound()'.format(e))

	def _process_options(self, options):
		new_options = {}
		if not isinstance(options, dict):
			options = OrderedDict(enumerate(options))

		for key, option in options.items():
			if isinstance(option, dict):
				_type = option.get('type')
				if _type in ('OPTION', 'SLIDER', 'LABEL', 'ITEM', 'SPACER'):
					new_options[key] = option.copy()
				else:
					print('option unprocessable by menu: ', option)
			elif isinstance(option, str):
				if option.endswith('\t'):
					option += ' '
				new_options[key] = dict(type='LABEL', text=option)
			elif type(option) in (int, float, str):
				new_options[key] = dict(type='SPACER', amount=option)
			else:
				try:
					iter(option)
				except:
					continue
				if len(option) == 1:
					new_options[key] = dict(type='ITEM', text=option[0])
				else:
					if isinstance(option[-1], tuple):
						if len(option[-1]) == 3:
							pre, post, sel = option[-1]
						else:
							pre, post = option[-1]
							sel = 0
						new_options[key] = dict(
							type='OPTION', options=option[:-1],
							selected=sel, pre=pre, post=post)
					else:
						new_options[key] = dict(
							type='OPTION', options=option, selected=0)

		for option in new_options.values():
			if option['type'] == 'SLIDER':
				option['min'] = option.get('min', 0)
				option['max'] = option.get('max', 100)
				option['value'] = option.get(
						'value', int((option['max'] - option['min']) / 2))
				option['step'] = option.get('step', 5)
			elif option['type'] == 'OPTION':
				option['value'] = option['options'][option['selected']]
			elif option['type'] == 'SPACER':
				amount = option.get('amount', 0.5)
				try:
					amount = float(amount)
				except:
					amount = 0.5
				option['amount'] = amount
		return new_options

	def _modal_menu(self):
		old_target = self.target.target
		if old_target:
			self.target.target = Menu.buffer
			old_target.draw()
			self.target.target = old_target

		while self.alive:
			Menu.buffer.draw()
			rvalue = self.handle()

			if old_target:
				self.target.target = None
				old_target.draw()

			self.target.present()
			self.clock.tick(30)
			if old_target:
				self.target.target = old_target

		if old_target:
			self.target.target = old_target
			Menu.buffer.draw()
		return rvalue

	def _set_position(self):
		self.first_shown = True
		if self.patch:
			xvar = (self.patch.left - self.patch.right) // 2
			yvar = (self.patch.top - self.patch.bottom) // 2
		else:
			xvar = yvar = 0
		self.area.centerx = self.viewport.centerx + xvar
		self.area.centery = self.viewport.centery + yvar

		if self.position == 'mouse':
			self.area.center = pg.mouse.get_pos()
			w, h = self.viewport.size
			if self.patch:
				self.area.left = max(self.patch.left, self.area.left)
				self.area.top = max(self.patch.top, self.area.top)
				self.area.right = min(w - self.patch.right, self.area.right)
				self.area.bottom = min(h - self.patch.bottom, self.area.bottom)
			else:
				outl = self.frame[2] if self.frame else 0
				self.area.left = max(outl, self.area.left)
				self.area.top = max(outl, self.area.top)
				self.area.right = min(w - outl, self.area.right)
				self.area.bottom = min(h - outl, self.area.bottom)


			'''eX = self.spacingx
			eY = self.spacing * 2
			area = self.area.copy()
			if self.patch:
				area = self.patch.surround(area, draw=False)
			elif self.frame:
				eX += self.frame[2] * 2
				eY += self.frame[2] * 2
			area.center = pg.mouse.get_pos()
			area.clamp_ip(self.viewport.inflate(-eX, -eY))
			self.area.center = area.center'''

		elif self.patch:
			if self.position in (1,4,7):
				self.area.left = 0 + self.patch.left
			if self.position in (1,2,3):
				self.area.top = 0 + self.patch.top
			if self.position in (3,6,9):
				self.area.right = self.viewport.right - self.patch.right
			if self.position in (7,8,9):
				self.area.bottom = self.viewport.bottom - self.patch.bottom
		else:
			if self.position in (1,4,7):
				self.area.left = 0
			if self.position in (1,2,3):
				self.area.top = 0
			if self.position in (3,6,9):
				self.area.right = self.viewport.right
			if self.position in (7,8,9):
				self.area.bottom = self.viewport.bottom

	def create(self, typ, *args, **kwargs):
		if typ in ('dialog', 'input', 'options', 'select'):
			print(f'created {typ} menu')
			return getattr(self, typ)(*args, **kwargs)
		else:
			raise ValueError('{typ} is not a valid Menu type'.format(
					typ))

	def dialog(
			self, text, title, buttons=None, width=0,
			can_cancel=True, modeless=None, call_back=None):
		"""
		Display dialog with title, text, and up to 3 buttons

		:param title: title string
		:param text: text string
		:param buttons: tuple of strings for up to 3 buttons
		:param width: width of dialog in pixels
		:param can_cancel: can close menu without selecting a button by
				escape key, pg.QUIT event, and clicking outside menu
		"""
		self.title = title
		self.buttons = buttons
		self.call_back=call_back
		self.can_cancel = can_cancel
		width = min(width or self.viewport.width, self.viewport.width * 0.9)

		# Calculate max height
		height = int(self.viewport.height * 0.9) - self.spacing * 2
		if self.patch:
			height -= self.patch.top + self.patch.bottom
		if title:
			title_height = max(self.title_font.height * self.title_scale - self.title_offset,0)
			height -= title_height + self.spacing
		if buttons:
			height -= (self.font.height * self.reg_scale
					+ self.spacing + self.but_padding[1])
		self._break_text_lines(text, width, height)

		# Calculate actual height
		height = (self.text_font.height*self.text_scale) * (len(self.lines))
		if title:
			height += title_height + self.spacing
		if buttons:
			height += (self.font.height * self.reg_scale
					+ self.spacing + self.but_padding[1])

		self.area = pg.Rect(0, 0, width + self.spacingx*2, height + self.spacing * 2)
		self._set_position()
		self.rects = []
		self.bselected = 0
	
		self.ignore_input = True
		self.alive = True
		self.handle = self._handle_dialog
		if not modeless:
			return self._modal_menu()

	def _handle_dialog(self, events=None):
		rvalue = None
		if self.alive:
			self._draw_dialog()
			move, select, events = self._get_input(events)
			if move.x < 0:
				self.bselected -= 1
				self._play_sound()
			elif move.x > 0:
				self.bselected += 1
				self._play_sound()
			self.bselected = self.bselected % len(self.but_rects)

			if move.y:
				self._play_sound('bad')

			if select:	
				if select >= 0:
					rvalue = self.buttons[self.bselected]
					self.alive = False
					if self.call_back:
						self.call_back(rvalue)
				elif self.can_cancel:
					rvalue = 'Done'
					if self.call_back:
						self.call_back(rvalue)
					self.alive = False

		return rvalue
				

	def input(
			self, title, buttons=('Okay',), width=None, typ='string',
			length=None, can_cancel=True, modeless=False, call_back=None,
		  default_text=''):
		"""
		Display single line text input dialog with up to 3 buttons

		:param title: title string
		:param buttons: tuple of strings for up to 3 buttons
		:param width: width of dialog in pixels
		:param type: type can be 'string', 'int', 'float' (only strings so far)
		:param length: optional maximum length of text input (not yet implemented)
		:param can_cancel: can close menu without selecting a button by
				escape key, pg.QUIT event, and clicking outside menu
		:rvalue: 
		"""
		self.title = title
		self.buttons = buttons
		self.can_cancel = can_cancel
		self.bselected = 0
		self.old_repeat = pg.key.get_repeat()
		self.input_type = typ
		self.input_length = length
		self.call_back = call_back
		self.cur_char = None
		pg.key.set_repeat(500, 100)

		width = width or self.viewport.width * 0.75
		height = self.font.height * self.reg_scale + self.spacing
		height += self._get_box_size(0,0).height + self.spacing
		height += (self.title_font.height * self.title_scale + self.spacing) * 1
		height += self.but_padding[1] * 2

		self.area = pg.Rect(0, 0, width + self.spacingx*2, height + self.spacing)
		self._set_position()
		self.rects = [pg.Rect(0,0,0,0)]

		self.editing = 1
		self.textinput = default_text
		self._draw_input()

		self.ignore_input = True
		self.alive = True
		self.handle = self._handle_input
		if not modeless:
			return self._modal_menu()

	def _handle_input(self, events=None):
		rvalue = None, None, None
		if self.alive:
			self._draw_input()
			move, select, events = self._get_input(events)
			if move.x < 0:
				self._play_sound()
				self.bselected -= 1
			elif move.x > 0:
				self._play_sound()
				self.bselected += 1
			self.bselected = self.bselected % len(self.but_rects)

			if move.y:
				self._play_sound('bad')
			if select:
				self.alive = False
				if select >= 0:
					if self.joystick:
						self.textinput = self.textinput.replace('_', ' ')
					if self.input_type == 'int':
						try:
							self.textinput = int(self.textinput)
						except:
							self.textinput = 0
					elif self.input_type == 'float':
						try:
							self.textinput = float(self.textinput)
						except:
							self.textinput = float(0)
					rvalue = self.textinput, self.bselected, self.buttons[self.bselected]
				if self.call_back:
					self.call_back(*rvalue)

			if not self.alive:
				self.editing = 0
				pg.key.set_repeat(*self.old_repeat)
		return rvalue

	def select(
			self, options, title=None, min_width=0,
			can_cancel=False, modeless=False, call_back=None):
		"""
		Display selection dialog that displays options in a vertical list. Long
		lists will be broken into pages.

		:param options: list of option dicts or convinience tuples
		:param title: optional title string
		:param width: optional minimum width but dialog may stretch to accomodate
				longest option string
		:param can_cancel: can close menu without selecting a button by
				escape key, pg.QUIT event, and clicking outside menu
		:param call_back: call this function when an item is selected
		:rtype index, string: the option selected as index and string
		"""
		key_repeat = pg.key.get_repeat()
		pg.key.set_repeat(500, 250)
		scale = self.reg_scale
		#title = title or 'page'
		self.title = title or 'page'
		self.can_cancel = can_cancel
		self.call_back = call_back
		self.buttons = None
		self.but_rects = []
		xspace = self.l_space + self.r_space 
		height = 0

		if self.opt_left and self.opt_right:
			opt = self.opt_left.get_rect().width + self.opt_right.get_rect().width
		else:
			opt = self.title_font.width('<  >', scale)

		width = self.title_font.get_rect(self.title, 0,0, scale=self.title_scale).width
		space = opt
		width = max(width+space, min_width)
		height = self.spacing + max(0, 
			 self.title_font.height * self.title_scale - self.title_offset)

		max_height = self.viewport.height * 0.9 - height
		if self.patch:
			max_height -= self.patch.top + self.patch.bottom
		self.max_items = int(max_height / (self.font.height * scale + self.spacing))
		self.items = options
		options = options[:self.max_items]
		self.page = -1 if options == self.items else 0
		height += (self.font.height*scale + self.spacing) * len(options)
		if self.title == 'page' and self.page < 0:
			height -= self.font.height * self.title_scale
			self.title = ''

		for item in options:
			width = max(self.font.width(item, scale)+xspace, width)

		self.area = pg.Rect(0, 0, width + self.spacingx*2, height + self.spacing * 2)
		self._set_position()
		self.rects = []
		self.selected = 0
	
		self.ignore_input = True
		self.alive = True
		self.handle = self._handle_select
		if not modeless:
			return self._modal_menu()

	def _handle_select(self, events=None):
		if not self.alive:
			return
		move, select, events = self._get_input(events)
		rvalue = None
		max_items = self.max_items

		page = self.page
		if page >= 0:
			pages = int(len(self.items) / max_items + 0.9)
			options = self.items[page*max_items:(page+1)*max_items]
		else:
			options = self.items

		self._draw_select(options)
		if move.y < 0:
			self.selected -= 1
			self._play_sound()
		elif move.y > 0:
			self.selected += 1
			self._play_sound()
		elif move.x:
			if page >=0:
				self._play_sound()
				if move.x > 0:
					page = (page + 1) % pages
				if move.x < 0:
					page = (page - 1) % pages
				self.page = page
			else:
				self._play_sound('bad')

		self.selected = min(self.selected % len(options), len(options))
		if select:
			rvalue = None, None
			self.alive = False
			if select >= 0:
				selected = (self.selected + (page*max_items)
						if page > 0 else self.selected)
				rvalue = selected, options[self.selected]
			if self.call_back:
				self.call_back(*rvalue)
		return rvalue


	def _get_option_height(self, options):
		height = 0
		for item in options.values():
			th = self.font.get_rect(' ', 0,0, scale=self.reg_scale).height
			if item['type'] == 'ITEM':
				height += th + self.spacing
			elif item['type'] == 'LABEL':
				if item.get('size', None):
					height += th * item['size'] + self.spacing
				else:
					height += th + self.spacing
			elif item['type'] == 'OPTION':
				opt = self.opt_left.get_rect().height if self.opt_left else 0
				opt = th + self.spacing
				#FIX I disabled the opt icon spacing and just fit them

				height += max(th, opt) + self.spacing
			elif item['type'] == 'SPACER':
				height += item['amount'] * self.font.height * self.reg_scale
			elif item['type'] == 'SLIDER':
				if hasattr(self.box, 'min_height'):
					height += max(th, self.box.min_height) + self.spacing
				else: height += th + self.spacing
		height += self.but_padding[1]
		return height

	def options(
			self, options, title=None, buttons=('Okay', ), width=0,
			can_cancel=True, modeless=False, call_back=None):
		'''
		Create an options menu featuring buttons, sliders, and toggles
		:param options: list of option dicts or convenience tuples
		:param title: text for title bar
		:param buttons: bottom buttons such as okay, cancel
		:param width: default width in pixels
		:param can_cancel: if true menu may be closed without using bottom buttons
		:param modeless: set false and menu will block until closed
						set true and method returns immediately
		:param call_back: function will be called when menu options change
						call_back signature = menu(item, value, option_dict)
		:rtype item, value, option_dict:

		Available options include LABEL, ITEM, OPTION, SLIDER, and SPACER 
		LABEL - Simple non-interactive text label 
			type: 'LABEL' 
			size(int, float)(opt): scalar to alter font size(.5 for half, 2 to double) 
			color(3-tuple, pg.Color)(opt): font color 
			shortcut: string 
		ITEM - An item that can be clicked/selected
			type: 'ITEM'
			text(str): string to be displayed 
			shortcut: (string,)
		OPTION - multiple options of which one may be selected
			type: 'OPTION'
			options(list, tuple): list of strings, one for each option 
			pre(str): a string displayed before the selected option's text
			post(str): a string displayed after the selected option's text
			selected(int): index of default/current selected option
			shortcut: (option1, option2, etc, (pre, post, selected[optional])[optional]
		OPTION - slider to select an int/float value within a range
			type: 'SLIDER'
			min(int, float): minimum value to be selected
			max(int, float): maximum value to be selected
			step(int, float): how much to increase/decrease value per button press
			value(int): the default/current value of the slider
			shortcut: None
		SPACER - add some space between menu items to group them
			type: 'SPACER'
			amount(int, float): scalar for amount of space based on default font
			shortcut: int, float
		'''
		self.can_cancel = can_cancel
		self.title = title
		self.buttons = buttons
		items = self._process_options(options.copy())
		height = self._get_option_height(items)
		_width = self._get_options_width(items) + self.but_padding[0]

		if title:
			title_height = self.title_font.height * self.title_scale
			height += max(title_height - self.title_offset, 0) + self.spacing 
			_width = max(_width, self.title_font.width(title, self.title_scale))
		if buttons:
			h = self.but_padding[1] if self.sel_patch else 0
			min_height = self.but_patch.min_height if self.but_patch else 0
			height += max(self.font.height * self.reg_scale + self.spacing, min_height) + h
		_width += self.l_space + self.r_space
		width = max(width, _width)
		self.call_back = call_back

		self.rects = []
		self.area = pg.Rect(0, 0, width, height)
		self._set_position()
		self.selected = 0	
		self.bselected = 0
		self.rvalue = None

		self.items = items
		self.keys = []
		for k, v in self.items.items():
			if v['type'] in ('ITEM', 'OPTION', 'SLIDER'):
				self.keys.append(k)

		self.ignore_input = True
		self.alive = True
		self.handle = self._handle_options
		if not modeless:
			return self._modal_menu()

	def _handle_options(self, events=None):
		rvalue = None
		if self.alive:
			options = self.items
			self._draw_options(options)
			if self.buttons: # extra rect for bottom buttons
				self.rects.append(pg.Rect(0,0,1,1)) 
			move, select, events = self._get_input(events)

			if move.y < 0:
				self.selected -= 1
				self._play_sound()
			elif move.y > 0:
				self.selected += 1
				self._play_sound()
			if self.rects:
				self.selected = self.selected % len(self.rects)

			if move.x:
				if self.buttons and self.selected == len(self.rects) - 1: 
					# button row selected
					self._play_sound()
					if move.x > 0:
						self.bselected += 1 
					else:
						self.bselected -= 1
					self.bselected = self.bselected % len(self.but_rects)
				else:
					rvalue = self.keys[self.selected], self._change_option(move.x), self.items
					if rvalue and self.call_back:
						self.call_back(*rvalue)

			if select:
				rvalue = None
				if self.buttons and self.selected == len(self.rects) - 1:
					rvalue = 'BUTTON', self.buttons[self.bselected], self.items
					self.alive = False
				elif select >= 0:
					key = self.keys[self.selected]
					if self.changeable:
						val = self._change_option(1)
						rvalue = key, val, self.items
					else:
						sel = self.keys[self.selected]

						rvalue = key, self.items[sel]['text'], self.items
						self.alive = False
				else:
					self.alive = False
				if rvalue and self.call_back:
					self.call_back(*rvalue)
		return rvalue

	def set_background(self, background, tiled=False):
		'''
		Set background to draw behind modal menus. This does not effect
		modeless menus that users must manually draw instead.

		:param background: can be an image, texture, color, or callable
			callables should be in form (function, args, kwargs)
		:param tiled: set true to tile background image instead of stretching
		'''
		self.back_tiled = tiled
		self.back_func = None
		self.back_image = None
		self.back_color = pg.Color(0, 0, 0)
		self.draw_background = True if background or not self.patch else False

		if isinstance(background, (Image, Texture)):
			self.back_image = background
			r = background.get_rect()
			if r.width < self.viewport.width / 2 or r.height < self.viewport.height / 2:
				self.back_tiled = True
		elif callable(background):
			self.back_func = (background, [], {})
		elif isinstance(background, pg.Color):
			self.back_color = background
		elif isinstance(background, (tuple, list)):
			try:
				a, b, c = background
			except:
				a, b, c = 0, 0, 0
			
			if callable(a):
				self.back_func = a, b, c
	
	def _draw_background(self):
		if self.draw_background:
			if self.back_func:
				self.back_func[0](self.back_func[1:])
			elif  self.back_image:
				if self.back_tiled:
					tile_background(self.target, self.back_image)
				else:
					self.back_image.draw()
			else:
				self.target.draw_color = self.back_color
				self.target.clear()

	def _limit_string(self, text, font, scale, pre='_'):
		w = font.get_rect('=', 0,0, scale).width
		scr_w = self.viewport.w - self.spacingx * 2
		if self.patch:
			scr_w -= self.patch.left + self.patch.right
		elif self.frame:
			scr_w -= self.frame[2] * 2
		max_chars = scr_w // w
		if len(text) > max_chars:
			return pre + text[-max_chars:]
		return text

	def get_max_options(self):
		'''
		calculate max number of options for option menu
		that should fit on the current renderer
		'''
		items = ['test', ]
		self.options(items, 'title', ('test',), modeless=True)
		min_height = self.area.h
		self.options(items*2, 'title', ('test',), modeless=True)
		item_height = self.area.h - min_height
		if self.patch:
			min_height += self.patch.top + self.patch.bottom
		return ((self.viewport.h - min_height) // item_height) - 1
	def _get_file_list(self, path, show='both', allow='both'):
		files = []
		folders = []
		parent = [('..',)] if show in ('folders', 'both') else []
		sel_files = allow in ('files', 'both')
		for f in os.listdir(path):
			if show in ('folders', 'both'):
				if os.path.isdir(os.path.join(path, f)):
					folders.append(f+'/')
			if show in ('files', 'both'):
				if os.path.isfile(os.path.join(path, f)):
					files.append(f)
		
		files.sort(key=lambda s: s.lower())
		folders.sort(key=lambda s: s.lower())
		if allow in ('files', 'both'):
			files = [(f,) for f in files]
		folders = [(f,) for f in folders]
		
		return parent + folders + files

	def file_selector(self, path, show='both',
			allow='both', call_back=None, allow_new=False):
		'''
		Opens a dialog where users may navigate the directory structure
		and select a file or folder. 

		:param path: directory where the dialog starts
		:param show: show 'files', 'folders', or 'both.' Using folders
				or both allows directory navigation
		:param allow: allow 'file', 'folder', or 'both' to be selected
		:param call_back: a function to be called when an file or
				folder is selected. It should accept one string
				parameter that will be the absolute path
		:rvalue: returns the absolute path to the file or folder
				as a string when selected(modal). Or None if a 
				call_back is provided(modeless).
		'''
		def handle(key, sel, options):
			path, items, pages, page, max_items = handle.info
			if key == 1 and not handle.selected:
				pager = options[1]
				page = pager['selected']
				cur_items = items[page*max_items:(page+1)*max_items]
				items = [options[0], pager] + cur_items
				self.options(items, self.title, ('Okay','Cancel'), 
						call_back=handle, modeless=modeless, can_cancel=True)
			elif type(sel) != str:
				print('weird selector handle', key, sel)
			elif sel in ('Okay', 'New'):
				if sel == 'New':
					new_folder, _, but = self.input('New Folder', 
						('Okay', 'Cancel'), width=self.info_width)
					if but == 'Okay':
						path = os.path.join(path, new_folder)
						if not os.path.exists(path):
							os.mkdir(path)
				if handle.selected and handle.files:
					handle.selected = os.path.join(path, handle.selected)
				else:
					handle.selected = path
				if handle.call_back:
					call_back(handle.selected)
			elif sel == 'Cancel':
				handle.selected = None
				if handle.call_back:
					handle.call_back(None)
			elif sel == '..':
				if handle.selected:
					handle.selected = None
				else:
					path = os.path.dirname(path.rstrip(os.sep))
				handle.selected = self.file_selector(path,
						show, allow,
						handle.call_back, allow_new)
			elif sel.endswith('/'):
				path = os.path.join(path, sel)
				return self.file_selector(path,
						show, allow,
						handle.call_back, allow_new)
			else:
				self.alive = True
				handle.selected = sel
				items = [('..',), (sel)]
				self.options(items, self.title, ('Okay','Cancel'), 
						call_back=handle, modeless=modeless, can_cancel=True)

		handle.call_back = call_back
		handle.selected = None
		max_items = self.get_max_options()

		page = 0
		handle.files = allow in ('file', 'both')
		items = self._get_file_list(path, show, allow)
		pages = len(items) // (max_items-1)
		cur_items = items[page*max_items:(page+1)*max_items]

		psize = 0.77
		_path = self._limit_string(path, self.font, psize)
		dpath = dict(
			type='LABEL', size=psize, color=self.title_color, text=_path)

		pages = ['Page {}'.format(i+1) for i in range(pages+1)]
		options = [dpath, pages + [('', '')]] + cur_items
		handle.info = path, items, pages, page, max_items

		modeless = True if call_back else False
		self.position = 5
		title = {'file': "Select File", 'folder': "Select Folder",
				'both': 'Select File/Folder'}.get(allow, "Select File/Folder")
		buttons = ('Okay', 'Cancel', 'New') if allow_new else ('Okay', 'Cancel')
		self.options(options, title, buttons, 
			call_back=handle, modeless=modeless, can_cancel=True)
		result, handle.selected = handle.selected, None
		return result


