from bezier_base import BezierBase, interpolate, static_calc_line_layer

class BezierCollection(object):
	def __init__(self, throttle):
		self.__group_throttle = throttle
		self._curves = [BezierBase(self._group_throttle)]
		self._selections = [[]]
		self._primary_index = 0
	def set_throttle(self, throttle):
		self.__group_throttle = throttle
		for c in self._curves:
			c._throttle = throttle
	def get_primary(self):
		return self._curves[_primary_index]
	def regenerate_all(self):
		[c.regenerate() for c in self._curves]
	def regenerate_primary(self):
		self.get_primary().regenerate()
	def reset_canvas_times(self):
		for c in self._curves:
			c._canvas_time = 0
	def calc_frame_all(self, time):
		for c in self._curves:
			c._canvas_time = time
			c.calc_frame(time)
	def calc_frame_primary(self, time):
		self.get_primary()._canvas_time = time
		self.get_primary().calc_frame(time)

	def get_curve_points(self):
		return [[(int(c[0]), int(c[1])) for c in curve._points] for c in self._curves]
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
		return contols
	def get_bounding_points(self):
		return [[(int(contol[0]), int(contol[1])) for control in c._controls] for c in self._curves]

	def get_calc_lines_all(self):
		return [static_calc_line_layer((c._controls, c._canvas_time), True) for c in self._curves]
	def get_calc_lines_primary(self):
		return static_calc_line_layer((self.get_primary()._controls, self.get_primary()._canvas_time), True)

	def select_from_primary(self, index):
		self._selections[self._primary_index].append(index)
	def reset_selections(self):
		self._selections = [[]] * len(self._curves)
