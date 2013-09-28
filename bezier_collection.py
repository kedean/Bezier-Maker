from bezier_base import BezierBase, interpolate, static_calc_line_layer

class BezierCollection(object):
	POINT_NOT_FOUND = 2

	def __init__(self, throttle):
		self.__group_throttle = throttle
		self._curves = [BezierBase(self.__group_throttle)]
		self._selections = [[]]
		self._primary_index = 0
	
	@property
	def throttle(self):
		return self.__group_throttle
	@throttle.setter
	def throttle(self, throttle):
		self.__group_throttle = throttle
		for c in self._curves:
			c._throttle = throttle

	@property
	def primary(self):
		return self._curves[self._primary_index]
	def curves(self):
		for c in self._curves:
			yield c
	def selections(self):
		for c, s in zip(self._curves, self._selections):
			yield c, set(s)

	def add_curve(self):
		self._curves.append(BezierBase(self._group_throttle))
		self._primary_index = len(self._curves) - 1
	def regenerate(self, do_all):
		self.regenerate_all() if do_all else self.regenerate_primary()
	def regenerate_all(self):
		[c.regenerate() for c in self._curves]
	def regenerate_primary(self):
		self.primary.regenerate()
	def reset_canvas_time(self, do_all):
		self.reset_canvas_time_all() if do_all else self.reset_canvas_time_primary()
	def reset_canvas_time_all(self):
		for c in self._curves:
			c._canvas_time = 0
	def reset_canvas_time_primary(self):
		self.primary._canvas_time = 0
	def calc_frame(self, time, do_all):
		self.calc_frame_all(time) if do_all else self.calc_frame_primary(time)
	def calc_frame_all(self, time):
		for c in self._curves:
			c._canvas_time = time
			c.calc_frame(time)
	def calc_frame_primary(self, time):
		self.primary._canvas_time = time
		self.primary.calc_frame(time)

	def scale(self, factor, w, h):
		[c.scale(factor, w, h) for c in self._curves]

	def get_curve_points(self):
		return [[(int(c[0]), int(c[1])) for c in curve._points] for curve in self._curves]
	def get_selected_controls(self):
		controls = []
		for curve_index, c in enumerate(self._curves):
			for control_index, control in enumerate(c._controls):
				if control_index in self._selections[curve_index]:
					controls.append((int(control[0]) - 5, int(control[1]) - 5))
		return controls
	def get_deselected_controls(self):
		controls = []
		for curve_index, c in enumerate(self._curves):
			for control_index, control in enumerate(c._controls):
				if control_index not in self._selections[curve_index]:
					controls.append((int(control[0]) - 5, int(control[1]) - 5))
		return controls
	def get_bounding_points(self):
		return [[(int(control[0]), int(control[1])) for control in c._controls] for c in self._curves]

	def get_calc_lines(self, do_all):
		return self.get_calc_lines_all() if do_all else self.get_calc_lines_primary()
	def get_calc_lines_all(self):
		return [static_calc_line_layer((c._controls, c._canvas_time), True) for c in self._curves]
	def get_calc_lines_primary(self):
		return [static_calc_line_layer((self.primary._controls, self.primary._canvas_time), True)]

	def select_from_primary(self, index):
		self._selections[self._primary_index].append(index)
	def select_from_curve(self, curve_index, point_index):
		self._selections[curve_index].append(point_index)
	def deselect_from_curve(self, curve_index, point_index):
		self._selections[curve_index].remove(point_index)
	def reset_selections(self):
		self._selections = [[]] * len(self._curves)

	def find_point(self, r, x, y):
		for curve_index, curve in enumerate(self._curves):
			index, point = curve.find_point(r, x, y)
			if index != -1:
				return index, curve_index, point
		return -1, -1, self.POINT_NOT_FOUND

	def pop_index_from_primary(self, point_index):
		return self.primary.pop_point_at_index(point_index)
	def pop_index_from_curve(self, curve_index, point_index):
		return self._curves[curve_index].pop_point_at_index(point_index)