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
import pygame as pg
from pygame._sdl2.video import Window, Renderer, Texture, Image
from .base import load_images, load_texture, fetch_images

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
	def __init__(self, source, width=None, height=None, **kwargs):
		"""
		Create animated sprite object

		:param source: texture, image, or (renderer, filename) pair to
			load image from
		:param width: width of each animation frames
		:param height: height of each animation frame
		:param spacing: space between each animation frame
		:param margin: border between image edges and animation frames
		:param by_count: set True to use width and height value to
			calculate frame size from width and height of spritesheet
			grid
		"""
		pg.sprite.Sprite.__init__(self)
		if type(source) == Texture:
			self.images = fetch_images(source, width, height, **kwargs)
		elif hasattr(source, '__len__') and type(source[0]) == Renderer:
			self.images = load_images(
				source[0], source[1], width, height, **kwargs)
		elif hasattr(source, '__len__') and type(source[0]) == Image:
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
		self.set_anchor(kwargs.get('anchor', None))
		self.set_hitbox(kwargs.get('hitbox', None))
		self.set_transform(kwargs.get('transform', None))
		self.velocity = None
		self.rotation = None
		self.scaling = None
		self.set_frame(0)

	def draw(self):
		'''
		Render the sprite at its current position
		Use set_pos() and set_frame() modify where and how to draw it
		''' 
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
		r = pg.Rect(self.x+self.transform.x-2, self.y+self.transform.y-2, 4,4)
		renderer.fill_rect(r)
		renderer.draw_rect(self.rect)

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
		except:
			return

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
		angle = kwargs.get('angle', None) 
		self.angle = angle if angle != None else self.angle
		self.image.flipX = kwargs.get('flipx', False)
		self.image.flipY = kwargs.get('flipy', False)
		self.image.color = pg.color.Color(
				kwargs.get('color', (255,255,255)))
		self.image.alpha = pg.color.Color(
				kwargs.get('alpha', 255))
		self.scale = kwargs.get('scale', 1)
		self.pos = kwargs.get('pos', pg.Vector2())
		
		if 'velocity' in kwargs:
			self.velocity = kwargs['velocity']
		if 'rotation' in kwargs:
			self.rotation = kwargs['rotation']
		if 'scaling' in kwargs:
			self.scaling = kwargs['scaling']
		self.fading = kwargs.get('fading', None)
		self.coloring = kwargs.get('coloring', None)

		if self.pos:
			self.x, self.y = self.pos
		self.dest_rect = self.image.get_rect()
		if self.scale != 1:
			c = self.dest_rect.center
			self.dest_rect.width *= self.scale
			self.dest_rect.height *= self.scale
			self.dest_rect.center = c

		self.dest_rect.x = self.x + self.transform[0] - self.anchor[0]
		self.dest_rect.y = self.y + self.transform[1] - self.anchor[1]
		self.image.angle = self.angle
		self.image.origin = self.dest_rect.width / 2, self.dest_rect.height / 2
		if self.hit_anchor:
			self.rect.x = (self.x + self.hit_anchor[0]
				+ self.transform[0] - self.anchor[0])
			self.rect.y = (self.y + self.hit_anchor[1]
				+ self.transform[1] - self.anchor[1])
		else:
			self.rect = self.dest_rect

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
		if y == None:
			x, y = x
		self.x = x
		self.y = y

		self.dest_rect.x = self.x + self.transform[0] - self.anchor[0]
		self.dest_rect.y = self.y + self.transform[1] - self.anchor[1]
		if self.hit_anchor:
			self.rect.x = (self.x + self.hit_anchor[0]
				+ self.transform[0] - self.anchor[0])
			self.rect.y = (self.y + self.hit_anchor[1]
				+ self.transform[1] - self.anchor[1])
		else:
			self.rect = self.dest_rect
	
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
		if self.velocity:
			self.x += self.velocity[0] * delta * self.speed
			self.y += self.velocity[1] * delta * self.speed
		if self.rotation:
			self.angle += self.rotation * delta * self.speed
			self.image.angle = self.angle
		if self.scaling:
			self.scale += self.scaling * delta * self.speed
			r = self.image.get_rect()
			c = r.center
			r.width *= self.scale
			r.height *= self.scale
			r.center = c
			self.dest_rect = r
			self.image.origin = r.width/2, r.height/2
		if self.fading:
			fading = self.fading * delta * self.speed
			self.image.alpha = min(max(self.image.alpha-fading, 0), 255)
		self.dest_rect.x = self.x + self.transform[0] - self.anchor[0]
		self.dest_rect.y = self.y + self.transform[1] - self.anchor[1]
		if self.hit_anchor:
			self.rect.x = (self.x + self.hit_anchor[0]
				+ self.transform[0] - self.anchor[0])
			self.rect.y = (self.y + self.hit_anchor[1]
				+ self.transform[1] - self.anchor[1])
		else:
			self.rect = self.dest_rect
		
		if self.duration and self.time_spent > abs(self.duration / self.speed):
			self._next_frame()


def keyfr(frame=0, duration=1000, **kwargs):
	"""
	Returns a single keyframe with given parameters

	:param frame: name or number of image for this keyframe
	:param duration: time in milliseconds for this keyframe
	:param angle: degrees of clockwise rotation around a center origin
	:param flipx: set True to flip image horizontally
	:param flipy: set True flip image vertically
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

l = list(range(11,20))
anim1 = keyframes(l, 500, velocity=(15,0), rotation=30)
anim2 = [
	keyfr(11, 500),
	keyfr(12, 500),
	keyfr(13, 500) ]

def main():
	import os, sys, math
	from .tfont import TextureFont
	example_data = os.path.join(os.path.dirname(__file__), 'data', '')

	pg.init()
	window = Window('Testing', (1600,900))
	renderer = Renderer(window)
	clock = pg.time.Clock()
	running = True
	tfont = TextureFont(renderer, None, 48)

	transform = pg.Vector3()
	group = pg.sprite.Group()
	texture = load_texture(renderer, example_data+'sprite.png')
	for x in range(5):
		sprite = GPUAniSprite(texture, 10,14,by_count=True)
		sprite.set_animation(anim1, loop_type='back_forth', loop_count=-3)
		sprite.set_pos(200, 100*x)
		sprite.speed = .5 + (.25*x)
		group.add(sprite)
	sprite.speed = -1
	sprite = GPUAniSprite(sprite.images, 10,14,by_count=True)
	sprite.set_pos(500,20)
	sprite.set_animation(anim2, loop_type='forward', loop_count=-1)
	sprite.set_hitbox((50,50,25,25))
	sprite.set_anchor((40,40))
	GPUAniSprite.draw = GPUAniSprite.draw_debug

	mode = 0
	delta = 0
	frames = 0
	while running:
		frames += 1
		for event in pg.event.get():
			if event.type == pg.QUIT:
				running = False
			elif event.type == pg.KEYDOWN:
				if event.key == pg.K_ESCAPE:
					running = False
				elif event.key == pg.K_f:
					window_mode = window_mode + 1 if window_mode < 3 else 1
					if window_mode == 1:
						window.size = WINDOW_RESOLUTION
						window.set_windowed()
					elif window_mode == 2:
						window.size = SMALL_RESOLUTION
					else:
						window.set_fullscreen(True)
				elif event.key == pg.K_t:
					pass
			elif event.type == pg.MOUSEMOTION:				
				x, y = pg.mouse.get_rel()
				transform.x += x
				transform.y += y

			elif event.type == pg.MOUSEBUTTONDOWN:
				sprite.queue_animation(anim2)
				sprite.queue_animation(anim1, -1)

		tfont.draw('Testing Sprites', 10, 10)
		group.update(delta)
		am = (frames%90)/90
		am = 4 * am*am*am if am < 0.5 else 1 - math.pow(-2 * am + 2, 3) / 2
		sprite.y = 800 * am
		#sprite.y = 600 * (( 1 - (1 - am) ** 4) ) # quarterout
		#sprite.y = 800 * (am * am * am) # quarterin
		#sprite.y = 800 * (1 - math.cos((am * math.pi) / 2)) #sinein
		renderer.draw_color = (255,255,255,255)
		renderer.draw_line((0,800), (1600,800))
		sprite.update(delta)
		pg.sprite.spritecollide(sprite, group, False)
		group.draw()
		sprite.draw()
		renderer.present()
		delta = clock.tick(30)
		renderer.draw_color = (0,0,0,255)
		renderer.clear()

if __name__ == '__main__':
	main()
