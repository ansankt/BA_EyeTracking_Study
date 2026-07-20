class GazeAwareController implements EyeController {
  EyeAgent eyeAgent;
  StudyConfig config;
  EventLogger eventLogger;
  IdleMovementController randomGazeController;

  GazeAwareMode mode = GazeAwareMode.RANDOM_GAZE;
  int modeStartTime = 0;
  int lookingAtEyesSince = -1;
  int notLookingAtEyesSince = -1;

  GazeAwareController(EyeAgent eyeAgent, StudyConfig config, EventLogger eventLogger) {
    this.eyeAgent = eyeAgent;
    this.config = config;
    this.eventLogger = eventLogger;
    randomGazeController = new IdleMovementController(eyeAgent);
    resetToRandomGaze();
  }

  void update(GazeRegion currentGazeRegion) {
    boolean userLookingAtEyes = isUserLookingAtEyes(currentGazeRegion);

    if (mode == GazeAwareMode.RANDOM_GAZE) {
      updateRandomGaze(userLookingAtEyes, currentGazeRegion);
    } else if (mode == GazeAwareMode.MUTUAL_GAZE) {
      updateMutualGaze(userLookingAtEyes);
    } else if (mode == GazeAwareMode.GAZE_BREAK) {
      updateGazeBreak(userLookingAtEyes);
    }
  }

  void updateRandomGaze(boolean userLookingAtEyes, GazeRegion currentGazeRegion) {
    randomGazeController.update(currentGazeRegion);

    if (userLookingAtEyes) {
      if (lookingAtEyesSince < 0) {
        lookingAtEyesSince = millis();
      }

      if (millis() - lookingAtEyesSince >= config.lookingAtEyesToMutualGazeMs) {
        enterMode(GazeAwareMode.MUTUAL_GAZE);
      }
    } else {
      lookingAtEyesSince = -1;
    }
  }

  void updateMutualGaze(boolean userLookingAtEyes) {
    eyeAgent.setMovementSpeed(config.gazeAwareMutualGazeSpeed);
    eyeAgent.setSharedTargetFromLeftEye(eyeAgent.getLeftEyeCenter());

    if (!userLookingAtEyes) {
      if (notLookingAtEyesSince < 0) {
        notLookingAtEyesSince = millis();
      }

      if (millis() - notLookingAtEyesSince >= config.lostGazeToRandomMs) {
        enterMode(GazeAwareMode.RANDOM_GAZE);
      }
    } else {
      notLookingAtEyesSince = -1;
    }

    if (millis() - modeStartTime >= config.maxMutualGazeDurationMs) {
      enterMode(GazeAwareMode.GAZE_BREAK);
    }
  }

  void updateGazeBreak(boolean userLookingAtEyes) {
    if (!userLookingAtEyes) {
      if (notLookingAtEyesSince < 0) {
        notLookingAtEyesSince = millis();
      }

      if (millis() - notLookingAtEyesSince >= config.lostGazeToRandomMs) {
        enterMode(GazeAwareMode.RANDOM_GAZE);
      }

      return;
    }

    notLookingAtEyesSince = -1;

    if (millis() - modeStartTime >= config.gazeBreakDurationMs) {
      enterMode(GazeAwareMode.MUTUAL_GAZE);
    }
  }

  void enterMode(GazeAwareMode newMode) {
    mode = newMode;
    modeStartTime = millis();
    lookingAtEyesSince = -1;
    notLookingAtEyesSince = -1;

    if (mode == GazeAwareMode.MUTUAL_GAZE) {
      eyeAgent.setMovementSpeed(config.gazeAwareMutualGazeSpeed);
      eyeAgent.setSharedTargetFromLeftEye(eyeAgent.getLeftEyeCenter());
    }

    if (mode == GazeAwareMode.GAZE_BREAK) {
      eyeAgent.setMovementSpeed(config.gazeAwareBreakSpeed);
      eyeAgent.setSharedTargetFromLeftEye(randomBreakTarget());
    }

    eventLogger.logEvent("GAZE_AWARE_MODE_CHANGE", currentGazeRegion, currentGazeState, mode.toString());
  }

  void resetToRandomGaze() {
    mode = GazeAwareMode.RANDOM_GAZE;
    modeStartTime = millis();
    lookingAtEyesSince = -1;
    notLookingAtEyesSince = -1;
    randomGazeController = new IdleMovementController(eyeAgent);
  }

  PVector randomBreakTarget() {
    PVector center = eyeAgent.getLeftEyeCenter();
    float direction = random(1) < 0.5 ? -1 : 1;

    return new PVector(
      center.x + direction * eyeAgent.getTargetRadiusX(),
      center.y + random(-0.35, 0.35) * eyeAgent.getTargetRadiusY()
    );
  }

  boolean isUserLookingAtEyes(GazeRegion region) {
    return region == GazeRegion.LEFT_EYE || region == GazeRegion.RIGHT_EYE;
  }

  GazeAwareMode getMode() {
    return mode;
  }
}
