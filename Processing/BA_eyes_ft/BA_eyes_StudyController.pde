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

String participantId = "P_TEST";

StudyPhase studyPhase = StudyPhase.INTRO;
Trial[] trials;
int currentTrialIndex = -1;
Trial currentTrial;
int breakStartTime = 0;
int breakDuration = 2500;

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
  eventLogger.setContext(participantId, 0, activeCondition);
  eventLogger.logEvent("SESSION_START", currentGazeRegion, currentGazeState, "Mouse input test session");

  setupTrials();
}

void draw() {
  currentGazeSample = gazeInput.getCurrentSample();
  currentGazeRegion = gazeMapper.map(currentGazeSample);

  updateStudyFlow();

  if (studyPhase == StudyPhase.TRIAL_RUNNING) {
    activeEyeController.update();
    eyeAgent.update();
  }

  gazeClassifier.update(currentGazeRegion, currentGazeSample);
  currentGazeState = gazeClassifier.getStableState();
  gazeBreakDetected = gazeClassifier.hasGazeBreakDetected();

  if (studyPhase == StudyPhase.TRIAL_RUNNING) {
    logCurrentFrame();
  }

  eyeRenderer.clear();
  eyeRenderer.drawEyes(
    eyeAgent.getLeftPupilPosition(),
    eyeAgent.getRightPupilPosition()
  );
  drawDebugInfo();
}

void keyPressed() {
  if (key == ' ') {
    if (studyPhase == StudyPhase.INTRO) {
      startNextTrial();
    } else if (studyPhase == StudyPhase.BREAK) {
      startNextTrial();
    }
  }

  if (key == ENTER || key == RETURN) {
    completeCurrentQuestion();
  }

  if (key == '1') {
    activeEyeController = idleMovementController;
    setActiveCondition("GAZE_UNAWARE");
  }

  if (key == '2') {
    activeEyeController = gazeAwareController;
    setActiveCondition("GAZE_AWARE");
  }
}

void setupTrials() { //initializes counterbalanced Order
  String[] conditions = counterbalancedConditions(participantId);
  trials = new Trial[conditions.length];

  for (int i = 0; i < conditions.length; i++) {
    trials[i] = new Trial(i + 1, conditions[i], 5);
  }
}

String[] counterbalancedConditions(String participantId) {
  if (participantIdIsEven(participantId)) {
    return new String[] { "GAZE_AWARE", "GAZE_UNAWARE" };
  }

  return new String[] { "GAZE_UNAWARE", "GAZE_AWARE" };
}

boolean participantIdIsEven(String participantId) {
  String digits = "";

  for (int i = 0; i < participantId.length(); i++) {
    char currentChar = participantId.charAt(i);

    if (currentChar >= '0' && currentChar <= '9') {
      digits += currentChar;
    }
  }

  if (digits.length() == 0) {
    return false;
  }

  return int(digits) % 2 == 0;
}

void updateStudyFlow() {
  if (studyPhase == StudyPhase.TRIAL_RUNNING && currentTrial.isComplete()) {
    endCurrentTrial();
  }
}

void startNextTrial() {
  currentTrialIndex++;

  if (currentTrialIndex >= trials.length) {
    finishStudy();
    return;
  }

  currentTrial = trials[currentTrialIndex];
  studyPhase = StudyPhase.TRIAL_RUNNING;

  setActiveCondition(currentTrial.condition);
  eventLogger.startTrial(currentTrial.id, currentTrial.condition);
  eventLogger.logEvent("TRIAL_START", currentGazeRegion, currentGazeState, "question_count=" + currentTrial.questionCount);
}

void completeCurrentQuestion() {
  if (studyPhase != StudyPhase.TRIAL_RUNNING || currentTrial == null) {
    return;
  }

  currentTrial.completeQuestion();
  eventLogger.logEvent(
    "QUESTION_COMPLETED",
    currentGazeRegion,
    currentGazeState,
    "completed_questions=" + currentTrial.completedQuestions + ";question_count=" + currentTrial.questionCount
  );

  if (currentTrial.isComplete()) {
    endCurrentTrial();
  }
}

void endCurrentTrial() {
  eventLogger.logEvent("TRIAL_END", currentGazeRegion, currentGazeState, "");
  studyPhase = StudyPhase.BREAK;
  breakStartTime = millis();
  eventLogger.logEvent("BREAK_START", currentGazeRegion, currentGazeState, "");
}

void finishStudy() {
  studyPhase = StudyPhase.FINISHED;
  eventLogger.logEvent("STUDY_FINISHED", currentGazeRegion, currentGazeState, "");
}

void setActiveCondition(String condition) {
  applyActiveControllerForCondition(condition);

  if (condition.equals(activeCondition)) {
    return;
  }

  activeCondition = condition;
  eventLogger.setCondition(activeCondition);
  eventLogger.logEvent("CONDITION_SWITCH", currentGazeRegion, currentGazeState, activeCondition);
}

void applyActiveControllerForCondition(String condition) {
  if (condition.equals("GAZE_UNAWARE")) {
    activeEyeController = idleMovementController;
  }

  if (condition.equals("GAZE_AWARE")) {
    activeEyeController = gazeAwareController;
  }
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
  text("Phase: " + studyPhase, 24, 34);
  text("Condition: " + activeCondition, 24, 58);
  text("Gaze region: " + currentGazeRegion, 24, 82);
  text("Gaze state: " + currentGazeState, 24, 106);

  if (studyPhase == StudyPhase.INTRO) {
    text("Press SPACE to start", 24, 130);
  }

  if (studyPhase == StudyPhase.TRIAL_RUNNING && currentTrial != null) {
    text("Trial: " + currentTrial.id + " / " + trials.length, 24, 130);
    text("Questions: " + currentTrial.completedQuestions + " / " + currentTrial.questionCount, 24, 154);
    text("Press ENTER after question", 24, 178);
  }

  if (studyPhase == StudyPhase.BREAK) {
    text("Break", 24, 130);
    text("Press SPACE after questionnaire", 24, 154);
  }

  if (studyPhase == StudyPhase.FINISHED) {
    text("Finished", 24, 130);
  }

  if (gazeBreakDetected) {
    text("Gaze break", 24, 202);
  }

  popStyle();
}
