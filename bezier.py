import math
from pyglet import image
from pyglet.gl import *
#from pyglet.graphics import TextureGroup
from pyglet.window import key, mouse
from time import time
import sys

TICKS_PER_SEC = 60

class BezierBase(object):
	POINT_REMOVED = 1
	POINT_NOT_FOUND = 2

	def __init__(self, *args, **kwargs):
		super(BezierBase, self).__init__(*args, **kwargs)
		self._color = (0,0,0, 255)
		self._controlColor = (0,0,0, 255)
		self._boundingLineColor = (0,0,0, 255)
		self._animatedLineColor = (0,255,0, 255)
		self._throttle = 0.00001
		self._scaleOffsets = (0,0)
		self._scaleFactor = 1
		self._canvasTime = 0

		self._controls = []
		self._points = []
	""" 
	Adds a control point to the curve parameters. Regeneration is not performed automatically.

	Parameters
	----------
	x : int
		The x coordinate of the control point.
	y : int
		The y coordinate of the control point.
	"""
	def add_point(self, x, y):
		self._controls.append((int(x), int(y)))	
	""" 
	Removes a control point from the curve parameters, within a given variation of space. Regeneration is not performed automatically.

	Parameters
	----------
	range : int
		The first coordinate with this radius is the point that is removed. Ordering is outward from the x,y center. For points the same distance from the center, a FIFO ordering is used.
	x : int
		The x coordinate of the control point.
	y : int
		The y coordinate of the control point.
	"""
	def pop_point(self, range, x, y):
		x = int(x)
		y = int(y)
		range_2 = range**2
		for c in self._controls:
			if (c[0] - x)**2 + (c[1] - y)**2 <= range_2:
				self._controls.remove(c)
				return c

		return self.POINT_NOT_FOUND
	""" 
	Removes the indexed control point from the curve parameters. Regeneration is not performed.

	Parameters
	----------
	index : int
		Index of the controls list at which to remove. Negative numbers are treated as a distance from the end of the last, so -1 will be the last item added.
	"""
	def pop_point_at_index(self, index):
		if abs(index) >= len(self._controls):
			return self.POINT_NOT_FOUND
		elif index < 0: #negative indexing
			index = len(self._controls) + index
		p = self._controls.pop(index)
		return p
	""" 
	Shifts all control points out or in by a given factor, with shifting relative to the given center. Regeneration is not performed.

	Parameters
	----------
	factor : float
		Multiplicative factor by which to shift.
	centerX : int
		The x coordinate of the center point.
	centerY : int
		The y coordinate of the center point.
	"""
	def scale(self, factor, centerX, centerY):
		offsetX = centerX * (factor-1)
		offsetY = centerY * (factor-1)
		self._controls = [
			(
				(c[0] + self._scaleOffsets[0]) / self._scaleFactor,
				(c[1] + self._scaleOffsets[1]) / self._scaleFactor
			)
			for c in self._controls
		]

		if self._canvasTime != 0:
			max_t = self._canvasTime
			t = 0
			while t < max_t:
				self.calc_frame(t)
				t += self._throttle
			self.calc_frame(max_t)
		else:
			pass

		self._scaleFactor = factor
		self._scaleOffsets = (offsetX, offsetY)
	#math methods
	""" 
	Recalculates and stores the points that form the curve itself, based on the current set of control points.

	Parameters
	----------
	
	"""
	def generate(self): #this can probably be optimized, its currently a copy of the c++ implementation
		if len(self._controls) > 0:
			#maybe use list comps?
			self._points = []
			t = 0
			while t < 1:
				p = self.calc_line_layer(t)
				if len(self._points) == 0 or p != self._points[-1]:
					self._points.append(p)
				t += self._throttle
			if t != 1:
				p = self.calc_line_layer(1)
				if len(self._points) == 0 or p != self._points[-1]:
					self._points.append(p)
			self._canvasTime = 0
	""" 
	Calculates the point along the curve at drawing time t, where 0 <= t <= 1.

	Parameters
	----------
	t : float
		Time interval to calculate at. 0 is the start of the curve and 1 is the end.
	verbose : bool
		If true, the return value is a tuple that includes the normal return value as well as a list of point pairs that form the lines that calculate the point. This can be fed straight into something like opengl's GL_LINES.
	"""
	def calc_line_layer(self, t, verbose=False):
		base_max_control = len(self._controls) - 1
		if base_max_control == 0:
			return self._controls[0]
		elif base_max_control == -1:
			return (0,0)

		sub_controls = list(self._controls)

		sub_points = []

		for max_control in range(base_max_control, 0, -1):
			for i in range(0, max_control):
				sub_controls[i] = (
					sub_controls[i][0] + (sub_controls[i+1][0] - sub_controls[i][0]) * t,
					sub_controls[i][1] + (sub_controls[i+1][1] - sub_controls[i][1]) * t
					)
				if i != 0:
					sub_points.extend([sub_controls[i-1][0], sub_controls[i-1][1], sub_controls[i][0], sub_controls[i][1]])
		if verbose:
			return sub_controls[0], sub_points
		else:
			return sub_controls[0]
	""" 
	Calculates for the given time and progressively adds it to the points list. Used for animating, as successive calls with increasing t's will construct the curve.

	Parameters
	----------
	t : float
		Time interval to calculate at. 0 is the start of the curve and 1 is the end.
	"""
	def calc_frame(self, t):
		if len(self._controls) != 0:
			if t == 0:
				self._points = []
			elif t < 1:
				p = self.calc_line_layer(t)
				if len(self._points) == 0 or p != self._points[-1]:
					self._points.append(p)
		self._canvasTime = t
	""" 
	Removes all values, equivalent to deleting the BezierBase object and making a new one.

	Parameters
	----------
	"""
	def clear_curve(self):
		self._scaleFactor = 1
		self._scaleOffsets = (0,0)
		self._controls = []
		self._points = []

class Button(pyglet.text.Label):
	left_click_event = lambda:None
	right_click_event = lambda:None
	middle_click_event = lambda:None

	def parse_click(self, x, y, mouse_button):
		if x > self.x and x < self.x + self.content_width and y < self.y and y > self.y - self.content_height:
			if mouse_button == mouse.LEFT:
				self.left_click_event()
			elif mouse_button == mouse.RIGHT:
				self.right_click_event()
			elif mouse_button == mouse.MIDDLE:
				self.middle_click_event()
			return True
		else:
			return False
	def hovering(self, x, y):
		return (x > self.x and x < self.x + self.content_width and y < self.y and y > self.y - self.content_height)

class ImageButton(pyglet.sprite.Sprite):
	left_click_event = lambda:None
	right_click_event = lambda:None
	middle_click_event = lambda:None

	def parse_click(self, x, y, mouse_button):
		if x > self.x and x < self.x + self.width and y > self.y and y < self.y + self.height:
			if mouse_button == mouse.LEFT:
				self.left_click_event()
			elif mouse_button == mouse.RIGHT:
				self.right_click_event()
			elif mouse_button == mouse.MIDDLE:
				self.middle_click_event()
			return True
		else:
			return False
	def hovering(self, x, y):
		return (x > self.x and x < self.x + self.width and y < self.y and y > self.y - self.height)


class BezierCurve(BezierBase, pyglet.window.Window):
	def __init__(self, *args, **kwargs):
		super(BezierCurve, self).__init__(*args, **kwargs)
		self.show = {"curve":True, "controls":True, "bounds":True}
		self.invalidated = False
		self._throttle = 0.0001
		self.animating = False
		self.animating_paused = False
		self.stepping = 0
		self.animation_length = 2.0
		self.control_batch = pyglet.graphics.Batch()
		self.curve_batch = pyglet.graphics.Batch()
		self.control_vertices = {}
		self.curve_vertices = None
		self.fps_label = pyglet.text.Label(
						'', font_name='Arial', font_size=18,
						x=20, y=40, anchor_x='left', anchor_y='top',
						color=(0, 0, 0, 255)
						)
		self.show_fps = False
		self.show_buttons = True

		#set up the gui buttons
		self.show_button = Button('-', font_name='Arial', font_size=18,
						x=5, y=self.height - 18, anchor_x='left', anchor_y='top',
						color=(0, 0, 0, 255)
						)
		self.show_button.left_click_event = lambda: (self.toggle_buttons())
		self.show_button.text = ""

		exit_image = pyglet.image.load("exit.png")
		exit_button = ImageButton(exit_image,
						x=0, y=self.height - exit_image.height
						)
		exit_button.left_click_event = lambda: (sys.exit(0))

		animate_image = pyglet.image.load("animate.png")
		animate_button = ImageButton(animate_image,
						x=0, y=exit_button.y - animate_image.height
						)
		animate_button.left_click_event = lambda: (self.start_animating())

		clear_image = pyglet.image.load("clear.png")
		clear_button = ImageButton(clear_image,
						x=0, y=animate_button.y - clear_image.height
						)
		clear_button.left_click_event = lambda: (self.run_clear())

		more_detail_image = pyglet.image.load("more_detail.png")
		more_detail_button = ImageButton(more_detail_image,
						x=0, y=clear_button.y - more_detail_image.height
						)
		more_detail_button.left_click_event = lambda: (self.change_detail(-0.01))

		less_detail_image = pyglet.image.load("less_detail.png")
		less_detail_button = ImageButton(less_detail_image,
						x=0, y=more_detail_button.y - less_detail_image.height
						)
		less_detail_button.left_click_event = lambda: (self.change_detail(0.01))

		self.buttons = [exit_button, animate_button, clear_button, more_detail_button, less_detail_button]

		#the update loop runs at up to 60fps
		pyglet.clock.schedule_interval(self.update, 1.0 / TICKS_PER_SEC)
	def toggle_buttons(self):
		self.show_buttons = not self.show_buttons
		self.show_button.text = "-" if self.show_buttons else "+"
	def set_throttle(self, throttle):
		self._throttle = float(throttle)
	def change_detail(self, amount):
		self._throttle += amount
		if self._throttle < 0.01:
			self._throttle = 0.01
		self.invalidate()
	def invalidate(self):
		self.invalidated = True
	def validate(self):
		self.invalidated = False
	def debug(self, val=None):
		if val is None:
			self.show_fps = not self.show_fps
		else:
			self.show_fps = bool(val)
	def make_control_vertices(self, (x,y)):
		return [x-5, y, 0,
				x, y - 5, 0,
				x + 5, y, 0,
				x, y + 5, 0]
	def update(self, dt):
		if self.invalidated:
			self.generate()
			self.control_batch = pyglet.graphics.Batch()
			self.curve_batch = pyglet.graphics.Batch()
			
			if len(self._controls) > 0:
				[vert.delete() for c, vert in self.control_vertices.iteritems() if c not in self._controls]
				self.control_vertices = {}
				for c in self._controls:
					if c not in self.control_vertices:
						self.control_vertices[c] = self.control_batch.add(4, GL_QUADS, None, ('v3f/static', self.make_control_vertices(c)))
				curve_points = []
				[curve_points.extend([c[0], c[1], 0]) for c in self._points]
				self.curve_vertices.delete() if (self.curve_vertices is not None) else None
				self.curve_vertices = self.curve_batch.add(len(curve_points) / 3, GL_LINE_STRIP, None, ('v3f/static', curve_points))
			self.validate()
		if self.animating and not self.animating_paused:
			self._canvasTime += dt / self.animation_length
			if self._canvasTime >= 1.0:
				self.stop_animating()
			else:
				self.calc_frame(self._canvasTime)
		elif self.stepping != 0:
			self._canvasTime += (self.stepping * 0.01) / self.animation_length
			self.calc_frame(self._canvasTime)
			if self._canvasTime < 0:
				self._canvasTime = 0
			if self._canvasTime > 1.0:
				self.stop_animating()
	def clear_to_2d(self):
		glClearColor(1, 1, 1, 1)
		self.clear()
		width, height = self.get_size()
		glDisable(GL_DEPTH_TEST)
		glViewport(0, 0, width, height)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		glOrtho(0, width, 0, height, -1, 1)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
	def on_draw(self):
		self.clear_to_2d()
		if self.show["curve"]:
			self.draw_curve()
		if self.show["controls"]:
			self.draw_controls()
		if self.show["bounds"]:
			self.draw_bounding_lines()

		if self.animating:
			self.draw_calc_lines()
		if self.show_fps:
			self.fps_label.text = "{0:.02f}".format(pyglet.clock.get_fps())
			self.fps_label.draw()
		self.show_button.draw()
		if self.show_buttons:
			[button.draw() for button in self.buttons]
	def draw_curve(self):
		glColor3f(self._color[0], self._color[1], self._color[2])
		self.curve_batch.draw()
	def draw_controls(self):
		glColor3f(self._controlColor[0], self._controlColor[1], self._controlColor[2], self._controlColor[3])
		self.control_batch.draw()
	def draw_bounding_lines(self):
		glBegin(GL_LINE_STRIP)
		glColor3f(self._boundingLineColor[0], self._boundingLineColor[1], self._boundingLineColor[2])
		for c in self._controls:
			glVertex2f(c[0], c[1])
		glEnd()
	def draw_calc_lines(self):
		p, line_points = self.calc_line_layer(self._canvasTime, True)
		glColor3f(self._animatedLineColor[0], self._animatedLineColor[1], self._animatedLineColor[2]);
		pyglet.graphics.draw(len(line_points)/2, GL_LINES, ('v2f', line_points))
		#draw the control for it
		glBegin(GL_QUADS)
		glVertex2f(p[0] - 5, p[1])
		glVertex2f(p[0], p[1] - 5)
		glVertex2f(p[0] + 5, p[1])
		glVertex2f(p[0], p[1] + 5)
		glEnd()
	def run(self):
		pyglet.app.run()
	def start_animating(self):
		self._canvasTime = 0
		self.animating = True
		self.calc_frame(0)
		self.animating_paused = False
	def stop_animating(self):
		self.animating = False
		self.animating_paused = False
		self._canvasTime = 0
		self.calc_frame(1)
		self.invalidate()
		self.stepping = 0
	def pause_animating(self):
		self.animating_paused = not self.animating_paused
	def run_clear(self):
		self.stop_animating()
		self.clear_curve()
		self.invalidate()

	#event bindings
	def on_mouse_press(self, x, y, button, modifiers):
		if self.show_buttons:
			for b in self.buttons:
				if b.parse_click(x, y, button):
					return

		if self.show_button.parse_click(x, y, button):
			return

		if button == mouse.LEFT:
			self.add_point(x, y)
			self.invalidate()
		elif button == mouse.RIGHT:
			self.pop_point(5, x, y)
			self.invalidate()
	def on_mouse_motion(self, x, y, dx, dy):
		"""if self.show_buttons:
			for b in self.buttons:
				if b.hovering(x, y):
					b.color = (0, 0, 100, 255)
				else:
					b.color = (0, 0, 0, 255)"""
		pass

	def on_key_press(self, symbol, modifiers):
		if symbol == key.A: #animate it!
			self.start_animating()
		elif symbol == key.C:
			self.run_clear()
		elif symbol == key.P:
			self.pause_animating()
		elif symbol == key.S:
			if modifiers in (0, 1) and not (self.animating and not self.animating_paused):
				if not self.animating:
					self.start_animating()
					self.animating_paused = True

				if modifiers == 1:
					self.stepping = -1
				elif modifiers == 0:
					self.stepping = 1
		elif symbol == key.R:
			self.pop_point_at_index(-1)
			self.invalidate()
		elif symbol == key.D:
			self.debug()
	def on_key_release(self, symbol, modifiers):
		if symbol == key.S:
			self.stepping = 0
	def on_resize(self, width, height):
		pass

	#visual toggles
	def toggle_curve(self, val=None):
		if val is None:
			self.show["curve"] = not self.show["curve"]
		else:
			self.show["curve"] = bool(val)
	def toggle_controls(self, val=None):
		if val is None:
			self.show["controls"] = not self.show["controls"]
		else:
			self.show["controls"] = bool(val)
	def toggle_bounds(self, val=None):
		if val is None:
			self.show["bounds"] = not self.show["bounds"]
		else:
			self.show["bounds"] = bool(val)

	def set_curve_color(self, color):
		color = list(color)
		assert len(color) == 3 or len(color) == 4
		if len(color) == 3:
			color.append(255)
		self._color = color
	def set_control_color(self, color):
		color = list(color)
		assert len(color) == 3 or len(color) == 4
		if len(color) == 3:
			color.append(255)
		self._controlColor = color
	def set_bounds_color(self, color):
		color = list(color)
		assert len(color) == 3 or len(color) == 4
		if len(color) == 3:
			color.append(255)
		self._boundingLineColor = color
	def set_animation_color(self, color):
		color = list(color)
		assert len(color) == 3 or len(color) == 4
		if len(color) == 3:
			color.append(255)
		self._animatedLineColor = color
