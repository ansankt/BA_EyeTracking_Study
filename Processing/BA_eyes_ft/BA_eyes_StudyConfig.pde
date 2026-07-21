class StudyConfig {
  String participantId = "P_TEST";
  boolean debugMode = true;

  int questionsPerTrial = 5;
  int totalQuestionCount = 10;
  int sampleLogInterval = 33;
  int breakDuration = 2500;

  String questionDirectory = "questions";
  String questionFilePrefix = "question_";
  String questionFileExtension = ".mp3";

  String gazeAwareCondition = "GAZE_AWARE";
  String gazeUnawareCondition = "GAZE_UNAWARE";

  String gazeInputMode = "MOUSE";
  String mouseGazeInputMode = "MOUSE";
  String tobiiGazeInputMode = "TOBII";

  int lookingAtEyesToMutualGazeMs = 300;
  int lostGazeToRandomMs = 200;
  int maxMutualGazeDurationMs = 3600;
  int gazeBreakDurationMs = 1250;

  float gazeAwareMutualTriggerEyeScale = 0.45;
  float gazeAwareMutualGazeSpeed = 6.0;
  float gazeAwareBreakSpeed = 5.0;
}
