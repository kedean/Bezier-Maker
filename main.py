from bezier import BezierCurve
from ConfigParser import *
import json

def main(with_curve, with_controls, with_bounds, 
		curve_color, control_color, bounds_color, animation_color):

	curve = BezierCurve(width=800, height=600, caption='Beziers', resizable=True)
	curve.toggle_curve(with_curve)
	curve.toggle_controls(with_controls)
	curve.toggle_bounds(with_bounds)
	curve.set_curve_color(curve_color)
	curve.set_control_color(control_color)
	curve.set_bounds_color(bounds_color)
	curve.set_animation_color(animation_color)
	curve.run()

if __name__ == "__main__":
	config = ConfigParser({"draw_curve":"True", "draw_bounds":"True", "draw_controls":"True",
							"curve_color":"[0,0,0]", "control_color":"[0,0,0]", "bounds_color":"[0,0,0]",
							"animation_color":"[0,255,0]"})
	config.read("config.ini")
	with_curve = config.getboolean('draw_modes', 'draw_curve')
	with_controls = config.getboolean('draw_modes', 'draw_controls')
	with_bounds = config.getboolean('draw_modes', 'draw_bounds')
	curve_color = json.loads(config.get('colors', 'curve_color'))
	control_color = json.loads(config.get('colors', 'control_color'))
	bounds_color = json.loads(config.get('colors', 'bounds_color'))
	animation_color = json.loads(config.get('colors', 'animation_color'))

	main(with_curve, with_controls, with_bounds, curve_color, control_color, bounds_color, animation_color)