class GazeClassifier {
  int stableDuration = 150;
  float mutualGazeTolerance = 18;

  GazeState stableState = GazeState.INVALID;
  GazeState candidateState = GazeState.INVALID;

  int candidateSince = 0;
  int lastStateChangeTime = 0;

  boolean stateChanged = false;
  boolean gazeBreakDetected = false;

  EyeAgent eyeAgent;
  GazeTargetMapper gazeTargetMapper;

  GazeClassifier(EyeAgent eyeAgent, GazeTargetMapper gazeTargetMapper) {
    this.eyeAgent = eyeAgent;
    this.gazeTargetMapper = gazeTargetMapper;
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

    PVector expectedLeftPupil = gazeTargetMapper.leftPupilTargetForSample(sample);
    PVector currentLeftPupil = eyeAgent.getLeftPupilPosition();

    return currentLeftPupil.dist(expectedLeftPupil) <= mutualGazeTolerance;
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
