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
	mainCurve = BezierCurve().SetColor(Color3f(255, 0, 0)).SetThrottle(throttle);
	mode.Vertices = true;
	mode.Lines = true;
	animationMeter = 1.0f;
	pausedAnimationMeterVal = -1;
	currentScale = 1.0f;
}

// Called when the Quit button is clicked
- (IBAction)onQuit:(id)sender
{
	sfmlView->Close();
}
- (IBAction)onClear:(id)sender{
	mainCurve.Clear();
	animationMeter = 1.0f;
	currentScale = 1.0f;
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
- (IBAction)onZoomIn:(id)sender{
	if(currentScale > 1)
		++currentScale;
	else
		currentScale *= 2;
	mainCurve.Scale(currentScale, sfmlView->GetWidth()/2, sfmlView->GetHeight()/2);
}
- (IBAction)onZoomOut:(id)sender{
	if(currentScale > 1)
		--currentScale;
	else
		currentScale /= 2;

	mainCurve.Scale(currentScale, sfmlView->GetWidth()/2, sfmlView->GetHeight()/2);
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
		sfmlView->Clear(sf::Color(255, 255, 255));
		mainCurve.CalcFrame(animationMeter).DrawCalcLines();
		if(mode.Vertices)
			mainCurve.DrawControls();
		if(mode.Lines)
			mainCurve.DrawBoundingLines();
		
		sfmlView->Display();
		animationMeter += mainCurve.GetThrottle();
		
		if(animationMeter >= 1.0){
			[renderProgressIndicator stopAnimation:self];
			[animateButton setTitle:@"Animate"];
		}
	}
	else if(animationMeter == 2){ //Handle clicking when animation is paused
		sfmlView->Clear(sf::Color(255, 255, 255));
		mainCurve.CalcFrame(pausedAnimationMeterVal).DrawCalcLines();
		if(mode.Vertices)
			mainCurve.DrawControls();
		if(mode.Lines)
			mainCurve.DrawBoundingLines();
		sfmlView->Display();
		
		//event processing is done after displaying the current point to avoid a misrepresented curve
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
					Vector2f removed = mainCurve.RemovePoint(-1);
					if(removed.first == -1 && removed.second == -1){ //no point was found, shift the screen instead
						
					}
					else{
						mainCurve.AddPoint(Event.MouseMove.X, Event.MouseMove.Y);
					}
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
		
		sfmlView->Clear(sf::Color(255,255,255));
		mainCurve.DrawCurve();
		if(mode.Vertices)
			mainCurve.DrawControls();
		if(mode.Lines)
			mainCurve.DrawBoundingLines();
		sfmlView->Draw(sf::Shape::Line(0, 0, 1, 1, 1, sf::Color(0, 0, 0)));
		sfmlView->Display();
	}
} 

@end 

