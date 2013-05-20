import math
from pyglet import image
from pyglet.gl import *
#from pyglet.graphics import TextureGroup
from pyglet.window import key, mouse
from time import time

TICKS_PER_SEC = 60

class BezierBase(object):
	POINT_REMOVED = 1
	POINT_NOT_FOUND = 2

	def __init__(self, *args, **kwargs):
		super(BezierBase, self).__init__(*args, **kwargs)
		self._color = (0,0,0)
		self._controlColor = (0,0,0)
		self._boundingLineColor = (0,0,0)
		self._animatedLineColor = (0,255,0)
		self._throttle = 0.00001
		self._scaleOffsets = (0,0)
		self._scaleFactor = 1
		self._canvasTime = 0

		self._controls = []
		self._points = []
	def add_point(self, a, b=None):
		if b is None: #assume a is a two-tuple value
			assert(len(a) == 2)
			self._controls.append(a)
		else:
			a = int(a)
			b = int(b)
			self._controls.append((a, b))
	def pop_point(self, range, a, b=None):
		if b is None: #assume a is a two-tuple value
			assert(len(a) == 2)
			return self.pop_point(range, a[0], a[1])

		#else
		x = int(a)
		y = int(b)
		range_2 = range**2
		for c in self._controls:
			if (c[0] - x)**2 + (c[1] - y)**2 <= range_2:
				self._controls.remove(c)
				return cf

		return self.POINT_NOT_FOUND
	def pop_point_at_index(self, index):
		if abs(index) >= len(self._controls):
			return self.POINT_NOT_FOUND
		elif index < 0: #negative indexing
			index = len(self._controls) + index
		p = self._controls.pop(index)
		return p
	def scale(self, factor, (centerX, centerY)):
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
			self._canvasTime = 0
	def calc_line_layer(self, t, draw=False):
		base_max_control = len(self._controls) - 1
		if base_max_control == 0:
			return self._controls[0]
		elif base_max_control == -1:
			return (0,0)

		sub_controls = list(self._controls)

		for max_control in range(base_max_control, 0, -1):
			for i in range(0, max_control):
				sub_controls[i] = (
					sub_controls[i][0] + (sub_controls[i+1][0] - sub_controls[i][0]) * t,
					sub_controls[i][1] + (sub_controls[i+1][1] - sub_controls[i][1]) * t
					)
				if draw and i != 0:
					glColor3f(self._animatedLineColor[0], self._animatedLineColor[1], self._animatedLineColor[2]);
					pyglet.graphics.draw(2, GL_LINES, ('v2f', (sub_controls[i-1][0], sub_controls[i-1][1], sub_controls[i][0], sub_controls[i][1])))
		return sub_controls[0]
	def calc_frame(self, t):
		if len(self._controls) != 0:
			if t == 0:
				self._points = []
			elif t < 1:
				p = self.calc_line_layer(t)
				if len(self._points) == 0 or p != self._points[-1]:
					self._points.append(p)
		self._canvasTime = t
	def clear_curve(self):
		self._scaleFactor = 1
		self._scaleOffsets = (0,0)
		self._controls = []
		self._points = []

class BezierCurve(BezierBase, pyglet.window.Window):
	def __init__(self, *args, **kwargs):
		super(BezierCurve, self).__init__(*args, **kwargs)
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
		self.fps_label = pyglet.text.Label('', font_name='Arial', font_size=18,
		            x=10, y=self.height - 10, anchor_x='left', anchor_y='top',
		            color=(0, 0, 0, 255))
		self.show_fps = False
		pyglet.clock.schedule_interval(self.update, 1.0 / TICKS_PER_SEC)
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
		self.draw_curve()
		self.draw_controls()
		self.draw_bounding_lines()
		if self.animating:
			self.draw_calc_lines()
		if self.show_fps:
			self.fps_label.text = "{0:.02f}".format(pyglet.clock.get_fps())
			self.fps_label.draw()
	def draw_curve(self):
		self.curve_batch.draw()
	def draw_controls(self):
		glColor3f(self._color[0], self._color[1], self._color[2])
		self.control_batch.draw()
	def draw_bounding_lines(self):
		glBegin(GL_LINE_STRIP)
		glColor3f(self._boundingLineColor[0], self._boundingLineColor[1], self._boundingLineColor[2])
		for c in self._controls:
			glVertex2f(c[0], c[1])
		glEnd()
	def draw_calc_lines(self):
		p = self.calc_line_layer(self._canvasTime, True)
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
	def on_mouse_press(self, x, y, button, modifiers):
		if button == mouse.LEFT:
			self.add_point(x, y)
			self.invalidate()
		elif button == mouse.RIGHT:
			self.pop_point(5, x, y)
			self.invalidate()

	def on_mouse_motion(self, x, y, dx, dy):
		pass

	def on_key_press(self, symbol, modifiers):
		if symbol == key.A: #animate it!
			self.start_animating()
		elif symbol == key.C:
			self.stop_animating()
			self.clear_curve()
			self.invalidate()
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