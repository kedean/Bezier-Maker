#pragma once

#include<vector>
#ifdef __APPLE__
	#include<OpenGL/OpenGL.h>
#else
	#include<GL/GL.h>
#endif
#include<cmath>

using namespace std;

#define Vector2f pair<float, float>

typedef struct Color4f{
	int r, g, b, a;
	Color4f(int _r=255, int _g=255, int _b=255, int _a=255)
	: r(_r), g(_g), b(_b), a(_a){
	}
} Color4f;

#define Color3f Color4f

class BezierCurve{
private:
	vector<Vector2f> _controls; //list of control points
	vector<Vector2f> _points; //list of points that define the curve itself
	
	double _throttle; //controls detail level of the curve, setting this very low results in a series of angled lines. Very high gives the illusion of round corners
	
	Color4f _color, _animatedLineColor, _boundingLineColor, _controlColor;
	
	double _canvasTime; //time interval of the most recent call to CalcFrame() that was not interrupted by DrawCurve()
	
	/*variables for controlling the zoom/scale*/
	double _scaleFactor;
	Vector2f _scaleOffsets;
	
	void Generate(); //Regenerates the points of the curve. Internal only, foruse after calls that alter the control point structure
	
public:
	BezierCurve();
	
	/*display methods*/
	
	BezierCurve& DrawCurve(); //draw the current curve to the canvas
	BezierCurve& DrawControls(); //draw the control points to the canvas as 5px radius circles
	BezierCurve& DrawBoundingLines(); //draw the lines connecting the control points to the canvas
	BezierCurve& DrawCalcLines(); //draw the lines used to calculate the current curve time. When used after a call to Generate(), this will produce no useful results.
	
	/*line calculation*/
	
	BezierCurve& CalcFrame(double t=1.1); //same function as generate, except only up to the given time t. If drawing is enabled, it will also illustrate the steps used to animate
	Vector2f CalcLineLayer(double t, bool draw=false); //calculate the point at time interval t by recursively (technically used a for loop instead of recursion) performing intersections of lines in the control set. The final intersection is the result.
	Vector2f Interpolate(double i); //Mathematically calculates the point located at the time interval i using the Bezier formula
	Vector2f Derive(double i); //Mathematically calculates the point located at time interval i on the first derivative of the curve
	
	/*control point manipulation*/
	
	BezierCurve& AddPoint(Vector2f p); //add the point p as a control
	BezierCurve& AddPoint(int x, int y); //add the point (x, y) as a control
	Vector2f RemovePoint(Vector2f p, int range=0); //Removes the closest point within the given range of p
	Vector2f RemovePoint(int x, int y, int range=0); //Removes the closet point within the given range of (x, y)
	Vector2f RemovePoint(int index); //Removes the point at the given index. Negative indices indicate a distance from the top, so -1 is the most recent
	
	/*access methods*/
	
	const vector<Vector2f>& GetControls(); //returns a vector of the control points
	const vector<Vector2f>& GetPoints(); //returns a vector of all pixels currently occupied by the curve
	
	/*attribute manipulation*/
	
	BezierCurve& SetThrottle(double throttle); //alter the 'throttle', in the form 1/n, where n is the number of points on the curve to be drawn
	double GetThrottle();
	
	BezierCurve& SetColor(Color4f color); //alter the color of the curve drawn
	Color4f GetColor();
	
	BezierCurve& SetControlColor(Color4f color);
	Color4f GetControlColor();
	
	BezierCurve& SetBoundingLineColor(Color4f color);
	Color4f GetBoundingLineColor();
	
	BezierCurve& SetSize(int width, int height); //alter the size of the canvas
	BezierCurve& Scale(double factor, Vector2f center=make_pair(0,0)); //scale the points by the given factor and centered on the given center, used for zooming. The factor is relative to the original set of points
	BezierCurve& Scale(double factor, float centerX=0, float centerY=0);
	
	BezierCurve& Clear(); //erase all control points and curve points
};