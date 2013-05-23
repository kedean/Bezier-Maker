import math
from pyglet import image
from pyglet.gl import *
#from pyglet.graphics import TextureGroup
from pyglet.window import key, mouse
from time import time
import sys
import multiprocessing

TICKS_PER_SEC = 60

""" 
	Calculates the point along the curve at drawing time t, where 0 <= t <= 1.

	Parameters
	----------
	controls : list of tuples of int
		List of the control coordinates to calculate with.
	t : float
		Time interval to calculate at. 0 is the start of the curve and 1 is the end.
	verbose : bool
		If true, the return value is a tuple that includes the normal return value as well as a list of point pairs that form the lines that calculate the point. This can be fed straight into something like opengl's GL_LINES.
	"""
def static_calc_line_layer((controls, t), verbose=False):
	if not verbose:
		return interpolate(list(controls), t)

	control_count = len(controls) - 1
	if control_count == 1:
		return controls[0]
	elif control_count == 0:
		return (0,0)

	sub_controls = list(controls)
	sub_points = []
	max_control = control_count

	for max_control in range(control_count, 0, -1):
		for i in range(0, max_control):
			sub_controls[i] = (
				sub_controls[i][0] + (sub_controls[i+1][0] - sub_controls[i][0]) * t,
				sub_controls[i][1] + (sub_controls[i+1][1] - sub_controls[i][1]) * t
				)
			if i != 0:
				sub_points.extend([sub_controls[i-1][0], sub_controls[i-1][1], sub_controls[i][0], sub_controls[i][1]])
	
	return sub_controls[0], sub_points
def binomial_coefficient(n, i):
	return math.factorial(n) / (math.factorial(i) * math.factorial(n - i))
def interpolate(controls, i):
	if i == 1:
		return controls[-1]
	n = len(controls) - 1
	x, y = 0, 0
	iN = 1.0
	j = 1.0 - i
	jN = float(math.pow(j, n))
	
	for k, c in enumerate(controls):
		multiplier = binomial_coefficient(n, k) * iN * jN
		iN *= i
		jN /= j

		x += c[0] * multiplier
		y += c[1] * multiplier
	
	return (x, y)

class BezierBase(object):
	POINT_REMOVED = 1
	POINT_NOT_FOUND = 2

	def __init__(self, *args, **kwargs):
		super(BezierBase, self).__init__(*args, **kwargs)
		self._throttle = 0.00001
		self._scaleOffsets = (0,0)
		self._scaleFactor = 1
		self._canvasTime = 0

		self._controls = []
		self._points = []
		self._pool = multiprocessing.Pool()
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
	def regenerate(self): #this can probably be optimized, its currently a copy of the c++ implementation
		if len(self._controls) > 0:
			t1 = time()
			self._canvasTime = 0
			intervals = []
			t = 0
			while t < 1:
				intervals.append((self._controls, t))
				t += self._throttle
			if t != 1:
				intervals.append((self._controls, 1))
			self._points = self._pool.map(static_calc_line_layer, intervals)
			t2 = time()
			print "took {0}ms".format((t2 -  t1)*1000)

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
		return static_calc_line_layer((self._controls, t), verbose)
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
		self._color = (0,0,0, 255)
		self._controlColor = (0,0,0, 255)
		self._boundingLineColor = (0,0,0, 255)
		self._animatedLineColor = (0,255,0, 255)

		self._show = {"curve":True, "controls":True, "bounds":True}
		self._invalidated = False
		self._throttle = 0.0001
		self._animating = False
		self._animating_paused = False
		self._stepping = 0
		self._animation_length = 2.0
		self._control_batch = pyglet.graphics.Batch()
		self._curve_batch = pyglet.graphics.Batch()
		self._control_vertices = {}
		self._curve_vertices = None
		self._fps_label = pyglet.text.Label(
						'', font_name='Arial', font_size=18,
						x=20, y=40, anchor_x='left', anchor_y='top',
						color=(0, 0, 0, 255)
						)
		self._show_fps = False
		self._show_buttons = True

		#set up the gui buttons
		self._show_button = Button('-', font_name='Arial', font_size=18,
						x=5, y=self.height - 18, anchor_x='left', anchor_y='top',
						color=(0, 0, 0, 255)
						)
		self._show_button.left_click_event = lambda: (self.toggle_buttons())
		self._show_button.text = ""

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
		self._show_buttons = not self._show_buttons
		self._show_button.text = "-" if self._show_buttons else "+"
	def set_throttle(self, throttle):
		self._throttle = float(throttle)
	def change_detail(self, amount):
		self._throttle += amount
		if self._throttle < 0.01:
			self._throttle = 0.01
		self.invalidate()
	def invalidate(self):
		self._invalidated = True
	def validate(self):
		self._invalidated = False
	def debug(self, val=None):
		if val is None:
			self._show_fps = not self._show_fps
		else:
			self._show_fps = bool(val)
	def make_control_vertices(self, (x,y)):
		return [x-5, y,
				x, y - 5,
				x + 5, y,
				x, y + 5]
	def update(self, dt):
		if self._invalidated:
			self.regenerate()
			self._control_batch = pyglet.graphics.Batch()
			self._curve_batch = pyglet.graphics.Batch()
			
			if len(self._controls) > 0:
				[vert.delete() for c, vert in self._control_vertices.iteritems() if c not in self._controls]
				self._control_vertices = {}
				for c in self._controls:
					if c not in self._control_vertices:
						self._control_vertices[c] = self._control_batch.add(4, GL_QUADS, None, ('v2f/static', self.make_control_vertices(c)))
				curve_points = []
				[curve_points.extend([c[0], c[1]]) for c in self._points]
				self._curve_vertices.delete() if (self._curve_vertices is not None) else None
				self._curve_vertices = self._curve_batch.add(len(curve_points) / 2, GL_LINE_STRIP, None, ('v2f/static', curve_points))
			self.validate()
		if self._animating and not self._animating_paused:
			self._canvasTime += dt / self._animation_length
			if self._canvasTime >= 1.0:
				self.stop_animating()
			else:
				self.calc_frame(self._canvasTime)
		elif self._stepping != 0:
			self._canvasTime += (self._stepping * 0.01) / self._animation_length
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
		self.clear()
		if self._show["curve"]:
			self.draw_curve()
		if self._show["controls"]:
			self.draw_controls()
		if self._show["bounds"]:
			self.draw_bounding_lines()

		if self._animating:
			self.draw_calc_lines()
		if self._show_fps:
			self._fps_label.text = "{0:.02f}".format(pyglet.clock.get_fps())
			self._fps_label.draw()
		self._show_button.draw()
		if self._show_buttons:
			[button.draw() for button in self.buttons]
	def draw_curve(self):
		glColor3f(self._color[0], self._color[1], self._color[2])
		self._curve_batch.draw()
	def draw_controls(self):
		glColor3f(self._controlColor[0], self._controlColor[1], self._controlColor[2], self._controlColor[3])
		self._control_batch.draw()
	def draw_bounding_lines(self):
		glBegin(GL_LINE_STRIP)
		glColor3f(self._boundingLineColor[0], self._boundingLineColor[1], self._boundingLineColor[2])
		for c in self._controls:
			glVertex2f(c[0], c[1])
		glEnd()
	def draw_calc_lines(self):
		p, line_points = static_calc_line_layer((self._controls, self._canvasTime), True)
		glColor3f(self._animatedLineColor[0], self._animatedLineColor[1], self._animatedLineColor[2]);
		pyglet.graphics.draw(len(line_points)/2, GL_LINES, ('v2f', line_points))
		#draw the control for it
		pyglet.graphics.draw(4, GL_QUADS, ('v2f', [
			p[0] - 5, p[1],
			p[0], p[1] - 5,
			p[0] + 5, p[1],
			p[0], p[1] + 5
			]))
	def run(self):
		self.clear_to_2d()
		pyglet.app.run()
	def start_animating(self):
		self._canvasTime = 0
		self._animating = True
		self.calc_frame(0)
		self._animating_paused = False
	def stop_animating(self):
		self._animating = False
		self._animating_paused = False
		self._canvasTime = 0
		self.calc_frame(1)
		self.invalidate()
		self._stepping = 0
	def pause_animating(self):
		self._animating_paused = not self._animating_paused
	def run_clear(self):
		self.stop_animating()
		self.clear_curve()
		self.invalidate()

	#event bindings
	def on_mouse_press(self, x, y, button, modifiers):
		if self._show_buttons:
			for b in self.buttons:
				if b.parse_click(x, y, button):
					return

		if self._show_button.parse_click(x, y, button):
			return

		if button == mouse.LEFT:
			self.add_point(x, y)
			self.invalidate()
		elif button == mouse.RIGHT:
			self.pop_point(5, x, y)
			self.invalidate()
	def on_mouse_motion(self, x, y, dx, dy):
		"""if self._show_buttons:
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
			if modifiers in (0, 1) and not (self._animating and not self._animating_paused):
				if not self._animating:
					self.start_animating()
					self._animating_paused = True

				if modifiers == 1:
					self._stepping = -1
				elif modifiers == 0:
					self._stepping = 1
		elif symbol == key.R:
			self.pop_point_at_index(-1)
			self.invalidate()
		elif symbol == key.D:
			self.debug()
	def on_key_release(self, symbol, modifiers):
		if symbol == key.S:
			self._stepping = 0
	def on_resize(self, width, height):
		pass

	#visual toggles
	def toggle_curve(self, val=None):
		if val is None:
			self._show["curve"] = not self._show["curve"]
		else:
			self._show["curve"] = bool(val)
	def toggle_controls(self, val=None):
		if val is None:
			self._show["controls"] = not self._show["controls"]
		else:
			self._show["controls"] = bool(val)
	def toggle_bounds(self, val=None):
		if val is None:
			self._show["bounds"] = not self._show["bounds"]
		else:
			self._show["bounds"] = bool(val)

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
