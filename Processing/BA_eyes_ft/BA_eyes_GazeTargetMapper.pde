class GazeTargetMapper {
  EyeAgent eyeAgent;

  float inputDistanceForMaxEyeMovement = 350;

  GazeTargetMapper(EyeAgent eyeAgent) {
    this.eyeAgent = eyeAgent;
  }

  PVector leftPupilTargetForSample(GazeSample sample) {
    PVector faceCenter = eyeAgent.getFaceCenter();
    PVector leftEyeCenter = eyeAgent.getLeftEyeCenter();

    float dx = sample.x - faceCenter.x;
    float dy = sample.y - faceCenter.y;

    float targetX = leftEyeCenter.x + dx / inputDistanceForMaxEyeMovement * eyeAgent.getTargetRadiusX();
    float targetY = leftEyeCenter.y + dy / inputDistanceForMaxEyeMovement * eyeAgent.getTargetRadiusY();

    return eyeAgent.constrainTargetToEye(new PVector(targetX, targetY), leftEyeCenter);
  }
}
