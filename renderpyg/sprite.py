'''
sprite.py: GPU Animated Sprite renderer

Render and animate sprites using the pygame._sdl2 GPU renderer

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
from math import copysign
import pygame as pg
from pygame._sdl2.video import Window, Renderer, Texture, Image
from .base import load_images, load_texture, fetch_images, load_xml_images

def GPUGroupDraw(self, surface=None):
	"""
	Draws all of the member sprites into their attached renderer.

	Group.draw(surface): return None

	This method overrides the draw() method of default groups to 
	renderer to sprite.image.dstrect instead of sprite.rect. This
	allows collision functions to use sprite.rect as a hit box.
	"""
	sprites = self.sprites()
	for spr in sprites:
		self.spritedict[spr] = spr.image.draw(dstrect=spr.dest_rect)
	self.lostsprites = []
pg.sprite.AbstractGroup.draw = GPUGroupDraw

class GPUAniSprite(pg.sprite.Sprite):
	"""
	Class for rendering and animating game objects using the
	pygame._sdl2 GPU renderer. Retains compatability with the sprite
	groups provided pygame.
	"""
	loop_types = ('forward', 'back_forth')
	max_velocity = 1000
	def __init__(self, source, width=None, height=None, **kwargs):
		"""
		Create animated sprite object

		:param source: texture, image list, or a (renderer, filename) pair to
			load images an from image file or TextureAtlas XML
		:param width: width of each animation frames
		:param height: height of each animation frame
		:param spacing: space between each animation frame
		:param margin: border between image edges and animation frames
		:param by_count: set True to use width and height value to
			calculate frame size from width and height of spritesheet
			grid
		"""
		pg.sprite.Sprite.__init__(self)
		if isinstance(source, Texture):
			self.images = fetch_images(source, width, height, **kwargs)
		else:
			try:
				iter(source)
			except Exception:
				raise ValueError(
					'Cannot parse {} as source of GPUAniSPrite'.format(source))
			if isinstance(source[0], Renderer):
				if source[1].endswith('.xml'):
					self.images = load_xml_images(source[0], source[1])
				else:
					self.images = load_images(
						source[0], source[1], width, height, **kwargs)
			elif isinstance(source[0], Image):
				self.images = []
				for image in source:
					self.images.append(Image(image))
			else:
				raise ValueError(
					'Cannot parse {} as source of GPUAniSPrite'.format(source))

		self.names = {}
		self.x = 0
		self.y = 0
		self.angle = 0
		self.anim_frame = 0
		self.anim_frames = []
		self.loop_type='forward'
		self.loop_count = 0
		self.time_spent = 0
		self.held_animation = None
		self.event_queue = []
		self.anim_queue = []
		self.speed = 1
		self.scale = 1
		self.set_anchor(kwargs.get('anchor'))
		self.set_hitbox(kwargs.get('hitbox'))
		self.set_transform(kwargs.get('transform'))
		self.velocity = None
		self.accel = None
		self.rotation = None
		self.scaling = None
		self.clock = None
		self.rect = self.images[0].get_rect()
		self.set_frame(0)

	def draw(self, dstrect=None):
		'''
		Render the sprite at its current position or at the postion of dstrect
		Use set_pos() and set_frame() modify where and how to draw it
		Sprites will animate if Sprite.clock references a time.Clock object
		''' 
		if self.clock:
			self.update(self.clock.get_time())
		
		if dstrect:
			self.image.draw(dstrect=dstrect)
		else:
			self.image.draw(dstrect=self.dest_rect)
	
	def draw_debug(self, color=(255,255,255,255)):
		'''
		Render the sprite at its current position, showing collision
		hit box and anchor point for debugging.

		:param color: color and alpha value for outline, default white
		'''
		renderer = self.image.texture.renderer
		self.image.draw(dstrect=self.dest_rect)
		renderer.draw_color = color
		r = pg.Rect(self.x-self.transform.x-2, self.y-self.transform.y-2, 4,4)
		renderer.fill_rect(r)
		renderer.draw_rect(self.rect)

	def get_rect(self):
		"""
		This method is provided to support compatability with Image objects. Allows
		animated sprites to be drawn where still images are expected.
		"""
		rect = self.rect.copy()
		rect.x = 0
		rect.y = 0
		return rect

	def interrupt(self, animation, loop_type='forward'):
		"""
		Interrupt current animation and play given one once before resuming
		previous animation.

		:param animation: list of animation keyframes
		:param loop_type: playback mode from available loop types:
				'forward', 'back_forth', 'reverse'
		:rtype None:
		"""
		self.held_animation = (
				self.anim_frames, self.anim_frame, self.loop_type,
				self.loop_count)
		self.set_animation(animation, 0, loop_type)

	def _next_animation(self):
		"""
		Internal method to transition to interrupted and queued animations
		"""
		if self.held_animation:
			(self.anim_frames, self.anim_frame, self.loop_type,
				self.loop_count)=self.held_animation
			self.held_animation = False
			return True
		else:
			if self.anim_queue and self.loop_count <= 0:
				self.set_animation(*self.anim_queue.pop(0))
				return True
			if self.event_queue and self.loop_count <= 0:
				for event, args, kwargs in self.event_queue:
					event(*args, **kwargs)
				self.event_queue = []

	def _next_frame(self):
		"""
		Internal method to handle keyframe progression
		"""
		self.anim_frame += 1
		try:
			anim_length = len(self.anim_frames)
		except Exception as e:
			print(f"[Error] {type(e).__name__}: {e}")

		set_frame = False
		if self.loop_type == 'forward':
			if self.anim_frame >= anim_length:
				self.loop_count -= 1
				if self._next_animation():
					return
				elif self.loop_count != 0:
					self.anim_frame = 0
					set_frame = self.anim_frames[self.anim_frame]
				else:
					self.stop()
			else:
				set_frame = self.anim_frames[self.anim_frame]

		elif self.loop_type == 'back_forth':
			if self.anim_frame < anim_length:
				set_frame = self.anim_frames[self.anim_frame]
			elif self.anim_frame < anim_length * 2-1:
				next_frame = anim_length-self.anim_frame-2
				set_frame = self.anim_frames[next_frame]
			else:
				self.anim_frame = 0
				self.loop_count -= 1
				if self._next_animation():
					return
				elif self.loop_count != 0:
					self.anim_frame = 0
				else:
					set_frame = False
					self.stop()

		if set_frame:
			self.set_frame(**set_frame)

	def queue_animation(self, animation, loop_count=0, loop_type='forward'):
		"""
		Queue animation to play following the current animation.

		:param animation: list of animatin keyframes
		:param loop_count: number of times to loop animation,
			or -1 for continous
		:param loop_type: playback mode from available loop types:
				'forward', 'back_forth', 'reverse'
		:rvalue None:

		This method will let the current animation's loop count finish
		or play after current cycle when a continous loop is playing.
		Multiple animations	may be queued and will play in First In 
		First Out order.
		"""
		if not self.duration:
			self.set_animation(animation, loop_count, loop_type)
		else:
			self.anim_queue.append((animation, loop_count, loop_type))
	
	def queue_event(self, func, *args, **kwargs):
		"""
		Queue events to be executed after current animation finishes.

		:param func: function to all
		:param args: arguments to pass into function
		:param kwargs: keyword arguments to pass into function
		:rvalue None:

		This method will let the current animation's loop count finish
		or play after current cycle when a continous loop is playing.
		All queue events will execute when the first animation finishes.
		"""
		self.event_queue.append((func, args, kwargs))

	def set_anchor(self, anchor):
		"""
		Set anchor point to draw image around. Default (0,0) at 
		top-left corner

		:param anchor: (x,y) pair or Vector2
		"""
		try:
			if len(anchor) == 2:
				self.anchor = anchor
		except:
			self.anchor = pg.Vector2()

	def set_animation(self, animation, loop_count=0, loop_type='forward'):
		"""
		Start animation based on keyframe list and loop count

		:param animation: list of keyframes as generated by keyfr()
		:param loop_count: number of times to loop animation,
			or -1 for continous
		:param loop_type: playback mode from available loop types:
				'forward', 'back_forth', 'reverse'
		:rvalue None:
		"""
		self.anim_frame = 0
		self.time_spent = 0
		self.anim_frames = animation
		self.loop_count = loop_count
		self.loop_type = loop_type
		self.set_frame(**self.anim_frames[0])

	def set_clock(self, clock=None):
		"""
		Provide a pygame.time.Clock reference for automatic animation. Future
		Sprite.draw() calls will automatically call its update() method so
		you should not call it yourself. Use set_clock(None) to return to
		normal behavior
		"""
		self.clock = clock

	def set_frame(self, frame=0, duration=0, **kwargs):
		"""
		Set frame number and other parameters as generated by keyfr()

		:param frame: frame number or name string
		:param duration: length for current frame transitions, used
			mostly with set_animation()
		"""
		self.time_spent = 0
		self.frame = self.names.get(frame, int(frame))
		try:
			self.image = self.images[self.frame]
		except:
			self.image = self.images[0]
		self.duration = duration
		self.angle = kwargs.get('angle', self.angle)
		self.image.flipX = kwargs.get('flipX', False)
		self.image.flipY = kwargs.get('flipY', False)

		color = kwargs.get('color', None)
		if color:
			self.image.color = color
		self.image.alpha = kwargs.get('alpha', self.image.alpha)

		if 'scale' in kwargs:
			self.scale = kwargs['scale']
		self.pos = kwargs.get('pos', pg.Vector2())
		
		if 'velocity' in kwargs:
			self.velocity = kwargs['velocity']
		if 'accel' in kwargs:
			self.accel = kwargs['accel']
		if 'rotation' in kwargs:
			self.rotation = kwargs['rotation']
		if 'scaling' in kwargs:
			self.scaling = kwargs['scaling']
		self.fading = kwargs.get('fading', None)
		self.coloring = kwargs.get('coloring', None)

		if self.pos:
			self.x, self.y = self.pos
		self.dest_rect = getattr(self, 'dest_rect', self.image.get_rect())  
		#if self.scale != 1:
			#self.dest_rect.inflate_ip(
			#	dest.w * self.scale, dest.h * self.scale)
			#c = self.dest_rect.center
			#self.dest_rect.width *= self.scale
			#self.dest_rect.height *= self.scale
			#self.dest_rect.center = c

		self.dest_rect.x = self.x - self.transform[0] - self.anchor[0]
		self.dest_rect.y = self.y - self.transform[1] - self.anchor[1]
		self.image.angle = self.angle
		self.image.origin = self.dest_rect.width / 2, self.dest_rect.height / 2
		if self.hit_anchor:
			self.rect.x = (self.x + self.hit_anchor[0]
				- self.transform[0] - self.anchor[0])
			self.rect.y = (self.y + self.hit_anchor[1]
				- self.transform[1] - self.anchor[1])		


	def set_hitbox(self, box):
		"""
		Set collision area of the sprite

		:param box: rect area for hit box based on top-left corner of image
		:rvalue None:
		"""
		try:
			box = pg.Rect(box)
			self.hit_anchor = box.x, box.y
			self.rect = box
			self.rect.x = 0
			self.rect.y = 0
		except:
			self.hit_anchor = None	

	def set_pos(self, x, y=None):
		"""
		Set new sprite location and update rects for drawing and collision
		
		:param x: x coordinate, (x,y) pair, or Vector2
		:param y: y cordinate if (x,y) pair and Vector2 not used
		:rvalue None:
		"""
		if y is None:
			x, y = x
		self.x = x
		self.y = y

		self.dest_rect.x = self.x - self.transform[0] - self.anchor[0]
		self.dest_rect.y = self.y - self.transform[1] - self.anchor[1]
		if self.hit_anchor:
			self.rect.x = (self.x + self.hit_anchor[0]
				- self.transform[0] - self.anchor[0])
			self.rect.y = (self.y + self.hit_anchor[1]
				- self.transform[1] - self.anchor[1])
		else:
			pass
			#self.rect = self.dest_rect
	
	def set_transform(self, transform):
		"""
		Set camera and zoom transform to support a scrolling tilemap or background

		:transform: (x,y,zoom) triplet or Vector3
		:rvalue None:
		"""
		try:
			if len(transform) == 3:
				self.transform = transform
		except:
			self.transform = pg.Vector3()

	def stop(self):
		"""
		Stop current animation and transformation. The image will stay where it is.
		"""
		self.duration = 0
		self.velocity = None
		self.rotation = None
		self.scaling = None
		self.fading = None
		self.coloring = None	


	def update(self, delta):
		"""
		Update the sprite's animation based on time delta in milliseconds

		:param delta: time in milliseconds that passed since the last update()
		:rvalue None:
		"""
		if not self.speed:
			return
		self.time_spent += delta
		delta = delta / 1000
		if self.duration and self.time_spent > abs(self.duration / self.speed):
			self._next_frame()

		if self.accel:
			self.velocity[0] += self.accel[0] * delta * self.speed
			self.velocity[1] += self.accel[1] * delta * self.speed
			#self.velocity = (
			#		self.velocity[0] + self.accel[0] * delta * self.speed,
			#		self.velocity[1] + self.accel[1] * delta * self.speed )


			if abs(self.velocity[0]) > self.max_velocity:
				self.velocity[0] = copysign(self.max_velocity, self.velocity[0])
			if abs(self.velocity[1]) > self.max_velocity:
				self.velocity[1] = copysign(self.max_velocity, self.velocity[1])

		if self.velocity:
			self.x += self.velocity[0] * delta * self.speed
			self.y += self.velocity[1] * delta * self.speed

		dest = self.image.get_rect()
		dest.x = self.x - self.anchor[0]
		dest.y = self.y - self.anchor[1]
		#if self.hit_box:
		#	pass

		if self.rotation:
			self.angle += self.rotation * delta * self.speed
			self.image.angle = self.angle
		if self.scaling:
			self.scale += self.scaling * delta * self.speed
		if self.scale != 1:
			dest.inflate_ip(
				dest.w * (self.scale-1), dest.h * (self.scale-1))

		if self.fading:
			fading = self.fading * delta * self.speed
			self.image.alpha = min(max(
					self.image.alpha - fading, 0), 255)

		'''
		self.dest_rect = dest # WTF DOUBLED
		self.dest_rect.x = self.x - self.transform[0] - self.anchor[0]
		self.dest_rect.y = self.y - self.transform[1] - self.anchor[1]
		if self.hit_anchor:
			self.rect.x = (self.x + self.hit_anchor[0]
				- self.transform[0] - self.anchor[0])
			self.rect.y = (self.y + self.hit_anchor[1]
				- self.transform[1] - self.anchor[1])'''

		self.rect = dest
		self.dest_rect = dest.move(-self.transform[0], -self.transform[1])



def keyfr(frame=0, duration=1000, **kwargs):
	"""
	Returns a single keyframe with given parameters

	:param frame: name or number of image for this keyframe
	:param duration: time in milliseconds for this keyframe
	:param angle: degrees of clockwise rotation around a center origin
	:param flipX: set True to flip image horizontally
	:param flipY: set True flip image vertically
	:param color: (r,g,b) triplet to shift color values
	:param alpha: alpha transparency value
	:param scale: scaling multiplier where 1.0 is unchanged
	:param pos: optional (x,y) pair or Vector2 to set sprite position
	:param velocity: optional (x,y) or Vector2 for sprite to move
		measured in pixels per second
	:param rotation: optional degrees of clockwise rotation per second
	:param scaling: optional amount to scale per second where 0 = None
	:param fading: optional int to subract from alpha value per second
	:param coloring: (r,g,b) triplet to shift each color value per second
	"""
	kwargs.update(frame=frame, duration=duration)
	return(kwargs)

def keyframes(frames=[], duration=1000, **kwargs):
	"""
	Returns a list of frames sharing the same parameters

	:param frames: list of image names or numbers to build keyframes
		that share the given parameters.
	:param duration: time in milliseconds for every keyframe
	
	Any additional parameters availble for keyfr() are allowed and will
	be set for each keyframe in the list.
	"""
	frame_list = []
	for fr in frames:
		kwargs.update(frame=fr, duration=duration)
		frame_list.append(kwargs.copy())
	return frame_list

def keyrange(start, end, duration=1000, **kwargs):
	"""
	Returns a list of frames sharing the same parameters

	:param start: the first frame number for a range of frames used to
		build a list of keyframes that share the given parameters
	:param end: the last frame number for a range of frames used to
		build a list of keyframes that share the given parameter
	:param duration: time in milliseconds for every keyframe
	
	Any additional parameters availble for keyfr() are allowed and will
	be set for each keyframe in the list.
	"""
	frame_list = []
	for fr in range(start, end):
		kwargs.update(frame=fr, duration=duration)
		frame_list.append(kwargs.copy())
	return frame_list
