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
}
