class GazeClassifier {
  int stableDuration = 150;
  float inputDistanceForMaxEyeMovement = 350;
  float mutualGazeTolerance = 18;

  GazeState stableState = GazeState.INVALID;
  GazeState candidateState = GazeState.INVALID;

  int candidateSince = 0;
  int lastStateChangeTime = 0;

  boolean stateChanged = false;
  boolean gazeBreakDetected = false;

  EyeAgent eyeAgent;

  GazeClassifier(EyeAgent eyeAgent) {
    this.eyeAgent = eyeAgent;
    candidateSince = millis();
    lastStateChangeTime = millis();
  }

  void update(GazeRegion region, GazeSample sample) {
    stateChanged = false;
    gazeBreakDetected = false;

    GazeState mappedState = mapRegionToState(region, sample);

    if (mappedState != candidateState) {
      candidateState = mappedState;
      candidateSince = millis();
      return;
    }

    if (mappedState != stableState && millis() - candidateSince >= stableDuration) {
      GazeState previousState = stableState;
      stableState = mappedState;
      lastStateChangeTime = millis();
      stateChanged = true;

      gazeBreakDetected = previousState == GazeState.MUTUAL_GAZE
        && stableState != GazeState.MUTUAL_GAZE;
    }
  }

  GazeState mapRegionToState(GazeRegion region, GazeSample sample) {
    if (region == GazeRegion.LEFT_EYE || region == GazeRegion.RIGHT_EYE) {
      if (agentEyesLookAtSample(sample)) {
        return GazeState.MUTUAL_GAZE;
      }

      return GazeState.LOOKING_AT_EYES;
    }

    if (region == GazeRegion.FACE) {
      return GazeState.LOOKING_AT_FACE;
    }

    if (region == GazeRegion.OUTSIDE) {
      return GazeState.LOOKING_AWAY;
    }

    return GazeState.INVALID;
  }

  boolean agentEyesLookAtSample(GazeSample sample) {
    if (sample == null || !sample.valid) {
      return false;
    }

    PVector expectedLeftPupil = expectedLeftPupilTargetForSample(sample);
    PVector currentLeftPupil = eyeAgent.getLeftPupilPosition();

    return currentLeftPupil.dist(expectedLeftPupil) <= mutualGazeTolerance;
  }

  PVector expectedLeftPupilTargetForSample(GazeSample sample) {
    PVector faceCenter = eyeAgent.getFaceCenter();
    PVector leftEyeCenter = eyeAgent.getLeftEyeCenter();

    float dx = sample.x - faceCenter.x;
    float dy = sample.y - faceCenter.y;

    float targetX = leftEyeCenter.x + dx / inputDistanceForMaxEyeMovement * eyeAgent.getTargetRadiusX();
    float targetY = leftEyeCenter.y + dy / inputDistanceForMaxEyeMovement * eyeAgent.getTargetRadiusY();

    return eyeAgent.constrainTargetToEye(new PVector(targetX, targetY), leftEyeCenter);
  }

  GazeState getStableState() {
    return stableState;
  }

  GazeState getCandidateState() {
    return candidateState;
  }

  boolean hasStateChanged() {
    return stateChanged;
  }

  boolean hasGazeBreakDetected() {
    return gazeBreakDetected;
  }

  int getCurrentStateDuration() {
    return millis() - lastStateChangeTime;
  }
}
