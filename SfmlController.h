
////////////////////////////////////////////////////////////
// Headers
////////////////////////////////////////////////////////////
#import <Cocoa/Cocoa.h> 
#import <SFML/Graphics.hpp> 
#import "Bezier.h"

@interface SfmlController : NSWindowController 
{ 
	IBOutlet NSView* contextView;
	IBOutlet NSProgressIndicator *renderProgressIndicator;
	IBOutlet NSButton *animateButton;
	sf::RenderWindow *sfmlView; 
	sf::Sprite spriteCurve;
	int detailValue;
	bool gradientOn;
	struct DrawMode{
		bool Lines, Vertices, Gradient;
	} mode;
	
	BezierCurve mainCurve;
	double animationMeter;
	double pausedAnimationMeterVal;
	double currentScale;
}

- (void)display:(NSTimer*)theTimer; 
- (void)onInit;
- (IBAction)onQuit:(id)sender;
- (IBAction)onClear:(id)sender;
- (IBAction)onUndo:(id)sender;
- (IBAction)onToggleVertices:(id)sender;
- (IBAction)onToggleLines:(id)sender;
- (IBAction)onToggleGradient:(id)sender;
- (IBAction)onSetDetail:(id)sender;
- (IBAction)onAnimate:(id)sender;
- (IBAction)onZoomIn:(id)sender;
- (IBAction)onZoomOut:(id)sender;

@end 
