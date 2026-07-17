class GazeAwareController implements EyeController {
  EyeAgent eyeAgent;
  GazeInput gazeInput;

  float movementSpeed = 6.0;
  float inputDistanceForMaxEyeMovement = 350;

  GazeAwareController(EyeAgent eyeAgent, GazeInput gazeInput) {
    this.eyeAgent = eyeAgent;
    this.gazeInput = gazeInput;
  }

  void update() {
    GazeSample currentSample = gazeInput.getCurrentSample();

    if (!currentSample.valid) {
      return;
    }

    eyeAgent.setMovementSpeed(movementSpeed);
    eyeAgent.setSharedTargetFromLeftEye(targetForGazeSample(currentSample));
  }

  PVector targetForGazeSample(GazeSample sample) { //currently looking directly at input position
    PVector faceCenter = eyeAgent.getFaceCenter();
    PVector leftEyeCenter = eyeAgent.getLeftEyeCenter();

    float dx = sample.x - faceCenter.x;
    float dy = sample.y - faceCenter.y;

    float targetX = leftEyeCenter.x + dx / inputDistanceForMaxEyeMovement * eyeAgent.getTargetRadiusX(); //theoretically not right, because eyemovement is mirrored so the pupils dont look 100% in the right direction, but it looks more natural
    float targetY = leftEyeCenter.y + dy / inputDistanceForMaxEyeMovement * eyeAgent.getTargetRadiusY();

    return new PVector(targetX, targetY);
  }
}
