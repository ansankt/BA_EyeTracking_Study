class GazeMapper {
  EyeAgent eyeAgent;

  float eyeRadiusX;
  float eyeRadiusY;
  float faceMarginX = 90;
  float faceMarginY = 90;

  GazeMapper(EyeAgent eyeAgent, float eyeWidth, float eyeHeight) {
    this.eyeAgent = eyeAgent;
    eyeRadiusX = eyeWidth / 2;
    eyeRadiusY = eyeHeight / 2;
  }

  GazeRegion map(GazeSample sample) {
    if (sample == null || !sample.valid) {
      return GazeRegion.INVALID;
    }

    PVector gazePoint = new PVector(sample.x, sample.y);

    if (isInsideEye(gazePoint, eyeAgent.getLeftEyeCenter())) {
      return GazeRegion.LEFT_EYE;
    }

    if (isInsideEye(gazePoint, eyeAgent.getRightEyeCenter())) {
      return GazeRegion.RIGHT_EYE;
    }

    if (isInsideFaceArea(gazePoint)) {
      return GazeRegion.FACE;
    }

    return GazeRegion.OUTSIDE;
  }

  boolean isInsideEye(PVector point, PVector eyeCenter) {
    float dx = point.x - eyeCenter.x;
    float dy = point.y - eyeCenter.y;
    float ellipseValue = sq(dx) / sq(eyeRadiusX) + sq(dy) / sq(eyeRadiusY);

    return ellipseValue <= 1;
  }

  boolean isInsideFaceArea(PVector point) {
    PVector leftEyeCenter = eyeAgent.getLeftEyeCenter();
    PVector rightEyeCenter = eyeAgent.getRightEyeCenter();

    float left = leftEyeCenter.x - eyeRadiusX - faceMarginX;
    float right = rightEyeCenter.x + eyeRadiusX + faceMarginX;
    float top = leftEyeCenter.y - eyeRadiusY - faceMarginY;
    float bottom = leftEyeCenter.y + eyeRadiusY + faceMarginY;

    return point.x >= left
      && point.x <= right
      && point.y >= top
      && point.y <= bottom;
  }
}
