from bezier_curve import BezierCurve
import random
from ConfigParser import *
import json
from time import time
import multiprocessing

def main():
	config = ConfigParser({"draw_curve":"True", "draw_bounds":"True", "draw_controls":"True",
		"curve_color":"[0,0,0]", "control_color":"[0,0,0]", "bounds_color":"[0,0,0]",
		"animation_color":"[0,255,0]", "throttle":"0.001"})
	config.read("config.ini")

	curve = BezierCurve(width=800, height=600, caption='Beziers', resizable=True)
	curve.toggle_curve(config.getboolean('draw_modes', 'draw_curve'))
	curve.toggle_controls(config.getboolean('draw_modes', 'draw_controls'))
	curve.toggle_bounds(config.getboolean('draw_modes', 'draw_bounds'))
	curve.set_curve_color(json.loads(config.get('colors', 'curve_color')))
	curve.set_control_color(json.loads(config.get('colors', 'control_color')))
	curve.set_bounds_color(json.loads(config.get('colors', 'bounds_color')))
	curve.set_animation_color(json.loads(config.get('colors', 'animation_color')))
	curve.set_throttle(config.getfloat('attributes', 'throttle'))

	"""
	The test that compares interpolate to static_calc_line_layer
	"""

	"""
	controls = []
	k = 200
	for i in range(0, k):
		controls.append((random.randint(0, 100), random.randint(0, 100)))
	pool = multiprocessing.Pool()

	n = 400

	interp_args = []
	calc_args = []
	for i in range(0, n):
		interp_args.append((controls, .5))
		calc_args.append((controls, .5))

	t1 = time()
	vals = pool.map(interpolate, interp_args)
	t2 = time()
	print "{0} interpolates on {2} controls took {1}ms".format(n, (t2 - t1)*1000, k)

	t1 = time()
	vals = pool.map(static_calc_line_layer, calc_args)
	t2 = time()
	print "{0} static_calc_line_layers on {2} controls took {1}ms".format(n, (t2 - t1)*1000, k)
	
	exit()
	"""

	curve.run()

if __name__ == "__main__":
	main()