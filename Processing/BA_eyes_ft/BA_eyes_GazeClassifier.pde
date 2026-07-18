class GazeClassifier {
  int stableDuration = 150;

  GazeState stableState = GazeState.INVALID;
  GazeState candidateState = GazeState.INVALID;

  int candidateSince = 0;
  int lastStateChangeTime = 0;

  boolean stateChanged = false;
  boolean gazeBreakDetected = false;

  GazeClassifier() {
    candidateSince = millis();
    lastStateChangeTime = millis();
  }

  void update(GazeRegion region) {
    stateChanged = false;
    gazeBreakDetected = false;

    GazeState mappedState = mapRegionToState(region);

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

  GazeState mapRegionToState(GazeRegion region) {
    if (region == GazeRegion.LEFT_EYE || region == GazeRegion.RIGHT_EYE) {
      return GazeState.MUTUAL_GAZE;
    }

    if (region == GazeRegion.FACE) {
      return GazeState.LOOKING_AT_FACE;
    }

    if (region == GazeRegion.OUTSIDE) {
      return GazeState.LOOKING_AWAY;
    }

    return GazeState.INVALID;
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
