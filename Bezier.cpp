#include "Bezier.h"

sf::Vector2f BezierCurve::Interpolate(double i){
	
	//incorrect implementation
	
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
	
	for(; maxControl > 0; maxControl--){
		for(int i = 0; i < maxControl; i++){
			subControls[i].x += (subControls[i+1].x - subControls[i].x)*t;
			subControls[i].y += (subControls[i+1].y - subControls[i].y)*t;
			
			if(_canvas != NULL && i != 0){
				_canvas->Draw(sf::Shape::Line(subControls[i-1], subControls[i], 1, _animatedLineColor));
			}
		}
	}
	
	return subControls[0];
}

void BezierCurve::Generate(){
	if(_controls.size() != 0){ //no control points, no curve
		_points.clear();
		
		sf::RenderWindow* tempCanvas = _canvas;
		_canvas = NULL;
		
		for(double t = 0; t < 1; t+=_throttle){
			
			sf::Vector2f p = this->DrawLineLayer(_controls, t);
			
			if(_points.size() == 0 || p != _points.back()){ //only draw pixels inside the image space
				_points.push_back(p);
			}
		}
		
		_canvas = tempCanvas;
	}
}

BezierCurve::BezierCurve()
: _throttle(0.00001), _color(0,0,0), _controlColor(255, 0, 0), _boundingLineColor(0, 0, 255), _animatedLineColor(0, 255, 0), _scaleOffsets(0,0), _scaleFactor(1), _canvas(NULL), _canvasTime(0){
}
BezierCurve::BezierCurve(sf::RenderWindow* canvas, double throttle)
: _color(0,0,0), _controlColor(255, 0, 0), _boundingLineColor(0, 0, 255), _animatedLineColor(0, 255, 0), _scaleOffsets(0,0), _scaleFactor(1), _canvasTime(0){
	_throttle = throttle;
	_canvas = canvas;
}
BezierCurve& BezierCurve::AddPoint(sf::Vector2f p){
	_controls.push_back(p);
	Generate();
	return *this;
}
BezierCurve& BezierCurve::AddPoint(int x, int y){
	_controls.push_back(sf::Vector2f(x, y));
	Generate();
	return *this;
}
sf::Vector2f BezierCurve::RemovePoint(sf::Vector2f p, int range){
	return RemovePoint(p.x, p.y, range);
}
sf::Vector2f BezierCurve::RemovePoint(int x, int y, int range){
	vector<sf::Vector2f>::iterator it;
	int range_2 = range*range; //range^2, since the search uses pythagorean theorem
	
	for(it = _controls.begin(); it < _controls.end(); it++){
		if(((*it).x - x)*((*it).x - x) + ((*it).y - y)*((*it).y - y) <= range_2){ //distance formula. If the distance between this point and the clicked spot is less than 5, its within threshold
			_controls.erase(it);
			Generate();
			return *it;
		}
	}
	
	return sf::Vector2f(-1, -1);
}
sf::Vector2f BezierCurve::RemovePoint(int index){
	if(index >= (signed int) _controls.size()){ //if the index is too high, error by returning -1
		return sf::Vector2f(-1, -1);
	}
	else if(index < 0){ //negative index is treated as that many from the top, so -1 is the last element
		index = _controls.size() + index;
	}
	
	sf::Vector2f p = *(_controls.begin() + index); //store the point for returning
	
	//remove the point from the system
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

BezierCurve& BezierCurve::SetThrottle(double throttle){
	_throttle = throttle;
	Generate();
	return *this;
}
double BezierCurve::GetThrottle(){
	return _throttle;
}

BezierCurve& BezierCurve::SetColor(sf::Color color){
	_color = color;
	Generate();
	return *this;
}
sf::Color BezierCurve::GetColor(){
	return _color;
}

BezierCurve& BezierCurve::SetControlColor(sf::Color color){
	_controlColor = color;
	Generate();
	return *this;
}
sf::Color BezierCurve::GetControlColor(){
	return _controlColor;
}

BezierCurve& BezierCurve::SetBoundingLineColor(sf::Color color){
	_boundingLineColor = color;
	Generate();
	return *this;
}
sf::Color BezierCurve::GetBoundingLineColor(){
	return _boundingLineColor;
}

BezierCurve& BezierCurve::Scale(double factor, sf::Vector2f center){
	double offsetX = center.x*(factor-1);
	double offsetY = center.y*(factor-1);
	
	vector<sf::Vector2f>::iterator it;
	
	for(it = _controls.begin(); it < _controls.end(); it++){
		it->x = (((it->x + _scaleOffsets.x)/_scaleFactor) * factor) - offsetX; //undo the last scale so that the point is completely unscaled, then scale it to the new factor
		it->y = (((it->y + _scaleOffsets.y)/_scaleFactor) * factor) - offsetY;
	}
	
	if(_canvas != NULL && _canvasTime != 0){ //if an animation was in progress, start over and reanimate silently up to the point where the animation was paused
		sf::RenderWindow* tempCanvas = _canvas;
		_canvas = NULL;
		int max_t = _canvasTime;
		for(double t = 0; t < max_t; t+=_throttle)
			DrawFrame(t);
		_canvas = tempCanvas;
		DrawFrame(max_t);
	} else{
		Generate();
	}
	
	_scaleFactor = factor;
	_scaleOffsets.x = offsetX;
	_scaleOffsets.y = offsetY;
	return *this;
}


/*draw functions*/

BezierCurve& BezierCurve::DrawCurve(){
	if(_points.size() > 1 && _canvas != NULL){
		for(int i = 0; i < _points.size()-1; i++)
			_canvas->Draw(sf::Shape::Line(_points[i], _points[i+1], 1, _color));
	}
	_canvasTime = 0;
	return *this;
}
BezierCurve& BezierCurve::DrawControls(){
	if(_canvas != NULL){
		std::vector<sf::Vector2f>::iterator it;
		for(it = _controls.begin(); it < _controls.end(); it++){
			_canvas->Draw(sf::Shape::Circle(it->x, it->y, 5, _controlColor));
		}
	}
	return *this;
}
BezierCurve& BezierCurve::DrawBoundingLines(){
	if(_canvas != NULL){
		std::vector<sf::Vector2f>::iterator it;
		for(it = _controls.begin()+1; it < _controls.end(); it++){
			_canvas->Draw(sf::Shape::Line(*it, *(it-1), 1, _boundingLineColor));
		}
	}
	return *this;
}

BezierCurve& BezierCurve::DrawFrame(double t){
	if(_controls.size() != 0){ //do not do any animating with no control points
		
		if(t == 0){ //on the first time iteration the pixels must be cleared
			_points.clear();
		}
		if(_canvas != NULL){
			_canvas->Clear(sf::Color(255, 255, 255));
			
			DrawCurve();
			
			for(int i = 0; i < _controls.size()-1; i++){
				_canvas->Draw(sf::Shape::Line(_controls[i], _controls[i+1], 1, _boundingLineColor));
			}
		}
		
		sf::Vector2f p = this->DrawLineLayer(_controls, t);
		
		if(_points.size() == 0 || p != _points.back()){ //only draw pixels inside the image space
			_points.push_back(p);
		}
		
		if(_canvas != NULL){
			_canvas->Draw(sf::Shape::Circle(p, 5, _controlColor));
			_canvas->Display();
		}
	}
	_canvasTime = t; //store the time for later use as the most recently animated frame
	return *this;
}
BezierCurve& BezierCurve::Clear(){
	_scaleOffsets = sf::Vector2f(0,0);
	_scaleFactor = 1;
	_controls.clear();
	_points.clear();
	return *this;
}