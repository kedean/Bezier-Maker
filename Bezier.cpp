#include "Bezier.h"
#include<iostream>
sf::Color longToColor(unsigned long int color){
	int r = color % 256;
	int g = (color/256) % 256;
	int b = (color/65536) % 256;
	
	return sf::Color(r,g,b);
}

void BezierCurve::DrawLine(sf::Vector2f origin, sf::Vector2f slope){
	if(slope.x == 0)
		return;
	
	float slopeVal = slope.x / (0-slope.y);
	
	float y = origin.y, x = origin.x;
	
	sf::Color color(0, 0, 255, 100);
	float colorStep = 200.0 / (_width - origin.x);
	
	while(x > 0 && x < _width && y > 0 && y < _height){ //within bounds
		color.b -= colorStep;
		SetPixel(x, y, color);
		x -= 1;
		y += slopeVal;
	}
	
	return;
	color = sf::Color(0, 0, 255, 100);
	colorStep = 200.0 / origin.x;
	
	y = origin.y, x = origin.x; //reset, go the other direction
	
	while(x > 0 && x < _width && y > 0 && y < _height){ //within bounds
		color.b -= colorStep;
		SetPixel(x, y, color);
		x += 1;
		y -= slopeVal;
	}
}

sf::Vector2f BezierCurve::Interpolate(double i){
	
	int n = _controls.size() - 1; //n should actually be one less than the number of coords
	
	double x = 0, y = 0; //output coords
	
	double iN = 1; //at the end this will be i to the nth power
	
	double j = 1 - i; //additive inverse of i
	double jN = 1;
	for(int k = 0; k < n; k++) //jN is j to the nth power, will be 1 by the end
		jN *= j;
	for(int k = 0; k <= n; k++){
		double multiplier = ((k > 0 && k < n) ? n : 1) * iN * jN; //middle values are multiplied by n, then in any case by the current powers of i and j
		iN *= i;
		jN /= j;
		
		x += _controls[k].x * multiplier;
		y += _controls[k].y * multiplier;
	}
	return sf::Vector2f(x, y);
}

sf::Vector2f BezierCurve::Derive(double i){
	
	int n = _controls.size() - 1; //n should actually be one less than the number of coords
	
	vector<sf::Vector2f> q_controls;
	
	for(int k = 0; k < n; k++){
		q_controls.push_back(sf::Vector2f(n*(_controls[k+1].x - _controls[k].x), n*(_controls[k+1].y - _controls[k].y)));
	}
	
	n--;
	
	double x = 0, y = 0; //output coords
	
	double iN = 1; //at the end this will be i to the nth power
	
	double j = 1 - i; //additive inverse of i
	double jN = 1;
	for(int k = 0; k < n; k++) //jN is j to the nth power, will be 1 by the end
		jN *= j;
	for(int k = 0; k <= n; k++){
		double multiplier = ((k > 0 && k < n) ? n : 1) * iN * jN; //middle values are multiplied by n, then in any case by the current powers of i and j
		iN *= i;
		jN /= j;
		
		x += q_controls[k].x * multiplier;
		y += q_controls[k].y * multiplier;
	}
	return sf::Vector2f(x, y);
}

sf::Vector2f BezierCurve::DrawLineLayer(vector<sf::Vector2f> &controlSet, double t){
	int maxControl = controlSet.size()-1; //do not operate on the last control, since it will be just an endpoint to a line
	if(maxControl == 0) //only one control, so there are no control sets
		return controlSet[0];
	else if(maxControl == -1) //no controls
		return sf::Vector2f(0, 0);
	
	sf::Vector2f subControls[maxControl+1]; //array of control subsets. Will get smaller as the loop iterates, but its size is always the first sub group
	for(int i = 0; i <= maxControl; i++){ //copy all controls over as the initial set
		subControls[i] = controlSet[i];
	}
	
	do{
		for(int i = 0; i < maxControl; i++){
			subControls[i].x += (subControls[i+1].x - subControls[i].x)*t;
			subControls[i].y += (subControls[i+1].y - subControls[i].y)*t;
			
			if(_canvas != NULL && i != 0){
				_canvas->Draw(sf::Shape::Line(subControls[i-1], subControls[i], 1, _animatedLineColor));
			}
		}
		maxControl--;
	} while(maxControl >= 1);
	
	return subControls[0];
}

void BezierCurve::Generate(){
	if(_controls.size() == 0) //no control points, no curve
		return;
	Create(_width, _height, sf::Color(0, 0, 0, 0));
	_asSprite = sf::Sprite(*this);
	//sf::Vector2f lastPoint(INT_MAX, INT_MAX); //used to prevent duplicate points from being operated on
	/*int** pixeldist = new int*[_width]; //the min distance of each pixel in the image to any point on the curve. At the start this is infinity, or int_max.
	
	for(int i = 0; i < _width; i++){
		pixeldist[i] = new int[_height];
		for(int j = 0; j < _height; j++){
			pixeldist[i][j] = INT_MAX;
		}
	}*/
	
	for(double t = 0; t < 1; t+=_stepSize){
		/*
		 //Old version which calculated with bezier equations
		 sf::Vector2f point = Interpolate(t);
		
		if(point != lastPoint){
			_points.push_back(point);
			SetPixel(point.x, point.y, _color);
			if(_hasGradient){ //for gradients, the distance of every pixel to this pixel needs to be calculated, and a point drawn.
//				DrawLine(point, Derive(t));
				//old version just drew lines through the normal of the point
				
				//create bounds for screen scanning to avoid obvious failures
				sf::IntRect scanBoxA(0, 0, _width, _height), scanBoxB(0, 0, _width, _height);
				
				if(t != 0){ //bounds for the first coord are always fullscreen
					//x axis scan bounds
					if(point.x < lastPoint.x){
						scanBoxA.Right = lastPoint.x;
					}
					else if(point.x > lastPoint.x){
						scanBoxA.Left = lastPoint.x;
					}
					
					//y axis scan bounds
					if(point.y < lastPoint.y){
						scanBoxB.Bottom = lastPoint.y;
						scanBoxA.Top = lastPoint.y;
					}
					else if(point.y > lastPoint.y){
						scanBoxB.Top = lastPoint.y;
						scanBoxA.Bottom = lastPoint.y;
					}
				}
				
				//scan the possible screen space for min dist
				
				//first scan block
				for(int i = scanBoxA.Left; i < scanBoxA.Right; i++){
					for(int j = scanBoxA.Top; j < scanBoxA.Bottom; j++){
						int distance_2 = (i - point.x)*(i - point.x) + (j - point.y)*(j - point.y);
						if(distance_2 < pixeldist[i][j])
							pixeldist[i][j] = distance_2;
					}
				}
				
				//second scan block
				for(int i = scanBoxB.Left; i < scanBoxB.Right; i++){
					for(int j = scanBoxB.Top; j < scanBoxB.Bottom; j++){
						int distance_2 = (i - point.x)*(i - point.x) + (j - point.y)*(j - point.y);
						if(distance_2 < pixeldist[i][j])
							pixeldist[i][j] = distance_2;
					}
				}
			}
			
		   lastPoint = point;
		}*/
		
		//new version calculates by recursive line drawing, more accurate
		
		sf::Vector2f p = this->DrawLineLayer(_controls, t);
		
		if(_points.size() == 0 || p != _points.back()){
			if(p.x < _width && p.x > 0 && p.y < _height && p.y > 0) //only draw pixels inside the image space
				SetPixel(p.x, p.y, _color);
			_points.push_back(p);
		}
	}
	/*
	if(_hasGradient){
		for(int i = 0; i < _width; i++){
			for(int j = 0; j < _height; j++){
				if(pixeldist[i][j] != 0){
					SetPixel(i, j, longToColor((pixeldist[i][j])));
				}
			}
		}
	}*/
}

BezierCurve::BezierCurve(){
	_stepSize = 0.00001;
	_width = 800;
	_height = 600;
	_color = sf::Color(0,0,0);
	_animatedLineColor = sf::Color(0, 255, 0);
	_hasGradient = false;
	_scaleOffsets = sf::Vector2f(0,0);
	_scaleFactor = 1;
	_canvas = NULL;
	_canvasTime = 0;
	Create(_width, _height, sf::Color(0, 0, 0, 0));
	_asSprite = sf::Sprite(*this);
}
BezierCurve::BezierCurve(int width, int height, bool gradient, sf::Color color, double throttle){
	_stepSize = throttle;
	_width = width;
	_height = height;
	_color = color;
	_animatedLineColor = sf::Color(0, 255, 0);
	_scaleOffsets = sf::Vector2f(0,0);
	_scaleFactor = 1;
	_canvas = NULL;
	_canvasTime = 0;
	_hasGradient = gradient;
	Create(width, height, sf::Color(0, 0, 0, 0));
	_asSprite = sf::Sprite(*this);
}
void BezierCurve::AddPoint(sf::Vector2f p){
	_controls.push_back(p);
	Generate();
}
void BezierCurve::AddPoint(int x, int y){
	_controls.push_back(sf::Vector2f(x, y));
	Generate();
}
sf::Vector2f BezierCurve::RemovePoint(sf::Vector2f p, int range){
	vector<sf::Vector2f>::iterator it;
	for(it = _controls.begin(); it < _controls.end(); it++){
		if(((*it).x - p.x)*((*it).x - p.x) + ((*it).y - p.y)*((*it).y - p.y) <= range*range){ //distance formula. If the distance between this point and the clicked spot is less than 5, its within threshold
			_controls.erase(it);
			Generate();
			return *it;
		}
	}
	
	return sf::Vector2f(-1, -1);
}
sf::Vector2f BezierCurve::RemovePoint(int x, int y, int range){
	return RemovePoint(sf::Vector2f(x, y), range);
}
sf::Vector2f BezierCurve::RemovePoint(int index){
	if(index >= (signed int) _controls.size()){
		return sf::Vector2f(-1, -1);
	}
	else if(index < 0){ //negative index is treated as that many from the top, so -1 is the last element
		index = _controls.size() + index;
	}
	
	sf::Vector2f p = *(_controls.begin() + index);
	
	_controls.erase(_controls.begin() + index);
	Generate();
	return p;
}
const vector<sf::Vector2f>& BezierCurve::GetControls(){
	return _controls;
}
const vector<sf::Vector2f>& BezierCurve::GetPoints(){
	return _points;
}
void BezierCurve::SetThrottle(double throttle){
	_stepSize = throttle;
	Generate();
}
double BezierCurve::GetThrottle(){
	return _stepSize;
}
void BezierCurve::SetColor(sf::Color color){
	_color = color;
	Generate();
}
sf::Color BezierCurve::GetColor(){
	return _color;
}
void BezierCurve::SetSize(int width, int height){
	_width = width;
	_height = height;
	Generate();
}
void BezierCurve::Scale(double factor, sf::Vector2f center){
	vector<sf::Vector2f>::iterator it;
	double offsetX = center.x*(factor-1);
	double offsetY = center.y*(factor-1);
	
	for(it = _controls.begin(); it < _controls.end(); it++){
		it->x = (((it->x + _scaleOffsets.x)/_scaleFactor) * factor) - offsetX;
		it->y = (((it->y + _scaleOffsets.y)/_scaleFactor) * factor) - offsetY;
	}
	
	if(_canvas != NULL){ //don't regenerate in the middle of animation, just scale the already calculated pixels
		sf::RenderWindow* tempCanvas = _canvas;
		for(double t = 0; t < _canvasTime; t+=_stepSize)
			Animate(NULL, t);
		Animate(tempCanvas, _canvasTime);
	} else{
		Generate();
	}
	
	_scaleFactor = factor;
	_scaleOffsets.x = offsetX;
	_scaleOffsets.y = offsetY;
}
void BezierCurve::Animate(sf::RenderWindow* canvas, double t){
	_canvas = canvas;
	if(t == 0){ //on the first time iteration the pixels must be cleared
		Create(_width, _height, sf::Color(0, 0, 0, 0));
		_asSprite = sf::Sprite(*this);
	}
	int lControls = _controls.size()-1; //number of non-end control points
	
	if(_canvas != NULL){
		_canvas->Clear(sf::Color(255, 255, 255));
		_canvas->Draw(_asSprite);
		
		for(int i = 0; i < lControls; i++){
			_canvas->Draw(sf::Shape::Line(_controls[i], _controls[i+1], 1, sf::Color(0, 0, 255)));
		}
	}
	
	sf::Vector2f p = this->DrawLineLayer(_controls, t);
	
	if(_points.size() == 0 || p != _points.back()){
		if(p.x < _width && p.x > 0 && p.y < _height && p.y > 0) //only draw pixels inside the image space
			SetPixel(p.x, p.y, _color);
		_points.push_back(p);
	}
	
	if(_canvas != NULL){
		_canvas->Draw(sf::Shape::Circle(p, 5, sf::Color(255, 0, 0)));
		_canvas->Display();
		_canvasTime = t;
	}
	
	if(t == 1)
		_canvas = NULL;
}
void BezierCurve::Clear(){
	_scaleOffsets = sf::Vector2f(0,0);
	_scaleFactor = 1;
	_controls.clear();
	Create(_width, _height, sf::Color(0,0,0,0));
	_asSprite = sf::Sprite(*this);
}