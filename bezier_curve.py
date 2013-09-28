import gtk
import math
import sys
import time

from bezier_collection import BezierCollection
from bezier_base import BezierBase, interpolate, static_calc_line_layer

TICKS_PER_SEC = 60
MAX_ZOOM_DETAIL = 0.001

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
		self._curve_set = BezierCollection(self._throttle)
		
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
		
		self._control_vertices = {}
		self._curve_vertices = None
		self.selected_indices = []
		
	def set_throttle(self, throttle):
		self._throttle = float(throttle)
		self._curve_set.throttle = throttle
	def change_detail(self, amount):
		self._throttle += amount
		if self._throttle < MAX_ZOOM_DETAIL:
			self._throttle = MAX_ZOOM_DETAIL
		self._curve_set.throttle = self._throttle
		self.invalidate_all()
	def zoom(self, amount):
		self._zoom *= amount
		self._curve_set.scale(self._zoom, self.width/2, self.height/2)
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
		return [int(x-5), int(y-5), 10, 10]
	def update(self, dt):
		#self._fps_label.text = "fps = {0:.02f}".format(pyglet.clock.get_fps())
		
		if self._invalidated:
			self._curve_set.regenerate(self._invalidated_all)
			self._should_redraw = True
			self.validate()
		if self._animating and not self._animating_paused:
			self._animation_time += dt / self._animation_length
			n_canvas_time = math.floor(self._animation_time / self._curve_set.primary._throttle) * self._curve_set.primary._throttle
			if n_canvas_time >= 1.0:
				self.stop_animating()
			else:
				self._curve_set.calc_frame(n_canvas_time, self._apply_all_curves)
			self._should_redraw = True
		elif self._stepping != 0:
			self._animation_time += (self._stepping * dt) / self._animation_length
			n_canvas_time = math.floor(self._animation_time / self._curve_set.primary._throttle) * self._curve_set.primary._throttle
			self._curve_set.calc_frame(n_canvas_time, self._apply_all_curves)
			if n_canvas_time < 0:
				self._curve_set.reset_canvas_time(self._apply_all_curves)
			elif n_canvas_time > 1.0:
				self.stop_animating()
			self._should_redraw = True
	def clear(self):
		self.gc.foreground = self.white
		self.canvas.draw_rectangle(self.gc, True, 0, 0, self.width, self.height)
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
		[self.canvas.draw_lines(self.gc, points) for points in self._curve_set.get_curve_points() if len(points) > 0]
	def draw_controls(self):
		self.gc.foreground = self.canvas.get_colormap().alloc(self._controlColor[0], self._controlColor[1], self._controlColor[2])
		[self.canvas.draw_rectangle(self.gc, True, v[0], v[1], 10, 10) for v in self._curve_set.get_deselected_controls()]

		self.gc.foreground = self.canvas.get_colormap().alloc(abs(0xffff - self._controlColor[0]), abs(0xffff - self._controlColor[1]), abs(0xffff - self._controlColor[2]))
		[self.canvas.draw_rectangle(self.gc, True, v[0], v[1], 10, 10) for v in self._curve_set.get_selected_controls()]

	def draw_bounding_lines(self):
		self.gc.foreground = self.canvas.get_colormap().alloc(self._boundingLineColor[0], self._boundingLineColor[1], self._boundingLineColor[2])
		[self.canvas.draw_lines(self.gc, verts) for verts in self._curve_set.get_bounding_points() if len(verts) > 0]
	def draw_calc_lines(self):
		self.gc.foreground = self.canvas.get_colormap().alloc(self._animatedLineColor[0], self._animatedLineColor[1], self._animatedLineColor[2])
		for p, line_points in self._curve_set.get_calc_lines(self._apply_all_curves):
			if line_points != 0:
				self.canvas.draw_segments(self.gc, line_points)
				self.canvas.draw_rectangle(self.gc, True, int(p[0])-5, int(p[1])-5, 10, 10)
		
	def quit_app(self, event):
		self.quit = True
	def run(self):
		self.quit = False

		self.window = gtk.Window()
		self.window.set_title("Bezier Maker")
		self.window.connect("destroy", self.quit_app)
		self.width, self.height = 800, 600
		self.screen = gtk.DrawingArea()
		self.screen.set_size_request(self.width, self.height)
		
		self.screen.connect("expose-event", self.canvas_expose)
		
		self.window.add_events(gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.KEY_PRESS_MASK | gtk.gdk.KEY_RELEASE_MASK)
		self.window.connect("button-press-event", self.on_mouse_press)
		self.window.connect("button-release-event", self.on_mouse_release)
		self.window.connect("key-press-event", self.on_key_press)
		self.window.connect("key-release-event", self.on_key_release)
		self.window.connect("motion-notify-event", self.on_mouse_drag)
		self.window.set_resizable(False)
		
		self.screen.show()
		self.window.add(self.screen)
		self.window.show_all()

		self.canvas = gtk.gdk.Pixmap(self.screen.window, self.width, self.height)
		self.white = self.canvas.get_colormap().alloc(0xffff, 0xffff, 0xffff)

		self._should_redraw = True

		self._shift_down = False
		self._dragging_origin = None
		
		last_update_time = time.time()
		while not self.quit:
			while gtk.events_pending():
				gtk.main_iteration(False)
			now = time.time()
			elapsed = now - last_update_time
			if elapsed >= 1.0 / TICKS_PER_SEC:
				self.update(elapsed)
				last_update_time = now
				self.full_redraw()


	def canvas_expose(self, canvas, event):
		self.gc = event.window.new_gc()
		self._should_redraw = True
		self.full_redraw()
	def full_redraw(self):
		if self._should_redraw:
			self._should_redraw = False
			self.on_draw()
			self.screen.window.draw_drawable(self.screen.get_style().fg_gc[gtk.STATE_NORMAL], self.canvas, 0, 0, 0, 0, self.width, self.height)

	def start_animating(self):
		self._curve_set.reset_canvas_time(True)
		self._animating = True
		self._curve_set.calc_frame(0, self._apply_all_curves)
		self._animating_paused = False
	def stop_animating(self):
		self._animating = False
		
		self._animating_paused = False
		self._animation_time = 0.0
		self._curve_set.calc_frame(1, True)

		self.invalidate_all() if self._apply_all_curves else self.invalidate()

		self._apply_all_curves = False
		self._stepping = 0
	def pause_animating(self):
		self._animating_paused = not self._animating_paused
	def run_clear(self):
		self.resetEverything()
		self.clear()
		self.invalidate_all()
		
	#event bindings
	def on_mouse_press(self, canvas, event):
		x, y, button = event.x, event.y, event.button
		
		self._dragging_origin = (x, y)
		self.stop_animating()
		grabbed_index, curve_index, point = self._curve_set.find_point(5, x, y)
		
		if button == 1:
			if point == self._curve_set.POINT_NOT_FOUND:
				self._curve_set.reset_selections()
				self._curve_set.primary.add_point(x, y)
			else:
				if not self._shift_down: #shift means add to the collection, so if theres no shifting then old selections are invalid
					self._curve_set.reset_selections()
				self._curve_set.select_from_curve(curve_index, grabbed_index)
		elif button == 3:
			self._curve_set.pop_index_from_curve(curve_index, grabbed_index)
		
		self.invalidate()
	def on_mouse_release(self, canvas, event):
		self._dragging_origin = None
	def on_mouse_motion(self, x, y, dx, dy):
		self._location_label.text = "pos = {0}, {1}".format(x, y)
	def on_mouse_drag(self, canvas, event):
		#self._location_label.text = "pos = {0}, {1}".format(x, y)
		
		if self._dragging_origin is not None:
			x, y = self._dragging_origin
			dx, dy = event.x - x, event.y - y
			self._dragging_origin = (event.x, event.y) #the d is per iteration of this function, so next time it should be d from here
			for curve, selections in self._curve_set.selections():
				for i in selections:
					existing_x, existing_y = curve.get_point(i)
					curve.set_point(i, existing_x + dx, existing_y + dy)
			self.invalidate()

	def on_key_press(self, canvas, event):
		symbol, modifiers = event.keyval, None
		if symbol == 65505: #shift down
			self._shift_down = True
		elif symbol == ord('a'): #animate it!
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
			for curve, selections in self._curve_set.selections():
				for i in reversed(list(selections)):
					curve.pop_point_at_index(i)
			self._curve_set.reset_selections()
			self.invalidate()
		elif symbol == ord('R'):
			self._curve_set.primary.pop_point_at_index(-1)
			self.invalidate()
		elif symbol == ord('d'):
			self.debug()
		elif symbol == ord(']'):
			self.zoom(self._zoom_factor)
		elif symbol == ord('['):
			self.zoom(1/self._zoom_factor)
	def on_key_release(self, canvas, event):
		symbol = event.keyval
		if symbol == 65505: #shift up
			self._shift_down = False
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
