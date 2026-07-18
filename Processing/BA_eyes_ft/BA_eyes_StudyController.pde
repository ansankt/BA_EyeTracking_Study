EyeRenderer eyeRenderer;
EyeAgent eyeAgent;
GazeInput gazeInput;
GazeMapper gazeMapper;
GazeClassifier gazeClassifier;
GazeSample currentGazeSample;
GazeRegion currentGazeRegion = GazeRegion.INVALID;
GazeState currentGazeState = GazeState.INVALID;
boolean gazeBreakDetected = false;

EyeController activeEyeController;
IdleMovementController idleMovementController;
GazeAwareController gazeAwareController;

void setup() {
  //size(800, 800);
  fullScreen();
  eyeRenderer = new EyeRenderer();
  eyeAgent = new EyeAgent(
    eyeRenderer.getLeftEyeCenter(),
    eyeRenderer.getRightEyeCenter(),
    eyeRenderer.getEyeWidth(),
    eyeRenderer.getEyeHeight(),
    eyeRenderer.getPupilDiameter()
  );
  gazeInput = new MouseGazeInput(); //to test Eye Behaviour if it gets input
  gazeMapper = new GazeMapper(eyeAgent, eyeRenderer.getEyeWidth(), eyeRenderer.getEyeHeight());
  gazeClassifier = new GazeClassifier(eyeAgent);

  idleMovementController = new IdleMovementController(eyeAgent);
  gazeAwareController = new GazeAwareController(eyeAgent, gazeInput);

  // activeEyeController = idleMovementController;
  activeEyeController = gazeAwareController;
}

void draw() {
  currentGazeSample = gazeInput.getCurrentSample();
  currentGazeRegion = gazeMapper.map(currentGazeSample);

  activeEyeController.update();
  eyeAgent.update();

  gazeClassifier.update(currentGazeRegion, currentGazeSample);
  currentGazeState = gazeClassifier.getStableState();
  gazeBreakDetected = gazeClassifier.hasGazeBreakDetected();

  eyeRenderer.clear();
  eyeRenderer.drawEyes(
    eyeAgent.getLeftPupilPosition(),
    eyeAgent.getRightPupilPosition()
  );
  drawDebugInfo();
}

void keyPressed() {
  if (key == '1') {
    activeEyeController = idleMovementController;
  }

  if (key == '2') {
    activeEyeController = gazeAwareController;
  }
}

void drawDebugInfo() {
  pushStyle();

  fill(0);
  textSize(18);
  text("Gaze region: " + currentGazeRegion, 24, 34);
  text("Gaze state: " + currentGazeState, 24, 58);

  if (gazeBreakDetected) {
    text("Gaze break", 24, 82);
  }

  popStyle();
}
