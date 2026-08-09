class IdleMovementController implements EyeController {
  static final int TARGET_ANYWHERE = 0;
  static final int TARGET_NEAR_CENTER = 1;
  static final int TARGET_SMALL_SACCADE = 2;
  static final int TARGET_MIXED = 3;

  EyeAgent eyeAgent;
  StudyConfig config;

  int targetMode = TARGET_MIXED; //speciefies the strategy for the next eye position 

  int minWaitTime = 800; //Fixation Time
  int maxWaitTime = 3000;

  float minMovementSpeed = 1.5;
  float maxMovementSpeed = 6.0;

  float centerBias = 0.65;
  float smallSaccadeProbability = 0.55;
  float returnToCenterProbability = 0.15;

  float smallSaccadeMinDistance = 20;
  float smallSaccadeMaxDistance = 85;

  boolean waiting = false;
  int waitUntil = 0;
  int nextSaccadeTime = 0;

  IdleMovementController(EyeAgent eyeAgent, StudyConfig config) {
    this.eyeAgent = eyeAgent;
    this.config = config;
    reset();
  }

  void update(GazeRegion currentGazeRegion, GazeSample currentGazeSample) {
    if (usesChatvrmSaccades()) {
      updateChatvrmSaccade();
      return;
    }

    updateRandomWander();
  }

  void reset() {
    waiting = false;
    nextSaccadeTime = 0;

    if (usesChatvrmSaccades()) {
      eyeAgent.setMovementSpeed(config.idleSaccadeMovementSpeed);
      eyeAgent.setSharedTargetFromLeftEye(centerTarget());
      scheduleNextSaccade();
      return;
    }

    startWaiting();
  }

  boolean usesChatvrmSaccades() {
    return config.idleMovementPattern.equals(config.chatvrmSaccadeIdlePattern);
  }

  void updateChatvrmSaccade() {
    if (millis() >= nextSaccadeTime) {
      chooseChatvrmSaccadeTarget();
      scheduleNextSaccade();
    }
  }

  void scheduleNextSaccade() {
    nextSaccadeTime = millis() + int(random(config.idleSaccadeMinIntervalMs, config.idleSaccadeMaxIntervalMs));
  }

  void chooseChatvrmSaccadeTarget() {
    eyeAgent.setMovementSpeed(config.idleSaccadeMovementSpeed);
    eyeAgent.setSharedTargetFromLeftEye(randomChatvrmSaccadeTarget());
  }

  PVector randomChatvrmSaccadeTarget() {
    PVector center = eyeAgent.getLeftEyeCenter();

    return new PVector(
      center.x + random(-1, 1) * eyeAgent.getTargetRadiusX() * config.idleSaccadeRadiusScale,
      center.y + random(-1, 1) * eyeAgent.getTargetRadiusY() * config.idleSaccadeRadiusScale
    );
  }

  void updateRandomWander() {
    if (waiting) {
      if (millis() >= waitUntil) {
        waiting = false;
        chooseNewTarget();
      }
      return;
    }

    if (eyeAgent.hasReachedTarget()) {
      startWaiting();
    }
  }

  void startWaiting() {
    waiting = true;
    waitUntil = millis() + int(random(minWaitTime, maxWaitTime));
  }

  void chooseNewTarget() {
    eyeAgent.setMovementSpeed(random(minMovementSpeed, maxMovementSpeed));
    eyeAgent.setSharedTargetFromLeftEye(createTarget());
  }

  PVector createTarget() {
    if (targetMode == TARGET_ANYWHERE) {
      return randomTargetAnywhere();
    }

    if (targetMode == TARGET_NEAR_CENTER) {
      return randomTargetNearCenter();
    }

    if (targetMode == TARGET_SMALL_SACCADE) {
      return randomSmallSaccadeTarget();
    }

    return randomMixedTarget();
  }

  PVector randomMixedTarget() {
    float choice = random(1);

    if (choice < returnToCenterProbability) {
      return centerTarget();
    }

    if (choice < returnToCenterProbability + smallSaccadeProbability) {
      return randomSmallSaccadeTarget();
    }

    return randomTargetNearCenter();
  }

  PVector randomTargetAnywhere() {
    return randomTargetInEllipse(1.0);
  }

  PVector randomTargetNearCenter() {
    return randomTargetInEllipse(centerBias);
  }

  PVector randomSmallSaccadeTarget() {
    PVector currentPosition = eyeAgent.getLeftPupilPosition();
    float angle = random(TWO_PI);
    float distance = random(smallSaccadeMinDistance, smallSaccadeMaxDistance);

    return new PVector(
      currentPosition.x + cos(angle) * distance,
      currentPosition.y + sin(angle) * distance
    );
  }

  PVector randomTargetInEllipse(float radiusScale) {
    PVector center = eyeAgent.getLeftEyeCenter();
    float angle = random(TWO_PI);
    float radius = sqrt(random(1)) * radiusScale;

    return new PVector(
      center.x + cos(angle) * radius * eyeAgent.getTargetRadiusX(),
      center.y + sin(angle) * radius * eyeAgent.getTargetRadiusY()
    );
  }

  PVector centerTarget() {
    return eyeAgent.getLeftEyeCenter();
  }

  String getPatternName() {
    return config.idleMovementPattern;
  }

  int getNextSaccadeTime() {
    return nextSaccadeTime;
  }

  int getTimeUntilNextSaccade() {
    return max(0, nextSaccadeTime - millis());
  }
}
