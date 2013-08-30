from pyglet import image
from pyglet.gl import *
#from pyglet.graphics import TextureGroup
from pyglet.window import key, mouse
import math
import sys

from bezier_base import BezierBase, interpolate, static_calc_line_layer

TICKS_PER_SEC = 60


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
	@staticmethod
	def make_button(filename, y_pos, left_click=lambda:None, right_click=lambda:None, middle_click=lambda:None):
		image = pyglet.image.load(filename)
		button = ImageButton(image, x=0, y=y_pos - image.height)
		button.left_click_event = left_click
		button.right_click_event = right_click
		button.middle_click_event = middle_click
		return button


class BezierCurve(pyglet.window.Window):
	def __init__(self, *args, **kwargs):
		super(BezierCurve, self).__init__(*args, **kwargs)

		self.curves = [BezierBase()]
		self.curve = self.curves[0]
		
		self._color = (0,0,0, 255)
		self._controlColor = (0,0,0, 255)
		self._boundingLineColor = (0,0,0, 255)
		self._animatedLineColor = (0,255,0, 255)
		self._zoom_factor = 1.3
		self._zoom = 1.0
		self._show = {"curve":True, "controls":True, "bounds":True, "fps":False}
		self._invalidated = False
		self._invalidated_all = False
		self._animating = False
		self._apply_all_curves = False
		self._animating_paused = False
		self._stepping = 0
		self._animation_length = 2.0
		self._animation_time = 0.0
		self._control_batch = pyglet.graphics.Batch()
		self._curve_batch = pyglet.graphics.Batch()
		self._control_vertices = {}
		self._curve_vertices = None
		self.selected_indices = []
		self._fps_label = pyglet.text.Label('', font_name='Courier', font_size=13, x=20, y=60, anchor_x='left', anchor_y='top', color=(0, 0, 0, 255))
		self._location_label = pyglet.text.Label('pos = 0, 0', font_name='Courier', font_size=13, x=20, y=40, anchor_x='left', anchor_y='top', color=(0, 0, 0, 255))

		exit_button = ImageButton.make_button("exit.png", self.height, lambda:(sys.exit(0)))
		animate_button = ImageButton.make_button("animate.png", exit_button.y, lambda: (self.start_animating()))
		clear_button = ImageButton.make_button("clear.png", animate_button.y, lambda:(self.run_clear()))
		more_detail_button = ImageButton.make_button("more_detail.png", clear_button.y, lambda:(self.change_detail(-0.01)))
		less_detail_button = ImageButton.make_button("less_detail.png", more_detail_button.y, lambda:(self.change_detail(0.01)))
		more_zoom_button = ImageButton.make_button("more_zoom.png", less_detail_button.y, lambda:(self.zoom(self._zoom_factor)))
		less_zoom_button = ImageButton.make_button("less_zoom.png", more_zoom_button.y, lambda:(self.zoom(1/self._zoom_factor)))
 
		self.buttons = [exit_button, animate_button, clear_button, more_detail_button, less_detail_button, more_zoom_button, less_zoom_button]

		self._doodle_mode = False
		self._doodle_points = []
		self._doodle_batch = pyglet.graphics.Batch()
		self._doodle_vertices = []
		
		self._doodle_tolerance = 5 #pixels of difference in any direction between estimated curve and the drawn line

		#the update loop runs at up to 60fps
		pyglet.clock.schedule_interval(self.update, 1.0 / TICKS_PER_SEC)
	def set_throttle(self, throttle):
		self.curve._throttle = float(throttle)
	def change_detail(self, amount):
		self.curve._throttle += amount
		if self.curve._throttle < 0.01:
			self.curve._throttle = 0.01
		self.invalidate_all()
	def zoom(self, amount):
		self._zoom *= amount
		for curve in self.curves:
			curve.scale(self._zoom, self.width/2, self.height/2)
		self.invalidate_all()
	def invalidate(self):
		self._invalidated = True
	def invalidate_all(self):
		self._invalidated = True
		self._invalidated_all = True
	def validate(self):
		self._invalidated = False
		self._invalidated_all = False
	def debug(self, val=None):
		if val is None:
			self._show["fps"] = not self._show["fps"]
		else:
			self._show["fps"] = bool(val)
	def make_control_vertices(self, (x,y)):
		return [x-5, y,
				x, y - 5,
				x + 5, y,
				x, y + 5]
	def update(self, dt):
		self._fps_label.text = "fps = {0:.02f}".format(pyglet.clock.get_fps())
		
		if self._invalidated:
			if self._doodle_mode:
				doodle_points = []
				self._doodle_batch = pyglet.graphics.Batch()
				[doodle_points.extend([c[0], c[1]]) for c in self._doodle_points]
				if len(doodle_points) > 0:
					self._doodle_vertices = self._doodle_batch.add(len(doodle_points) / 2, GL_LINE_STRIP, None, ('v2f/static', doodle_points))
			else:	
				if self._invalidated_all:
					for curve in self.curves:
						curve.regenerate()
				else:
					self.curve.regenerate()
				self._control_batch = pyglet.graphics.Batch()
				self._curve_batch = pyglet.graphics.Batch()
				
				if len(self.curve._controls) > 0:
					#[vert.delete() for c, vert in self._control_vertices.iteritems() if c not in self.curve._controls]
					"""
					self._control_vertices = {}
					for i, c in enumerate(self.curve._controls):
						if c not in self._control_vertices and i not in self.selected_indices:
							self._control_vertices[c] = self._control_batch.add(4, GL_QUADS, None, ('v2f/static', self.make_control_vertices(c)))
					for curve in self.curves:
						for c in curve._controls:
							if c not in self._control_vertices:
								self._control_vertices[c] = self._control_batch.add(4, GL_QUADS, None, ('v2f/static', self.make_control_vertices(c)))
					"""
					"""
					for curve in self.curves:
						curve_points = []
						[curve_points.extend([c[0], c[1]]) for c in curve._points]
						#self._curve_vertices.delete() if (self._curve_vertices is not None) else None
						self._curve_vertices = self._curve_batch.add(len(curve_points) / 2, GL_LINE_STRIP, None, ('v2f/static', curve_points))
					"""
			self.validate()
		if self._animating and not self._animating_paused:
			self._animation_time += dt / self._animation_length
			self.curve._canvas_time = math.floor(self._animation_time / self.curve._throttle) * self.curve._throttle
			if self.curve._canvas_time >= 1.0:
				self.stop_animating()
			else:
				if self._apply_all_curves:
					for curve in self.curves:
						curve._canvas_time = self.curve._canvas_time
						curve.calc_frame(curve._canvas_time)
				else:
					self.curve.calc_frame(self.curve._canvas_time)
		elif self._stepping != 0:
			self._animation_time += (self._stepping * dt) / self._animation_length
			self.curve._canvas_time = math.floor(self._animation_time / self.curve._throttle) * self.curve._throttle
			if self._apply_all_curves:
				for curve in self.curves:
					curve._canvas_time = self.curve._canvas_time
					curve.calc_frame(curve._canvas_time)
			else:
				self.curve.calc_frame(self.curve._canvas_time)
			if self.curve._canvas_time < 0:
				if self._apply_all_curves:
					for curve in self.curves:
						curve._canvas_time = 0
				else:
					self.curve._canvas_time = 0
			if self.curve._canvas_time > 1.0:
				self.stop_animating()
	def clear_to_2d(self):
		glClearColor(1, 1, 1, 1)
		self.clear()
		width, height = self.get_size()
		glDisable(GL_DEPTH_TEST)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glEnable( GL_LINE_SMOOTH )
		glEnable( GL_POLYGON_SMOOTH )
		glHint( GL_LINE_SMOOTH_HINT, GL_NICEST )
		glHint( GL_POLYGON_SMOOTH_HINT, GL_NICEST )
		glViewport(0, 0, width, height)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		glOrtho(0, width, 0, height, -1, 1)
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
	def on_draw(self):
		self.clear()

		if self._doodle_mode:
			glColor3f(0, 255, 0)
			self._doodle_batch.draw()
		else:
			if self._show["curve"]:
				self.draw_curve()
			if self._show["controls"]:
				self.draw_controls()
			if self._show["bounds"]:
				self.draw_bounding_lines()

			if self._animating:
				self.draw_calc_lines()
			if self._show["fps"]:
				self._fps_label.draw()
				self._location_label.draw()
		[button.draw() for button in self.buttons]
	def draw_curve(self):
		glColor3f(self._color[0], self._color[1], self._color[2])
		#self._curve_batch.draw()
		for curve in self.curves:
			curve_points = []
			[curve_points.extend([c[0], c[1]]) for c in curve._points]
			#self._curve_vertices.delete() if (self._curve_vertices is not None) else None
			pyglet.graphics.draw(len(curve_points) / 2, GL_LINE_STRIP, ('v2f/static', curve_points))
	def draw_controls(self):
		#self._control_batch.draw()
		glColor4f(self._controlColor[0], self._controlColor[1], self._controlColor[2], self._controlColor[3])
		control_verts = []
		for curve in self.curves:
			for i, c in enumerate(curve._controls):
				if curve == self.curve and i in self.selected_indices:
					glColor3f(100, 0, 0)
					pyglet.graphics.draw(4, GL_QUADS, ('v2f/static', self.make_control_vertices(c)))
				else:
					control_verts.extend(self.make_control_vertices(c))
		glColor4f(self._controlColor[0], self._controlColor[1], self._controlColor[2], self._controlColor[3])
		pyglet.graphics.draw(len(control_verts)/2, GL_QUADS, ('v2f/static', control_verts))
			

	def draw_bounding_lines(self):
		glColor3f(self._boundingLineColor[0], self._boundingLineColor[1], self._boundingLineColor[2])
		for curve in self.curves:
			verts = []
			for c in curve._controls:
				verts.append(c[0])
				verts.append(c[1])
			pyglet.graphics.draw(len(verts)/2, GL_LINE_STRIP, ('v2f/static', verts))
	def draw_calc_lines(self):
		if self._apply_all_curves:
			for curve in self.curves:
				p, line_points = static_calc_line_layer((curve._controls, curve._canvas_time), True)
				if line_points != 0:
					glColor3f(self._animatedLineColor[0], self._animatedLineColor[1], self._animatedLineColor[2]);
					pyglet.graphics.draw(len(line_points)/2, GL_LINES, ('v2f', line_points))
					#draw the control for it
					pyglet.graphics.draw(4, GL_QUADS, ('v2f', [
						p[0] - 5, p[1],
						p[0], p[1] - 5,
						p[0] + 5, p[1],
						p[0], p[1] + 5
						]))
		else:
			p, line_points = static_calc_line_layer((self.curve._controls, self.curve._canvas_time), True)
			if line_points != 0:
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
		self.curve._canvas_time = 0
		self._animating = True
		self.curve.calc_frame(0)
		self._animating_paused = False
	def stop_animating(self):
		self._animating = False
		
		self._animating_paused = False
		self._animation_time = 0.0
		for curve in self.curves:
			curve._canvas_time = 0
			curve.calc_frame(1)

		self.invalidate_all() if self._apply_all_curves else self.invalidate()

		self._apply_all_curves = False
		self._stepping = 0
	def pause_animating(self):
		self._animating_paused = not self._animating_paused
	def run_clear(self):
		self.stop_animating()
		self.selected_indices = []
		if self._doodle_mode:
			self._doodle_points = []
			self._doodle_batch = pyglet.graphics.Batch()
		else:
			self.curves = [BezierBase()]
		self.invalidate_all()
	def compare_curve_to_doodle(self):
		pass
	def undoodle(self):
		start = self._doodle_points[0]
		end = self._doodle_points[-1]

		self.curve.add_point(*start)
		self.curve.add_point(*end)

		self.run_clear()
		
	#event bindings
	def on_mouse_press(self, x, y, button, modifiers):
		for b in self.buttons:
			if b.parse_click(x, y, button):
				return

		if self._doodle_mode:
			if button == mouse.LEFT:
				pass
		else:
			if button == mouse.LEFT:
				if modifiers & key.MOD_CTRL:
					self.curves.append(BezierBase())
					self.curve = self.curves[-1]
					self.curve._throttle = self.curves[-2]._throttle
					self.selected_indices = []
					self.curve.add_point(x, y)
					self.stop_animating()
					self.invalidate_all()
				else:
					grabbed_index, point = self.curve.find_point(5, x, y)

					if len(self.selected_indices) > 0 and grabbed_index != self.selected_indices[0]:
						self.invalidate()

					if grabbed_index == -1:
						self.selected_indices = []
						self.curve.add_point(x, y)
						self.invalidate()
					else:
						if modifiers & key.MOD_SHIFT:
							self.selected_indices.append(grabbed_index)
						else:
							self.selected_indices = [grabbed_index]
						self.invalidate()
			elif button == mouse.RIGHT:
				self.selected_indices = []
				self.curve.pop_point(5, x, y)
				self.invalidate()
	def on_mouse_release(self, x, y, button, modifiers):
		if self._doodle_mode:
			if button == mouse.LEFT:
				pass
		else:
			if button == mouse.LEFT:
				self.grabbed_index = -1
	def on_mouse_motion(self, x, y, dx, dy):
		self._location_label.text = "pos = {0}, {1}".format(x, y)
	def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
		self._location_label.text = "pos = {0}, {1}".format(x, y)

		if self._doodle_mode:
			self._doodle_points.append((x,y))
			self.invalidate()
		else:
			for i in set(self.selected_indices):
				existing = self.curve.get_point(i)
				
				self.curve.set_point(i, existing[0] + dx, existing[1] + dy)
				self.invalidate()

	def on_key_press(self, symbol, modifiers):
		if symbol == key.A: #animate it!
			self._apply_all_curves = modifiers & key.MOD_CTRL
			self.start_animating()
		elif symbol == key.C:
			self.run_clear()
		elif symbol == key.P:
			self.pause_animating()
		elif symbol == key.S:
			self._apply_all_curves = modifiers & key.MOD_CTRL
			if not (self._animating and not self._animating_paused):
				if not self._animating:
					self.start_animating()
					self._animating_paused = True

				if modifiers & key.MOD_SHIFT:
					self._stepping = -1
					if self._animation_time == 0:
						self._animation_time = 1.0
				else:
					self._stepping = 1
		elif symbol == key.R:
			if modifiers & key.MOD_SHIFT:
				self.curve.pop_point_at_index(-1)
			else:
				for i in self.selected_indices:
					self.curve.pop_point_at_index(i)
				self.selected_indices = []
			self.invalidate()
		elif symbol == key.D:
			self.debug()
		elif symbol == key.BRACKETRIGHT:
			self.zoom(self._zoom_factor)
		elif symbol == key.BRACKETLEFT:
			self.zoom(1/self._zoom_factor)
		elif symbol == key.T:
			if self._doodle_mode:
				self.undoodle()
			self._doodle_mode = not self._doodle_mode
	def on_key_release(self, symbol, modifiers):
		if symbol == key.S:
			self._stepping = 0
	def on_resize(self, width, height):
		self.clear_to_2d()
		self.invalidate_all()
		exit_button = self.buttons[0]
		animate_button = self.buttons[1]
		clear_button = self.buttons[2]
		more_detail_button = self.buttons[3]
		less_detail_button = self.buttons[4]
		more_zoom_button = self.buttons[5]
		less_zoom_button = self.buttons[6]

		exit_button.y = height - exit_button.height
		animate_button.y = exit_button.y - animate_button.height
		clear_button.y = animate_button.y - clear_button.height
		more_detail_button.y = clear_button.y - more_detail_button.height
		less_detail_button.y = more_detail_button.y - less_detail_button.height
		more_zoom_button.y = less_detail_button.y - more_zoom_button.height
		less_zoom_button.y = more_zoom_button.y - less_zoom_button.height
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
