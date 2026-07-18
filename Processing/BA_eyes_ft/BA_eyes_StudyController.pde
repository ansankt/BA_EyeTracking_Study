EyeRenderer eyeRenderer;
EyeAgent eyeAgent;
GazeInput gazeInput;
GazeMapper gazeMapper;
GazeTargetMapper gazeTargetMapper;
GazeClassifier gazeClassifier;
EventLogger eventLogger;
GazeSample currentGazeSample;
GazeRegion currentGazeRegion = GazeRegion.INVALID;
GazeState currentGazeState = GazeState.INVALID;
boolean gazeBreakDetected = false;
int lastSampleLogTime = 0;
int sampleLogInterval = 33;

EyeController activeEyeController;
IdleMovementController idleMovementController;
GazeAwareController gazeAwareController;
String activeCondition = "GAZE_AWARE";

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
  gazeTargetMapper = new GazeTargetMapper(eyeAgent);
  gazeClassifier = new GazeClassifier(eyeAgent, eyeRenderer.getPupilDiameter());
  eventLogger = new EventLogger();

  idleMovementController = new IdleMovementController(eyeAgent);
  gazeAwareController = new GazeAwareController(eyeAgent, gazeInput, gazeTargetMapper);

  // activeEyeController = idleMovementController;
  activeEyeController = gazeAwareController;
  eventLogger.setContext("P_TEST", 0, activeCondition);
  eventLogger.logEvent("SESSION_START", currentGazeRegion, currentGazeState, "Mouse input test session");
}

void draw() {
  currentGazeSample = gazeInput.getCurrentSample();
  currentGazeRegion = gazeMapper.map(currentGazeSample);

  activeEyeController.update();
  eyeAgent.update();

  gazeClassifier.update(currentGazeRegion, currentGazeSample);
  currentGazeState = gazeClassifier.getStableState();
  gazeBreakDetected = gazeClassifier.hasGazeBreakDetected();

  logCurrentFrame();

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
    setActiveCondition("GAZE_UNAWARE");
  }

  if (key == '2') {
    activeEyeController = gazeAwareController;
    setActiveCondition("GAZE_AWARE");
  }
}

void setActiveCondition(String condition) {
  if (condition.equals(activeCondition)) {
    return;
  }

  activeCondition = condition;
  eventLogger.setCondition(activeCondition);
  eventLogger.logEvent("CONDITION_SWITCH", currentGazeRegion, currentGazeState, activeCondition);
}

void logCurrentFrame() {
  if (gazeClassifier.hasStateChanged()) {
    eventLogger.logEvent("GAZE_STATE_CHANGE", currentGazeRegion, currentGazeState, "");
  }

  if (gazeBreakDetected) {
    eventLogger.logEvent("GAZE_BREAK", currentGazeRegion, currentGazeState, "");
  }

  if (millis() - lastSampleLogTime >= sampleLogInterval) {
    eventLogger.logSample(currentGazeSample, currentGazeRegion, currentGazeState, eyeAgent);
    lastSampleLogTime = millis();
  }
}

void exit() {
  eventLogger.logEvent("SESSION_END", currentGazeRegion, currentGazeState, "");
  eventLogger.close();
  super.exit();
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
