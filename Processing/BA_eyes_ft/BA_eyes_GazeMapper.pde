class GazeMapper {
  EyeAgent eyeAgent;
  StudyConfig config;
  VisualAngleConverter angleConverter;

  float eyeRadiusX;
  float eyeRadiusY;
  float faceMarginX = 90;
  float faceMarginY = 90;

  GazeMapper(EyeAgent eyeAgent, float eyeWidth, float eyeHeight, StudyConfig config) {
    this.eyeAgent = eyeAgent;
    this.config = config;
    angleConverter = new VisualAngleConverter(config);
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

  boolean isInsideMutualGazeArea(GazeSample sample) {
    if (sample == null || !sample.valid) {
      return false;
    }

    return isInsideMutualGazeArea(new PVector(sample.x, sample.y));
  }

  boolean isInsideMutualGazeArea(PVector point) {
    float[] area = mutualGazeAreaBounds();

    return point.x >= area[0]
      && point.x <= area[1]
      && point.y >= area[2]
      && point.y <= area[3];
  }

  float[] mutualGazeAreaBounds() {
    PVector leftEyeCenter = eyeAgent.getLeftEyeCenter();
    PVector rightEyeCenter = eyeAgent.getRightEyeCenter();

    float horizontalPadding = angleConverter.degToPxX(config.mutualGazeAreaHorizontalPaddingDeg);
    float areaHeight = angleConverter.degToPxY(config.mutualGazeAreaHeightDeg);
    float centerY = leftEyeCenter.y + angleConverter.degToPxY(config.mutualGazeAreaYOffsetDeg);

    float left = leftEyeCenter.x - eyeRadiusX - horizontalPadding;
    float right = rightEyeCenter.x + eyeRadiusX + horizontalPadding;
    float top = centerY - areaHeight / 2;
    float bottom = centerY + areaHeight / 2;

    return new float[] { left, right, top, bottom };
  }
}
