from bezier_base import BezierBase, interpolate, static_calc_line_layer

class BezierCollection(object):
	def __init__(self, throttle):
		self.__group_throttle = throttle
		self._curves = [BezierBase(self._group_throttle)]
		self._primary = self._curves[0]
	def set_throttle(self, throttle):
		self.__group_throttle = throttle
		for c in self._curves:
			c._throttle = throttle
	def get_primary(self):
		return self._primary
	def regenerate_all(self):
		[c.regenerate() for c in self._curves]
	def regenerate_primary(self):
		self._primary.regenerate()
	def reset_canvas_times(self):
		for c in self._curves:
			c._canvas_time = 0
	def calc_frame_all(self, time):
		for c in self._curves:
			c._canvas_time = time
			c.calc_frame(time)
	def calc_frame_primary(self, time):
		self._primary._canvas_time = time
		self._primary.calc_frame(time)

	def get_curve_points(self):
		return [[(int(c[0]), int(c[1])) for c in curve._points] for c in self._curves]
	def get_selected_controls(self):
		pass
	def get_deselected_controls(self):
		pass
	def get_bounding_points(self):
		pass
	def get_calc_lines_all(self):
		pass
	def get_calc_lines_primary(self):
		pass
