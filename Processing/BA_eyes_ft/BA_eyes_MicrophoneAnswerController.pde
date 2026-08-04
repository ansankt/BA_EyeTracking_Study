class MicrophoneAnswerController {
  PApplet parent;
  StudyConfig config;
  Sound sound;
  AudioIn microphone;
  Amplitude amplitude;

  float currentLevel = 0;
  float meanNoise = 0;
  float maxNoise = 0;
  float speechThreshold = 0;

  boolean calibrating = false;
  boolean calibrationComplete = false;
  int calibrationStartTime = 0;
  float noiseSum = 0;
  int noiseSampleCount = 0;

  boolean detectingAnswer = false;
  boolean speechDetected = false;
  boolean answerFinished = false;
  int speechAboveThresholdSince = -1;
  int lastSpeechTime = 0;

  MicrophoneAnswerController(PApplet parent, StudyConfig config) {
    this.parent = parent;
    this.config = config;

    if (config.printSoundDevicesOnStart) {
      println("Available sound devices:");
      printArray(Sound.list());
    }

    sound = new Sound(parent);

    if (config.microphoneInputDevice >= 0) {
      sound.inputDevice(config.microphoneInputDevice);
      println("Selected microphone input device: " + config.microphoneInputDevice);
    }

    microphone = new AudioIn(parent, 0);
    microphone.start();
    microphone.amp(config.microphoneGain);

    amplitude = new Amplitude(parent);
    amplitude.input(microphone);
  }

  void startCalibration() {
    calibrating = true;
    calibrationComplete = false;
    calibrationStartTime = millis();
    noiseSum = 0;
    noiseSampleCount = 0;
    meanNoise = 0;
    maxNoise = 0;
    speechThreshold = 0;
  }

  void updateCalibration() {
    if (!calibrating) {
      return;
    }

    updateLevel();
    noiseSum += currentLevel;
    noiseSampleCount++;
    maxNoise = max(maxNoise, currentLevel);

    if (millis() - calibrationStartTime >= config.micCalibrationDurationMs) {
      finishCalibration();
    }
  }

  void finishCalibration() {
    calibrating = false;
    calibrationComplete = true;

    if (noiseSampleCount > 0) {
      meanNoise = noiseSum / noiseSampleCount;
    }

    speechThreshold = max(meanNoise * 3.0, maxNoise * 1.3);
  }

  void startAnswerDetection() {
    detectingAnswer = true;
    speechDetected = false;
    answerFinished = false;
    speechAboveThresholdSince = -1;
    lastSpeechTime = millis();
  }

  void updateAnswerDetection() {
    if (!detectingAnswer) {
      return;
    }

    updateLevel();

    if (currentLevel > speechThreshold) {
      if (speechAboveThresholdSince < 0) {
        speechAboveThresholdSince = millis();
      }

      lastSpeechTime = millis();

      if (millis() - speechAboveThresholdSince >= config.minSpeechDurationMs) {
        speechDetected = true;
      }
    } else {
      speechAboveThresholdSince = -1;
    }

    if (speechDetected && millis() - lastSpeechTime >= config.silenceToCompleteAnswerMs) {
      answerFinished = true;
      detectingAnswer = false;
    }
  }

  void updateLevel() {
    microphone.amp(config.microphoneGain);
    currentLevel = amplitude.analyze();
  }

  boolean isCalibrationComplete() {
    return calibrationComplete;
  }

  boolean hasAnswerFinished() {
    return answerFinished;
  }

  float getCurrentLevel() {
    return currentLevel;
  }

  float getMeanNoise() {
    return meanNoise;
  }

  float getMaxNoise() {
    return maxNoise;
  }

  float getSpeechThreshold() {
    return speechThreshold;
  }

  boolean isSpeechDetected() {
    return speechDetected;
  }

  boolean isDetectingAnswer() {
    return detectingAnswer;
  }

  boolean isCalibrating() {
    return calibrating;
  }
}
