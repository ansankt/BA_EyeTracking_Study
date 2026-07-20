class QuestionController {
  PApplet parent;
  EventLogger eventLogger;
  processing.sound.SoundFile currentAudio;

  Question[] questions;
  int currentQuestionIndex = -1;
  int completedQuestions = 0;
  Question currentQuestion;

  QuestionPhase phase = QuestionPhase.READY_TO_START;
  int phaseStartTime = 0;
  int answerLockoutAfterAudioMs = 2000;

  QuestionController(PApplet parent, Question[] questions, EventLogger eventLogger) {
    this.parent = parent;
    this.questions = questions;
    this.eventLogger = eventLogger;
  }

  void update() {
    if (phase == QuestionPhase.PLAYING_AUDIO && currentAudio != null && !currentAudio.isPlaying()) {
      phase = QuestionPhase.ANSWER_LOCKED;
      phaseStartTime = millis();
      logQuestionEvent("QUESTION_AUDIO_ENDED");
    }

    if (phase == QuestionPhase.ANSWER_LOCKED && millis() - phaseStartTime >= answerLockoutAfterAudioMs) {
      phase = QuestionPhase.WAITING_FOR_ANSWER;
      logQuestionEvent("QUESTION_ANSWER_ENABLED");
    }
  }

  void handleEnter() {
    if (phase == QuestionPhase.READY_TO_START) {
      startNextQuestion();
      return;
    }

    if (phase == QuestionPhase.WAITING_FOR_ANSWER) {
      completeCurrentQuestion();
    }
  }

  void startNextQuestion() {
    if (isComplete()) {
      phase = QuestionPhase.FINISHED;
      return;
    }

    currentQuestionIndex++;
    currentQuestion = questions[currentQuestionIndex];

    currentAudio = new processing.sound.SoundFile(parent, currentQuestion.audioPath);
    currentAudio.play();

    phase = QuestionPhase.PLAYING_AUDIO;
    phaseStartTime = millis();
    logQuestionEvent("QUESTION_STARTED");
  }

  void completeCurrentQuestion() {
    logQuestionEvent("QUESTION_COMPLETED");
    completedQuestions++;

    if (completedQuestions >= questions.length) {
      phase = QuestionPhase.FINISHED;
      return;
    }

    startNextQuestion();
  }

  boolean isComplete() {
    return phase == QuestionPhase.FINISHED;
  }

  int completedQuestionCount() {
    return completedQuestions;
  }

  int currentQuestionNumber() {
    if (currentQuestionIndex < 0) {
      return 0;
    }

    return currentQuestionIndex + 1;
  }

  int questionCount() {
    return questions.length;
  }

  String currentQuestionId() {
    if (currentQuestion == null) {
      return "";
    }

    return currentQuestion.id;
  }

  QuestionPhase getPhase() {
    return phase;
  }

  void logQuestionEvent(String eventType) {
    eventLogger.logQuestionEvent(
      eventType,
      currentGazeRegion,
      currentGazeState,
      currentQuestion.id,
      currentQuestionIndex + 1
    );
  }
}
