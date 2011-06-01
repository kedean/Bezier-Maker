#pragma once
#include <SFML/Graphics.hpp>
#include <vector>
using namespace std;

class BezierCurve{
private:
	vector<sf::Vector2f> _controls; //list of control points
	vector<sf::Vector2f> _points; //list of points that define the curve itself
	
	double _throttle; //controls detail level of the curve, setting this very low results in a series of angled lines. Very high gives the illusion of round corners
	
	sf::Color _color, _animatedLineColor, _boundingLineColor, _controlColor;
	
	sf::RenderWindow* _canvas; //the canvas object to draw to. Setting this to NULL disables drawing
	double _canvasTime; //time interval of the most recent call to DrawFrame() that was not interrupted by DrawCurve()
	
	/*variables for controlling the zoom/scale*/
	double _scaleFactor;
	sf::Vector2f _scaleOffsets;
	
	void Generate(); //Regenerates the points of the curve
	
public:
	BezierCurve(sf::RenderWindow* canvas=NULL); //a null canvas means no drawing will occur. Good for pure calculation.
	
	/*display methods*/
	
	BezierCurve& DrawCurve(); //draw the current curve to the canvas
	BezierCurve& DrawControls(); //draw the control points to the canvas as 5px radius circles
	BezierCurve& DrawBoundingLines(); //draw the lines connecting the control points to the canvas
	BezierCurve& DrawFrame(double t=1.1); //same as drawcurve, except only draws up to the given time interval, and includes an illustration of how the last point was reached
	
	/*line calculation*/
	
	sf::Vector2f DrawLineLayer(vector<sf::Vector2f> &controlSet, double t); //calculate the point at time interval t by recursively (technically used a for loop instead of recursion) performing intersections of lines in the control set. The final intersection is the result.
	sf::Vector2f Interpolate(double i); //Mathematically calculates the point located at the time interval i
	sf::Vector2f Derive(double i); //Mathematically calculates the point located at time interval i on the first derivative of the curve
	
	/*control point manipulation*/
	
	BezierCurve& AddPoint(sf::Vector2f p); //add the point p as a control
	BezierCurve& AddPoint(int x, int y); //add the point (x, y) as a control
	sf::Vector2f RemovePoint(sf::Vector2f p, int range=0); //Removes the closest point within the given range of p
	sf::Vector2f RemovePoint(int x, int y, int range=0); //Removes the closet point within the given range of (x, y)
	sf::Vector2f RemovePoint(int index); //Removes the point at the given index. Negative indices indicate a distance from the top, so -1 is the most recent
	
	const vector<sf::Vector2f>& GetControls(); //returns a vector of the control points
	const vector<sf::Vector2f>& GetPoints(); //returns a vector of all pixels currently occupied by the curve
	
	
	/*attribute manipulation*/
	
	BezierCurve& SetThrottle(double throttle); //alter the 'throttle', in the form 1/n, where n is the number of points on the curve to be drawn
	double GetThrottle();
	
	BezierCurve& SetColor(sf::Color color); //alter the color of the curve drawn
	sf::Color GetColor();
	
	BezierCurve& SetControlColor(sf::Color color);
	sf::Color GetControlColor();
	
	BezierCurve& SetBoundingLineColor(sf::Color color);
	sf::Color GetBoundingLineColor();
	
	BezierCurve& SetSize(int width, int height); //alter the size of the canvas
	BezierCurve& Scale(double factor, sf::Vector2f center=sf::Vector2f(0,0)); //scale the points by the given factor and centered on the given center, used for zooming. The factor is relative to the original set of points
	
	BezierCurve& Clear(); //erase all control points and curve points
};