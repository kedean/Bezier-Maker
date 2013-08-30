import math
from time import time
import sys
import multiprocessing

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
	#if not verbose:
	#	return interpolate(list(controls), t)

	control_count = len(controls) - 1
	if control_count == 1:
		return [controls[0]]
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
	
	if verbose:
		return sub_controls[0], sub_points
	else:
		return sub_controls[0]

def binomial_coefficient(n, i):
	return math.factorial(n) / (math.factorial(i) * math.factorial(n - i))
def interpolate((controls, i)):
	if i == 1:
		return controls[-1]
	n = len(controls) - 1
	x, y = 0, 0
	iN = 1.0
	j = 1.0 - i
	jN = math.pow(j, n)
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

	def __init__(self):
		#super(BezierBase, self).__init__(*args, **kwargs)
		self._throttle = 0.00001
		self._scaleOffsets = (0,0)
		self._scaleFactor = 1
		self._canvas_time = 0

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
		i, c = self.find_point(range, x, y)
		if i != -1:
			self._controls.remove(c)
		return c
	
	""" 
	Gets a control point from the curve parameters, within a given variation of space. Regeneration is not performed automatically.

	Parameters
	----------
	range : int
		The first coordinate with this radius is the point that is removed. Ordering is outward from the x,y center. For points the same distance from the center, a FIFO ordering is used.
	x : int
		The x coordinate of the control point.
	y : int
		The y coordinate of the control point.
	"""
	def find_point(self, range, x, y):
		x = int(x)
		y = int(y)
		range_2 = range**2
		for i, c in enumerate(self._controls):
			if (c[0] - x)**2 + (c[1] - y)**2 <= range_2:
				return i, c

		return -1, self.POINT_NOT_FOUND

	""" 
	Alters the point at the given index to have the given coordinates.

	Parameters
	----------
	index : int
		Index of the point to alter.
	x : int
		The x coordinate of the new control point.
	y : int
		The y coordinate of the new control point.
	"""

	def set_point(self, index, x, y):
		try:
			self._controls[index] = (int(x), int(y))
			return True 
		except:
			return False

	""" 
	Gets a point at a given index.

	Parameters
	----------
	index : int
		index of the point to return
	"""
	def get_point(self, index):
		try:
			return self._controls[index]
		except:
			return None

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
				(((c[0] + self._scaleOffsets[0]) / self._scaleFactor) * factor) - offsetX,
				(((c[1] + self._scaleOffsets[1]) / self._scaleFactor) * factor) - offsetY
			)
			for c in self._controls
		]
		"""
		if self._canvas_time != 0:
			max_t = self._canvas_time
			t = 0
			while t < max_t:
				self.calc_frame(t)
				t += self._throttle
			self.calc_frame(max_t)
		else:
			pass
		"""
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
			self._canvas_time = 0
			intervals = []
			t = 0
			while t < 1:
				intervals.append((self._controls, t))
				t += self._throttle
			if t != 1:
				intervals.append((self._controls, 1))
			
			self._points = self._pool.map(interpolate, intervals)

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
		self._canvas_time = t
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

