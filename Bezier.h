#pragma once
#include <SFML/Graphics.hpp>
#include <vector>
using namespace std;

class BezierCurve : public sf::Image{
private:
	vector<sf::Vector2f> _controls;
	vector<sf::Vector2f> _points;
	int _width, _height;
	double _stepSize;
	sf::Color _color, _animatedLineColor;
	sf::Sprite _asSprite;
	bool _hasGradient;
	sf::RenderWindow* _canvas;
	double _canvasTime;
	
	double _scaleFactor;
	sf::Vector2f _scaleOffsets;
	
	void DrawLine(sf::Vector2f origin, sf::Vector2f slope); //draws a straight line across the image, with the given slope, that goes through 'origin'
	sf::Vector2f DrawLineLayer(vector<sf::Vector2f> &controlSet, double t);
	
	sf::Vector2f Interpolate(double i); //Calculates the point located at the time interval i
	sf::Vector2f Derive(double i); //Calculates the point located at time interval i on the first derivative of the curve
	void Generate(); //Regenerates the curve and gradient
	
public:
	BezierCurve();
	BezierCurve(int width, int height, bool gradient, sf::Color color=sf::Color(255,0,0), double throttle=0.00001); //constructor
	
	void AddPoint(sf::Vector2f p); //add the point p as a control
	void AddPoint(int x, int y); //add the point (x, y) as a control
	
	sf::Vector2f RemovePoint(sf::Vector2f p, int range=0); //Removes the closest point within the given range of p
	sf::Vector2f RemovePoint(int x, int y, int range=0); //Removes the closet point within the given range of (x, y)
	sf::Vector2f RemovePoint(int index); //Removes the point at the given index. Negative indices indicate a distance from the top, so -1 is the most recent
	
	const vector<sf::Vector2f>& GetControls(); //returns a vector of the control points
	const vector<sf::Vector2f>& GetPoints(); //returns a vector of all pixels currently occupied by the curve
	
	void SetThrottle(double throttle); //alter the 'throttle', in the form 1/n, where n is the number of points on the curve to be drawn
	double GetThrottle();
	void SetColor(sf::Color color); //alter the color of the curve drawn
	sf::Color GetColor();
	void SetSize(int width, int height); //alter the size of the canvas
	void Scale(double factor, sf::Vector2f center=sf::Vector2f(0,0)); //scale the image by the given factor and centered on the given center, good for zooming
	
	void Animate(sf::RenderWindow* canvas, double t=1.1);
	
//	void EnableGradient(bool status); //enable or disable gradient drawing
	
	void Clear(); //erase all control points and curve points
};