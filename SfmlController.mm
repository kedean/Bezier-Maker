#import "SfmlController.h"
#import <vector>
#import <sstream>
#import <cstdio>

#define FPS 60.0f // framerate limit

@implementation SfmlController 

- (void)awakeFromNib 
{ 
	sfmlView = new sf::RenderWindow(contextView); 
	
	[NSTimer scheduledTimerWithTimeInterval:(1.f/FPS)
									 target:self
								   selector:@selector(display:)
								   userInfo:nil
									repeats:YES];
	
	[self onInit];
	[renderProgressIndicator setUsesThreadedAnimation: YES];
} 

- (void)onInit 
{
	double throttle = 1;
	for(int i = 0; i < detailValue+3; i++){
		throttle /= 10;
	}
	mainCurve = BezierCurve(sfmlView->GetWidth(), sfmlView->GetHeight(), false, sf::Color(255, 0, 0), throttle);
	spriteCurve = sf::Sprite(mainCurve);
	mode.Vertices = true;
	mode.Lines = true;
	mode.Gradient = false;
	animationMeter = 1.0f;
}

// Called when the Quit button is clicked
- (IBAction)onQuit:(id)sender
{
	sfmlView->Close();
}
- (IBAction)onClear:(id)sender{
	mainCurve.Clear();
	animationMeter = 1.0;
	[animateButton setTitle:@"Animate"];
	[renderProgressIndicator stopAnimation:self];
}
- (IBAction)onUndo:(id)sender{
//	[renderProgressIndicator startAnimation:self];
	mainCurve.RemovePoint(-1);
	[renderProgressIndicator stopAnimation:self];
}
- (IBAction)onToggleVertices:(id)sender{
//	[renderProgressIndicator startAnimation:self];
	mode.Vertices = !mode.Vertices;
	[renderProgressIndicator stopAnimation:self];
}
- (IBAction)onToggleLines:(id)sender{
//	[renderProgressIndicator startAnimation:self];
	mode.Lines = !mode.Lines;
	[renderProgressIndicator stopAnimation:self];
}
- (IBAction)onToggleGradient:(id)sender{
//	[renderProgressIndicator startAnimation:self];
	mode.Gradient = !mode.Gradient;
//	mainCurve.EnableGradient(mode.Gradient);
	[renderProgressIndicator stopAnimation:self];
}
- (IBAction)onSetDetail:(id)sender{
	if(detailValue < 3){
//		[renderProgressIndicator startAnimation:self];
		double throttle = 1;
		for(int i = 0; i < detailValue+3; i++){
			throttle /= 10;
		}
		mainCurve.SetThrottle(throttle);
		[renderProgressIndicator stopAnimation:self];
	}
}
- (IBAction)onAnimate:(id)sender{
	static double pausedAnimationMeterVal = -1;
	if(animationMeter >= 1.0 && animationMeter < 2.0){
		animationMeter = 0;
		[animateButton setTitle:@"Pause"];
		[renderProgressIndicator startAnimation:self];
	}
	else{
		if(pausedAnimationMeterVal == -1){
			pausedAnimationMeterVal = animationMeter;
			animationMeter = 2.0;
			[animateButton setTitle:@"Animate"];
			[renderProgressIndicator stopAnimation:self];
		} else{
			animationMeter = pausedAnimationMeterVal;
			pausedAnimationMeterVal = -1;
			[animateButton setTitle:@"Pause"];
			[renderProgressIndicator startAnimation:self];
		}
	}
}

- (void)display:(NSTimer *)theTimer
{
	static bool mouseClicked = false;
	
	if(!sfmlView->IsOpened()) {
		[theTimer invalidate];
		[NSApp terminate: nil];
	}
	else if(animationMeter < 1.0){ //Handle the animation process
		
		sf::Event Event;
		sfmlView->GetEvent(Event); //pull any events so as to ignore them.
		
		mainCurve.Animate(sfmlView, animationMeter);
		animationMeter += mainCurve.GetThrottle();
		
		if(animationMeter >= 1.0){
			[renderProgressIndicator stopAnimation:self];
			[animateButton setTitle:@"Animate"];
		}
	}
	else if(animationMeter == 2){ //Handle clicking when animation is paused
		sf::Event Event; 
		while (sfmlView->GetEvent(Event)) {
			if (Event.Type == sf::Event::Closed) {
				sfmlView->Close(); 
			}
			
			else if(Event.Type == sf::Event::MouseButtonPressed){
				animationMeter = 1.0;
				[renderProgressIndicator stopAnimation:self];
				[animateButton setTitle:@"Animate"];
				
				int mouseX = Event.MouseButton.X;
				int mouseY = Event.MouseButton.Y;
				if(Event.MouseButton.Button == sf::Mouse::Left){
					mainCurve.AddPoint(mouseX, mouseY);
					mouseClicked = true;
				}
				else{ //search for a point within a 5px radius
					mainCurve.RemovePoint(mouseX, mouseY, 5);
					[renderProgressIndicator stopAnimation:self];
				}
			}
		}
	}
	else if(animationMeter < 2.0){ //Handles normal drawing mode
		sf::Event Event; 
		while (sfmlView->GetEvent(Event)) {
			if (Event.Type == sf::Event::Closed) {
				sfmlView->Close(); 
			}
			
			if ((Event.Type == sf::Event::KeyPressed) &&
				(Event.Key.Code == sf::Key::Escape)) {
				sfmlView->Close();
			}
			
			if(Event.Type == sf::Event::KeyPressed){
				switch(Event.Key.Code){
				}
			}
			else if(Event.Type == sf::Event::MouseMoved){
				if(mouseClicked == true){
					mainCurve.RemovePoint(-1);
					mainCurve.AddPoint(Event.MouseMove.X, Event.MouseMove.Y);
				}
			}
			else if(Event.Type == sf::Event::MouseButtonPressed){
				int mouseX = Event.MouseButton.X;
				int mouseY = Event.MouseButton.Y;
				if(Event.MouseButton.Button == sf::Mouse::Left){
					mainCurve.AddPoint(mouseX, mouseY);
					mouseClicked = true;
				}
				else{ //search for a point within a 5px radius
					mainCurve.RemovePoint(mouseX, mouseY, 5);
				}
			}
			else if(Event.Type == sf::Event::MouseButtonReleased){
				mouseClicked = false;
			}
		}
		
		// Do the general SFML display process
		sfmlView->SetActive();
		
		sfmlView->Clear(sf::Color(255,255,255));
		sfmlView->Draw(spriteCurve);
		
		std::vector<sf::Vector2f>::iterator controlIt; //this will be used to iterate over the points for drawing lines, then drawing circles to represent the points
		std::vector<sf::Vector2f> controls = mainCurve.GetControls(); //array of the control points
		
		//Draw the circles to represent points
		
		if(controls.size() != 0){
			for(controlIt = controls.begin(); controlIt < controls.end()-1; controlIt++){
				if(mode.Lines)
					sfmlView->Draw(sf::Shape::Line(controlIt->x, controlIt->y, (controlIt+1)->x, (controlIt+1)->y, 1, sf::Color(0, 0, 200)));
				if(mode.Vertices)
					sfmlView->Draw(sf::Shape::Circle(controlIt->x, controlIt->y, 5, sf::Color(0, 0, 255)));
			}
			if(mode.Vertices)
				sfmlView->Draw(sf::Shape::Circle(controls.back().x, controls.back().y, 5, sf::Color(255, 0, 0))); //last point is specially colored
		}
		
		//Display an indicator of the vertex that the mouse is on, if any
		
		if(mode.Vertices){
			int mouseX = sfmlView->GetInput().GetMouseX();
			int mouseY = sfmlView->GetInput().GetMouseY();
			
			vector<sf::Vector2f>::iterator it;
			for(it = controls.begin(); it < controls.end(); it++){
				if(((*it).x - mouseX)*((*it).x - mouseX) + ((*it).y - mouseY)*((*it).y - mouseY) <= 25){ //distance formula. If the distance between this point and the clicked spot is less than 5, its within threshold
					
					break;
				}
			}
		}
		
		
		sfmlView->Display();
	}
} 

@end 

