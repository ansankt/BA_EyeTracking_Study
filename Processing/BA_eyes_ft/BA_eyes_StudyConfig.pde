class StudyConfig {
  String participantId = "P_TEST";
  boolean debugMode = true;

  int questionsPerTrial = 5;
  int totalQuestionCount = 10;
  int sampleLogInterval = 33;
  int breakDuration = 2500;
  boolean useMicrophoneAnswerAdvance = true;
  boolean printSoundDevicesOnStart = true;
  int microphoneInputDevice = -1;
  float microphoneGain = 1.0;
  float minimumValidMicSignalLevel = 0.0001;
  int micCalibrationDurationMs = 2000;
  int silenceToCompleteAnswerMs = 1000;
  int minSpeechDurationMs = 200;

  String questionDirectory = "questions";
  String questionFilePrefix = "question_";
  String questionFileExtension = ".mp3";

  String gazeAwareCondition = "GAZE_AWARE";
  String gazeUnawareCondition = "GAZE_UNAWARE";

  String gazeInputMode = "MOUSE";
  String mouseGazeInputMode = "MOUSE";
  String tobiiGazeInputMode = "TOBII";

  float screenWidthCm = 34.5;
  float screenHeightCm = 19.4;
  float viewingDistanceCm = 60.0;

  float eyeWidthDeg = 4.0;
  float eyeHeightDeg = 6.0;
  float eyeDistanceDeg = 5.0;
  float pupilDiameterDeg = 1.0;
  float eyeStrokeWeight = 4.0;

  float mutualGazeAreaWidthDeg = 8.0;
  float mutualGazeAreaHeightDeg = 5.0;
  float mutualGazeAreaYOffsetDeg = 0.0;
  float agentLooksAtUserToleranceDeg = 0.5;

  int lookingAtEyesToMutualGazeMs = 300;
  int lostGazeToRandomMs = 200;
  int maxMutualGazeDurationMs = 3600;
  int gazeBreakDurationMs = 1250;

  float gazeAwareMutualGazeSpeed = 6.0;
  float gazeAwareBreakSpeed = 5.0;
}
