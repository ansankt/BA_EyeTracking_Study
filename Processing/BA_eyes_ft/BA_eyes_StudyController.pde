EyeRenderer eyeRenderer;
EyeAgent eyeAgent;
StudyConfig config;
GazeInput gazeInput;
GazeMapper gazeMapper;
GazeTargetMapper gazeTargetMapper;
GazeClassifier gazeClassifier;
EventLogger eventLogger;
QuestionController questionController;
GazeSample currentGazeSample;
GazeRegion currentGazeRegion = GazeRegion.INVALID;
GazeState currentGazeState = GazeState.INVALID;
boolean gazeBreakDetected = false;
int lastSampleLogTime = 0;

StudyPhase studyPhase = StudyPhase.INTRO;
Trial[] trials;
int currentTrialIndex = -1;
Trial currentTrial;
int breakStartTime = 0;

EyeController activeEyeController;
IdleMovementController idleMovementController;
GazeAwareController gazeAwareController;
String activeCondition = "";

void setup() {
  //size(800, 800);
  fullScreen();
  config = new StudyConfig();
  activeCondition = config.gazeAwareCondition;

  eyeRenderer = new EyeRenderer();
  eyeAgent = new EyeAgent(
    eyeRenderer.getLeftEyeCenter(),
    eyeRenderer.getRightEyeCenter(),
    eyeRenderer.getEyeWidth(),
    eyeRenderer.getEyeHeight(),
    eyeRenderer.getPupilDiameter()
  );
  gazeInput = createGazeInput();
  gazeMapper = new GazeMapper(eyeAgent, eyeRenderer.getEyeWidth(), eyeRenderer.getEyeHeight());
  gazeTargetMapper = new GazeTargetMapper(eyeAgent);
  gazeClassifier = new GazeClassifier(eyeAgent, eyeRenderer.getPupilDiameter());
  eventLogger = new EventLogger(config.participantId);

  idleMovementController = new IdleMovementController(eyeAgent);
  gazeAwareController = new GazeAwareController(eyeAgent, config, eventLogger);

  // activeEyeController = idleMovementController;
  activeEyeController = gazeAwareController;
  eventLogger.setContext(config.participantId, 0, activeCondition);
  eventLogger.logEvent("SESSION_START", currentGazeRegion, currentGazeState, "Mouse input test session");

  setupTrials();
}

GazeInput createGazeInput() {
  if (config.gazeInputMode.equals(config.tobiiGazeInputMode)) {
    return new TobiiGazeInput(this);
  }

  return new MouseGazeInput();
}

void draw() {
  currentGazeSample = gazeInput.getCurrentSample();
  currentGazeRegion = gazeMapper.map(currentGazeSample);

  updateStudyFlow();

  if (studyPhase == StudyPhase.TRIAL_RUNNING) {
    activeEyeController.update(currentGazeRegion, currentGazeSample);
    eyeAgent.update();
    questionController.update();
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

  if (config.debugMode) {
    drawDebugInfo();
  }
}

void keyPressed() {
  if (key == 'd' || key == 'D') {
    config.debugMode = !config.debugMode;
    eventLogger.logEvent("DEBUG_TOGGLE", currentGazeRegion, currentGazeState, "debug_mode=" + config.debugMode);
  }

  if (key == ' ') {
    if (studyPhase == StudyPhase.INTRO) {
      startNextTrial();
    } else if (studyPhase == StudyPhase.BREAK) {
      startNextTrial();
    }
  }

  if (key == ENTER || key == RETURN) {
    handleQuestionEnter();
  }

  if (config.debugMode && key == '1') {
    activeEyeController = idleMovementController;
    setActiveCondition(config.gazeUnawareCondition);
  }

  if (config.debugMode && key == '2') {
    activeEyeController = gazeAwareController;
    setActiveCondition(config.gazeAwareCondition);
  }
}

void setupTrials() { //initializes counterbalanced Order
  String[] conditions = counterbalancedConditions(config.participantId);
  Question[] shuffledQuestions = shuffledQuestions();
  trials = new Trial[conditions.length];

  for (int i = 0; i < conditions.length; i++) {
    trials[i] = new Trial(i + 1, conditions[i], questionsForTrial(shuffledQuestions, i, config.questionsPerTrial));
  }
}

Question[] shuffledQuestions() {
  Question[] questions = new Question[config.totalQuestionCount];

  for (int i = 0; i < questions.length; i++) {
    int questionNumber = i + 1;
    questions[i] = new Question(
      "Q" + nf(questionNumber, 2),
      sketchPath(config.questionDirectory + "/" + config.questionFilePrefix + questionNumber + config.questionFileExtension)
    );
  }

  for (int i = questions.length - 1; i > 0; i--) {
    int randomIndex = int(random(i + 1));
    Question tempQuestion = questions[i];
    questions[i] = questions[randomIndex];
    questions[randomIndex] = tempQuestion;
  }

  return questions;
}

Question[] questionsForTrial(Question[] shuffledQuestions, int trialIndex, int questionCount) {
  Question[] trialQuestions = new Question[questionCount];
  int startIndex = trialIndex * questionCount;

  for (int i = 0; i < questionCount; i++) {
    trialQuestions[i] = shuffledQuestions[startIndex + i];
  }

  return trialQuestions;
}

String[] counterbalancedConditions(String participantId) {
  if (participantIdIsEven(participantId)) {
    return new String[] { config.gazeAwareCondition, config.gazeUnawareCondition };
  }

  return new String[] { config.gazeUnawareCondition, config.gazeAwareCondition };
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
  if (studyPhase == StudyPhase.TRIAL_RUNNING && questionController.isComplete()) {
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
  questionController = new QuestionController(this, currentTrial.questions, eventLogger);
  eventLogger.logEvent("TRIAL_START", currentGazeRegion, currentGazeState, "question_count=" + currentTrial.questions.length);
}

void handleQuestionEnter() {
  if (studyPhase != StudyPhase.TRIAL_RUNNING || currentTrial == null) {
    return;
  }

  questionController.handleEnter();

  if (questionController.isComplete()) {
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
  if (condition.equals(config.gazeUnawareCondition)) {
    activeEyeController = idleMovementController;
  }

  if (condition.equals(config.gazeAwareCondition)) {
    gazeAwareController.resetToRandomGaze();
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

  if (millis() - lastSampleLogTime >= config.sampleLogInterval) {
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
  text("Debug: ON (D toggles)", 24, 34);
  text("Phase: " + studyPhase, 24, 58);
  text("Condition: " + activeCondition, 24, 82);
  text("Gaze region: " + currentGazeRegion, 24, 106);
  text("Gaze state: " + currentGazeState, 24, 130);
  text("Aware mode: " + gazeAwareController.getMode(), 24, 154);

  if (studyPhase == StudyPhase.INTRO) {
    text("Press SPACE to start", 24, 178);
  }

  if (studyPhase == StudyPhase.TRIAL_RUNNING && currentTrial != null) {
    text("Trial: " + currentTrial.id + " / " + trials.length, 24, 178);
    text("Question: " + questionController.currentQuestionNumber() + " / " + questionController.questionCount(), 24, 202);
    text("Question phase: " + questionController.getPhase(), 24, 226);
    text("Current question: " + questionController.currentQuestionId(), 24, 250);
  }

  if (studyPhase == StudyPhase.BREAK) {
    text("Break", 24, 178);
    text("Press SPACE after questionnaire", 24, 202);
  }

  if (studyPhase == StudyPhase.FINISHED) {
    text("Finished", 24, 178);
  }

  if (gazeBreakDetected) {
    text("Gaze break", 24, 274);
  }

  popStyle();
}
