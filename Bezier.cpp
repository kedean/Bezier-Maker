#include "Bezier.h"

inline int Factorial(int k){
	int result = 1;
	int i;
	for (i = 1; i <= k; i++){
		result *= i;
	}
	
	return result;
}
double BinomialCoefficient(int n, int i){
	return Factorial(n) / (double)(Factorial(i) * Factorial(n - i));
}

Vector2f BezierCurve::Interpolate(double i){
	
	int n = _controls.size() - 1; //n should actually be one less than the number of coords
	
	double x = 0, y = 0; //output coords
	
	double iN = 1; //at the end this will be i to the nth power
	
	double j = 1 - i; //additive inverse of i
	double jN = 1;
	for(int k = 0; k < n; k++) //jN is j to the nth power, will be 1 by the end
		jN *= j;
	
	for(int k = 0; k <= n; k++){
		double multiplier = BinomialCoefficient(n, k) * iN * jN; //middle values are multiplied by n, then in any case by the current powers of i and j
		iN *= i;
		jN /= j;
		
		x += _controls[k].first * multiplier;
		y += _controls[k].second * multiplier;
	}
	return make_pair(x, y);
}

Vector2f BezierCurve::Derive(double i){
	
	int n = _controls.size() - 1; //n should actually be one less than the number of coords
	
	vector<Vector2f> q_controls;
	
	for(int k = 0; k < n; k++){
		q_controls.push_back(make_pair(n*(_controls[k+1].first - _controls[k].first), n*(_controls[k+1].second - _controls[k].second)));
	}
	
	n--;
	
	double x = 0, y = 0; //output coords
	
	double iN = 1; //at the end this will be i to the nth power
	
	double j = 1 - i; //additive inverse of i
	double jN = 1;
	for(int k = 0; k < n; k++) //jN is j to the nth power, will be 1 by the end
		jN *= j;
	for(int k = 0; k <= n; k++){
		double multiplier = BinomialCoefficient(n, k) * iN * jN; //middle values are multiplied by n, then in any case by the current powers of i and j
		iN *= i;
		jN /= j;
		
		x += q_controls[k].first * multiplier;
		y += q_controls[k].second * multiplier;
	}
	return make_pair(x, y);
}

Vector2f BezierCurve::CalcLineLayer(double t, bool draw){
	//alternate implementation of Interpolate()
	
	int maxControl = _controls.size()-1; //do not operate on the last control, since it will be just an endpoint to a line
	if(maxControl == 0) //only one control, so there are no control sets
		return _controls[0];
	else if(maxControl == -1) //no controls
		return make_pair(0, 0);
	
	Vector2f subControls[maxControl+1]; //array of control subsets. Will get smaller as the loop iterates, but its size is always the first sub group
	for(int i = 0; i <= maxControl; i++){ //copy all controls over as the initial set
		subControls[i] = _controls[i];
	}
	
	for(; maxControl > 0; maxControl--){
		for(int i = 0; i < maxControl; i++){
			subControls[i].first += (subControls[i+1].first - subControls[i].first)*t;
			subControls[i].second += (subControls[i+1].second - subControls[i].second)*t;
			
			if(draw && i != 0){ //if the draw parameter was enabled, draw the line segments which are used to calculate the resultant point
				glBegin(GL_LINES);
				glColor4f(_animatedLineColor.r, _animatedLineColor.g, _animatedLineColor.b, _animatedLineColor.a);
				glVertex2f(subControls[i-1].first, subControls[i-1].second);
				glVertex2f(subControls[i].first, subControls[i].second);
				glEnd();
			}
		}
	}
	
	return subControls[0];
}

void BezierCurve::Generate(){
	if(_controls.size() != 0){ //no control points, no curve
		_points.clear();
		
		for(double t = 0; t < 1; t+=_throttle){
			
			Vector2f p = this->CalcLineLayer(t);
			
			if(_points.size() == 0 || p != _points.back()){ //only draw pixels inside the image space
				_points.push_back(p);
			}
		}
		_canvasTime = 0;
		
		/*if(_canvas){
			_gradient.Create(_canvas->GetWidth(), _canvas->GetHeight());
			for(int i = 0; i < _points.size()-1; i++){
				for(int j = 0; j < _canvas->GetWidth(); j++){
					int val = _points[i].first - j;
					if(val < 0)
						val = 0 - val;
					if(val != 0){
						int s, e;
						if(_points[i].second > _points[i+1].second){
							s = _points[i+1].second;
							e = _points[i].second;
						} else{
							s = _points[i].second;
							e = _points[i+1].second;
						}
						for(int k = s; k < e; k++){
							_gradient.SetPixel(j, k, Color4f(0, 255, 0, 256.0/(val/10)) + Color4f(255, 0, 0, 256.0/(val/100)));
						}
					}
				}
			}
		}*/
	}
}

BezierCurve::BezierCurve()
: _color(0,0,0), _controlColor(255, 0, 0), _boundingLineColor(0, 0, 255), _animatedLineColor(0, 255, 0), _throttle(0.00001), _scaleOffsets(0,0), _scaleFactor(1), _canvasTime(0){
}

BezierCurve& BezierCurve::AddPoint(Vector2f p){
	_controls.push_back(p);
	Generate();
	return *this;
}
BezierCurve& BezierCurve::AddPoint(int x, int y){
	_controls.push_back(make_pair(x, y));
	Generate();
	return *this;
}
Vector2f BezierCurve::RemovePoint(Vector2f p, int range){
	return RemovePoint(p.first, p.second, range);
}
Vector2f BezierCurve::RemovePoint(int x, int y, int range){
	vector<Vector2f>::iterator it;
	int range_2 = range*range; //range^2, since the search uses pythagorean theorem
	
	for(it = _controls.begin(); it < _controls.end(); it++){
		if(((*it).first - x)*((*it).first - x) + ((*it).second - y)*((*it).second - y) <= range_2){ //distance formula. If the distance between this point and the clicked spot is less than 5, its within threshold
			_controls.erase(it);
			Generate();
			return *it;
		}
	}
	
	return make_pair(-1, -1);
}
Vector2f BezierCurve::RemovePoint(int index){
	if(index >= (signed int) _controls.size()){ //if the index is too high, error by returning -1
		return make_pair(-1, -1);
	}
	else if(index < 0){ //negative index is treated as that many from the top, so -1 is the last element
		index = _controls.size() + index;
	}
	
	Vector2f p = *(_controls.begin() + index); //store the point for returning
	
	//remove the point from the system
	_controls.erase(_controls.begin() + index);
	Generate();
	
	return p;
}

const vector<Vector2f>& BezierCurve::GetControls(){
	return _controls;
}
const vector<Vector2f>& BezierCurve::GetPoints(){
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

BezierCurve& BezierCurve::SetColor(Color4f color){
	_color = color;
	Generate();
	return *this;
}
Color4f BezierCurve::GetColor(){
	return _color;
}

BezierCurve& BezierCurve::SetControlColor(Color4f color){
	_controlColor = color;
	Generate();
	return *this;
}
Color4f BezierCurve::GetControlColor(){
	return _controlColor;
}

BezierCurve& BezierCurve::SetBoundingLineColor(Color4f color){
	_boundingLineColor = color;
	Generate();
	return *this;
}
Color4f BezierCurve::GetBoundingLineColor(){
	return _boundingLineColor;
}

BezierCurve& BezierCurve::Scale(double factor, Vector2f center){
	return this->Scale(center.first, center.second);
}

BezierCurve& BezierCurve::Scale(double factor, float centerX, float centerY){
	double offsetX = centerX*(factor-1);
	double offsetY = centerY*(factor-1);
	
	vector<Vector2f>::iterator it;
	
	for(it = _controls.begin(); it < _controls.end(); it++){
		it->first = (((it->first + _scaleOffsets.first)/_scaleFactor) * factor) - offsetX; //undo the last scale so that the point is completely unscaled, then scale it to the new factor
		it->second = (((it->second + _scaleOffsets.second)/_scaleFactor) * factor) - offsetY;
	}
	
	if(_canvasTime != 0){ //if an animation was in progress, start over and reanimate silently up to the point where the animation was paused
		double max_t = _canvasTime;
		for(double t = 0; t < max_t; t+=_throttle){
			CalcFrame(t);
		}
		CalcFrame(max_t);
	} else{
		Generate();
	}
	
	_scaleFactor = factor;
	_scaleOffsets.first = offsetX;
	_scaleOffsets.second = offsetY;
	return *this;
}


/*draw functions*/

BezierCurve& BezierCurve::DrawCurve(){
	glBegin(GL_LINE_STRIP);
	glColor4f(_color.r, _color.g, _color.b, _color.a);
	for(int i = 0; i < _points.size(); i++){
		glVertex2f(_points[i].first, _points[i].second);
	}
	glEnd();
	
	return *this;
}
BezierCurve& BezierCurve::DrawControls(){
	std::vector<Vector2f>::iterator it;
	glColor4f(_controlColor.r, _controlColor.g, _controlColor.b, _controlColor.a);
	for(it = _controls.begin(); it < _controls.end(); it++){
		glBegin(GL_POLYGON);
		for(int ang = 0; ang < 360; ang++){
			glVertex2f(5*cos(ang*3.14159265/180) + it->first, 5*sin(ang*3.14159265/180) + it->second);
		}
		glEnd();
	}
	
	return *this;
}
BezierCurve& BezierCurve::DrawBoundingLines(){
	std::vector<Vector2f>::iterator it;
	glLoadIdentity();
	glBegin(GL_LINE_STRIP);
	glColor4f(_boundingLineColor.r, _boundingLineColor.g, _boundingLineColor.b, _boundingLineColor.a);
	for(it = _controls.begin(); it < _controls.end(); it++){
		glVertex2f(it->first, it->second);
	}
	glEnd();
	
	return *this;
}
BezierCurve& BezierCurve::DrawCalcLines(){
	Vector2f p = this->CalcLineLayer(_canvasTime, true);
	
	glBegin(GL_POLYGON);
	glColor4f(_controlColor.r, _controlColor.g, _controlColor.b, _controlColor.a);
	for(int ang = 0; ang < 360; ang++){
		glVertex2f(5*cos(ang*3.14159265/180) + p.first, 5*sin(ang*3.14159265/180) + p.second);
	}
	glEnd();
	
	return *this;
}

BezierCurve& BezierCurve::CalcFrame(double t){
	if(_controls.size() != 0){ //do not do any animating with no control points
		
		if(t == 0){ //on the first time iteration the pixels must be cleared
			_points.clear();
		}
		
		Vector2f p = this->CalcLineLayer(t);
		
		if(_points.size() == 0 || p != _points.back()){ //only draw pixels inside the image space
			_points.push_back(p);
		}
		
	}
	_canvasTime = t; //store the time for later use as the most recently animated frame
	return *this;
}
BezierCurve& BezierCurve::Clear(){
	_scaleOffsets = make_pair(0,0);
	_scaleFactor = 1;
	_controls.clear();
	_points.clear();
	return *this;
}