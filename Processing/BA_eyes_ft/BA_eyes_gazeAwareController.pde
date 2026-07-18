class GazeAwareController implements EyeController {
  EyeAgent eyeAgent;
  GazeInput gazeInput;
  GazeTargetMapper gazeTargetMapper;

  float movementSpeed = 6.0;

  GazeAwareController(EyeAgent eyeAgent, GazeInput gazeInput, GazeTargetMapper gazeTargetMapper) {
    this.eyeAgent = eyeAgent;
    this.gazeInput = gazeInput;
    this.gazeTargetMapper = gazeTargetMapper;
  }

  void update() {
    GazeSample currentSample = gazeInput.getCurrentSample();

    if (!currentSample.valid) {
      return;
    }

    eyeAgent.setMovementSpeed(movementSpeed);
    eyeAgent.setSharedTargetFromLeftEye(gazeTargetMapper.leftPupilTargetForSample(currentSample));
  }
}
