class GazeClassifier {
  int stableDuration = 150;
  float agentLooksAtUserTolerance;

  GazeState stableState = GazeState.INVALID;
  GazeState candidateState = GazeState.INVALID;

  int candidateSince = 0;
  int lastStateChangeTime = 0;

  boolean stateChanged = false;
  boolean mutualGazeEnded = false;

  EyeAgent eyeAgent;
  GazeMapper gazeMapper;
  StudyConfig config;
  VisualAngleConverter angleConverter;

  GazeClassifier(EyeAgent eyeAgent, GazeMapper gazeMapper, StudyConfig config) {
    this.eyeAgent = eyeAgent;
    this.gazeMapper = gazeMapper;
    this.config = config;
    angleConverter = new VisualAngleConverter(config);
    agentLooksAtUserTolerance = angleConverter.degToPxX(config.agentLooksAtUserToleranceDeg);
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

  boolean agentLooksAtUser() {
    return eyeAgent.getLeftPupilPosition().dist(eyeAgent.getLeftEyeCenter()) <= agentLooksAtUserTolerance;
  }

  boolean isAgentLookingAtUser() {
    return agentLooksAtUser();
  }

  float getAgentLooksAtUserTolerancePx() {
    return agentLooksAtUserTolerance;
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
