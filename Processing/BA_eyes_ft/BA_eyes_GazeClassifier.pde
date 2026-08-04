class GazeClassifier {
  int stableDuration = 150;
  float pupilHitRadius;
  float agentLooksAtUserTolerance = 18;

  GazeState stableState = GazeState.INVALID;
  GazeState candidateState = GazeState.INVALID;

  int candidateSince = 0;
  int lastStateChangeTime = 0;

  boolean stateChanged = false;
  boolean mutualGazeEnded = false;

  EyeAgent eyeAgent;
  GazeMapper gazeMapper;

  GazeClassifier(EyeAgent eyeAgent, float pupilDiameter, GazeMapper gazeMapper) {
    this.eyeAgent = eyeAgent;
    this.gazeMapper = gazeMapper;
    pupilHitRadius = pupilDiameter / 2;
    candidateSince = millis();
    lastStateChangeTime = millis();
  }

  void update(GazeRegion region, GazeSample sample) {
    stateChanged = false;
    mutualGazeEnded = false;

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

      mutualGazeEnded = previousState == GazeState.MUTUAL_GAZE
        && stableState != GazeState.MUTUAL_GAZE;
    }
  }

  GazeState mapRegionToState(GazeRegion region, GazeSample sample) {
    if (gazeMapper.isInsideMutualGazeArea(sample)) {
      if (agentLooksAtUser()) {
        return GazeState.MUTUAL_GAZE;
      }

      return GazeState.LOOKING_AT_EYES;
    }

    if (region == GazeRegion.LEFT_EYE || region == GazeRegion.RIGHT_EYE) {
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

  boolean sampleHitsCurrentPupil(GazeRegion region, GazeSample sample) {
    if (sample == null || !sample.valid) {
      return false;
    }

    PVector gazePoint = new PVector(sample.x, sample.y);

    if (region == GazeRegion.LEFT_EYE) {
      return gazePoint.dist(eyeAgent.getLeftPupilPosition()) <= pupilHitRadius;
    }

    if (region == GazeRegion.RIGHT_EYE) {
      return gazePoint.dist(eyeAgent.getRightPupilPosition()) <= pupilHitRadius;
    }

    return false;
  }

  boolean agentLooksAtUser() {
    return eyeAgent.getLeftPupilPosition().dist(eyeAgent.getLeftEyeCenter()) <= agentLooksAtUserTolerance;
      // && eyeAgent.getRightPupilPosition().dist(eyeAgent.getRightEyeCenter()) <= agentLooksAtUserTolerance; //right not needed because pupils are mirrored
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

  boolean hasMutualGazeEnded() {
    return mutualGazeEnded;
  }

  int getCurrentStateDuration() {
    return millis() - lastStateChangeTime;
  }
}
