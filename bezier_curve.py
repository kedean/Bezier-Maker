import gtk
import math
import sys
import time

from bezier_base import BezierBase, interpolate, static_calc_line_layer

TICKS_PER_SEC = 60
MAX_ZOOM_DETAIL = 0.001
"""
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
"""

class BezierCurve(object):
	def __init__(self, *args, **kwargs):

		"""self._fps_label = pyglet.text.Label('', font_name='Courier', font_size=13, x=20, y=60, anchor_x='left', anchor_y='top', color=(0, 0, 0, 255))
		self._location_label = pyglet.text.Label('pos = 0, 0', font_name='Courier', font_size=13, x=20, y=40, anchor_x='left', anchor_y='top', color=(0, 0, 0, 255))

		exit_button = ImageButton.make_button("exit.png", self.height, lambda:(sys.exit(0)))
		animate_button = ImageButton.make_button("animate.png", exit_button.y, lambda: (self.start_animating()))
		clear_button = ImageButton.make_button("clear.png", animate_button.y, lambda:(self.run_clear()))
		more_detail_button = ImageButton.make_button("more_detail.png", clear_button.y, lambda:(self.change_detail(-0.01)))
		less_detail_button = ImageButton.make_button("less_detail.png", more_detail_button.y, lambda:(self.change_detail(0.01)))
		more_zoom_button = ImageButton.make_button("more_zoom.png", less_detail_button.y, lambda:(self.zoom(self._zoom_factor)))
		less_zoom_button = ImageButton.make_button("less_zoom.png", more_zoom_button.y, lambda:(self.zoom(1/self._zoom_factor)))
 
		self.buttons = [exit_button, animate_button, clear_button, more_detail_button, less_detail_button, more_zoom_button, less_zoom_button]
		"""
		self._show = {"curve":True, "controls":True, "bounds":True, "fps":False}

		self._throttle = 0.01
		self._color = (0,0,0, 255)
		self._controlColor = (0,0,0, 255)
		self._boundingLineColor = (0,0,0, 255)
		self._animatedLineColor = (0,255,0, 255)

		self.resetEverything()
		
	def resetEverything(self):
		self.curves = [BezierBase(self._throttle)]
		self.curve = self.curves[0]
		
		self._zoom_factor = 1.3
		self._zoom = 1.0
		
		self._invalidated = False
		self._invalidated_all = False
		self._animating = False
		self._apply_all_curves = False
		self._animating_paused = False
		self._stepping = 0
		self._animation_length = 2.0
		self._animation_time = 0.0
		"""
		self._control_batch = pyglet.graphics.Batch()
		self._curve_batch = pyglet.graphics.Batch()
		"""
		self._control_vertices = {}
		self._curve_vertices = None
		self.selected_indices = []
		"""
		self._doodle_mode = False
		self._doodle_points = []
		self._doodle_batch = pyglet.graphics.Batch()
		self._doodle_vertices = []
		
		self._doodle_tolerance = 5 #pixels of difference in any direction between estimated curve and the drawn line
		"""
	def set_throttle(self, throttle):
		self._throttle = float(throttle)
		for curve in self.curves:
			curve._throttle = self._throttle
	def change_detail(self, amount):
		self._throttle += amount
		if self._throttle < MAX_ZOOM_DETAIL:
			self._throttle = MAX_ZOOM_DETAIL
		for curve in self.curves:
			curve._throttle = self._throttle
		self.invalidate_all()
	def zoom(self, amount):
		self._zoom *= amount
		for curve in self.curves:
			curve.scale(self._zoom, self.width/2, self.height/2)
		self.invalidate_all()
	def invalidate(self):
		self._invalidated = True
		self.canvas.queue_draw()
	def invalidate_all(self):
		self._invalidated = True
		self._invalidated_all = True
		self.canvas.queue_draw()
	def validate(self):
		self._invalidated = False
		self._invalidated_all = False
	def debug(self, val=None):
		if val is None:
			self._show["fps"] = not self._show["fps"]
		else:
			self._show["fps"] = bool(val)
	def make_control_vertices(self, (x,y)):
		return [int(x-5), int(y-5), 10, 10]
	def update(self, dt):
		#self._fps_label.text = "fps = {0:.02f}".format(pyglet.clock.get_fps())
		
		if self._invalidated:
			if self._invalidated_all:
				for curve in self.curves:
					curve.regenerate()
			else:
				self.curve.regenerate()

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
	def clear(self):
		white = self.canvas.get_colormap().alloc(0xffff, 0xffff, 0xffff)
		self.gc.foreground = white
		self.canvas.window.draw_rectangle(self.gc, True, 0, 0, self.width, self.height)
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
		"""if self._show["fps"]:
			self._fps_label.draw()
			self._location_label.draw()"""
		#[button.draw() for button in self.buttons]
	def draw_curve(self):
		self.gc.foreground = self.canvas.get_colormap().alloc(self._color[0], self._color[1], self._color[2])
		#self._curve_batch.draw()
		for curve in self.curves:
			curve_points = [(int(c[0]), int(c[1])) for c in curve._points]
			if len(curve_points) > 0:
				self.canvas.window.draw_lines(self.gc, curve_points)
	def draw_controls(self):
		control_verts = []
		for curve in self.curves:
			for i, c in enumerate(curve._controls):
				if curve == self.curve and i in self.selected_indices:
					self.gc.foreground = self.canvas.get_colormap().alloc(100, 0, 0)
					#pyglet.graphics.draw(4, GL_QUADS, ('v2f/static', self.make_control_vertices(c)))
					vert = self.make_control_vertices(c)
					self.canvas.window.draw_rectangle(self.gc, True, vert[0], vert[1], vert[2], vert[3])
				else:
					control_verts.append(self.make_control_vertices(c))

		self.gc.foreground = self.canvas.get_colormap().alloc(self._controlColor[0], self._controlColor[1], self._controlColor[2])
		for vert in control_verts:
			self.canvas.window.draw_rectangle(self.gc, True, vert[0], vert[1], vert[2], vert[3])
			

	def draw_bounding_lines(self):
		self.gc.foreground = self.canvas.get_colormap().alloc(self._boundingLineColor[0], self._boundingLineColor[1], self._boundingLineColor[2])
		for curve in self.curves:
			verts = []
			for c in curve._controls:
				verts.append((int(c[0]), int(c[1])))
			if len(verts) > 0:
				self.canvas.window.draw_lines(self.gc, verts)
	def draw_calc_lines(self):
		curves = self.curves if self._apply_all_curves else [self.curve]
		
		for curve in self.curves:
			p, line_points = static_calc_line_layer((curve._controls, curve._canvas_time), True)
			if line_points != 0:
				self.gc.foreground = self.canvas.get_colormap().alloc(self._animatedLineColor[0], self._animatedLineColor[1], self._animatedLineColor[2])
				self.canvas.window.draw_segments(self.gc, line_points)
				#draw the control for it
				self.canvas.window.draw_rectangle(self.gc, True, int(p[0])-5, int(p[1])-5, 10, 10)
		
	def quit_app(self, event):
		self.quit = True
	def run(self):
		self.quit = False
		self.window = gtk.Window()
		self.window.set_title("Bezier Maker")
		self.window.connect("destroy", self.quit_app)
		self.width, self.height = 800, 600
		self.canvas = gtk.DrawingArea()
		self.canvas.set_size_request(self.width, self.height)
		
		self.canvas.connect("expose-event", self.canvas_expose)
		
		self.window.add_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.KEY_PRESS_MASK)
		self.window.connect("button_press_event", self.on_mouse_press)
		self.window.connect("key-press-event", self.on_key_press)
		self.window.connect("key-release-event", self.on_key_release)
		self.window.set_resizable(False)
		
		self.canvas.show()
		self.window.add(self.canvas)
		self.window.show_all()
		
		last_update_time = time.time()
		while not self.quit:
			while gtk.events_pending():
				gtk.main_iteration(False)
			now = time.time()
			elapsed = now - last_update_time
			if elapsed >= 1.0 / TICKS_PER_SEC:
				self.update(elapsed)
				last_update_time = now
				self.canvas.queue_draw()


	def canvas_expose(self, canvas, event):
		self.gc = event.window.new_gc()
		self.clear()
		self.on_draw()

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
		self.resetEverything()

	def compare_curve_to_doodle(self):
		pass
	def undoodle(self):
		start = self._doodle_points[0]
		end = self._doodle_points[-1]

		self.curve.add_point(*start)
		self.curve.add_point(*end)

		self.run_clear()
		
	#event bindings
	def on_mouse_press(self, canvas, event):
		x, y, button = event.x, event.y, event.button
		"""for b in self.buttons:
			if b.parse_click(x, y, button):
				return"""

		
		self.stop_animating()
		
		if button == 1:
			if False and modifiers & key.MOD_CTRL:
				self.curves.append(BezierBase(self._throttle))
				self.curve = self.curves[-1]
				self.curve._throttle = self.curves[-2]._throttle
				self.selected_indices = []
				self.curve.add_point(x, y)
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
		elif button == 3:
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

	def on_key_press(self, canvas, event):
		symbol, modifiers = event.keyval, None
		if symbol == ord('a'): #animate it!
			#self._apply_all_curves = modifiers & key.MOD_CTRL
			self.start_animating()
		elif symbol == ord('c'):
			self.run_clear()
		elif symbol == ord('p'):
			self.pause_animating()
		elif symbol == ord('s'):
			#self._apply_all_curves = modifiers & key.MOD_CTRL
			if not (self._animating and not self._animating_paused):
				if not self._animating:
					self.start_animating()
					self._animating_paused = True
				self._stepping = 1
		elif symbol == ord('S'):
			#self._apply_all_curves = modifiers & key.MOD_CTRL
			if not (self._animating and not self._animating_paused):
				if not self._animating:
					self.start_animating()
					self._animating_paused = True

				self._stepping = -1
				if self._animation_time == 0:
					self._animation_time = 1.0
		elif symbol == ord('r'):
			for i in self.selected_indices:
				self.curve.pop_point_at_index(i)
			self.selected_indices = []
			self.invalidate()
		elif symbol == ord('R'):
			self.curve.pop_point_at_index(-1)
			self.invalidate()
		elif symbol == ord('d'):
			self.debug()
		elif symbol == ord(']'):
			self.zoom(self._zoom_factor)
		elif symbol == ord('['):
			self.zoom(1/self._zoom_factor)
	def on_key_release(self, canvas, event):
		symbol = event.keyval
		if symbol == ord('s') or symbol == ord('S'):
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
		color = [int(c, 0) if type(c) != int else c for c in color]
		assert len(color) == 3 or len(color) == 4
		if len(color) == 3:
			color.append(0xffff)
		self._color = color
	def set_control_color(self, color):
		color = [int(c, 0) if type(c) != int else c for c in color]
		assert len(color) == 3 or len(color) == 4
		if len(color) == 3:
			color.append(0xffff)
		self._controlColor = color
	def set_bounds_color(self, color):
		color = [int(c, 0) if type(c) != int else c for c in color]
		assert len(color) == 3 or len(color) == 4
		if len(color) == 3:
			color.append(0xffff)
		self._boundingLineColor = color
	def set_animation_color(self, color):
		color = [int(c, 0) if type(c) != int else c for c in color]
		assert len(color) == 3 or len(color) == 4
		if len(color) == 3:
			color.append(0xffff)
		self._animatedLineColor = color
