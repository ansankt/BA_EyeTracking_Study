class EyeRenderer {
  StudyConfig config;
  VisualAngleConverter angleConverter;

  final int backgroundColor = 255;

  float pupilDiameter;
  float eyeWidth;
  float eyeHeight;
  float eyeDistance;

  PVector leftEyeCenter;
  PVector rightEyeCenter;

  EyeRenderer(StudyConfig config) {
    this.config = config;
    angleConverter = new VisualAngleConverter(config);

    eyeWidth = angleConverter.degToPxX(config.eyeWidthDeg);
    eyeHeight = angleConverter.degToPxY(config.eyeHeightDeg);
    eyeDistance = angleConverter.degToPxX(config.eyeDistanceDeg);
    pupilDiameter = angleConverter.degToPxX(config.pupilDiameterDeg);

    leftEyeCenter = new PVector(width / 2 - (eyeDistance / 2), height / 2);
    rightEyeCenter = new PVector(leftEyeCenter.x + eyeDistance, leftEyeCenter.y);
  }

  void clear() {
    background(backgroundColor);
  }

  void drawCenteredEyes() {
    drawEyes(leftEyeCenter.x, leftEyeCenter.y, rightEyeCenter.x, rightEyeCenter.y);
  }

  void drawEyes(float leftPupilX, float leftPupilY, float rightPupilX, float rightPupilY) {
    pushStyle();

    noFill();
    stroke(0);
    strokeWeight(config.eyeStrokeWeight);
    ellipse(leftEyeCenter.x, leftEyeCenter.y, eyeWidth, eyeHeight);
    ellipse(rightEyeCenter.x, rightEyeCenter.y, eyeWidth, eyeHeight);

    fill(0);
    circle(leftPupilX, leftPupilY, pupilDiameter);
    circle(rightPupilX, rightPupilY, pupilDiameter);

    popStyle();
  }

  void drawEyes(PVector leftPupil, PVector rightPupil) {
    drawEyes(leftPupil.x, leftPupil.y, rightPupil.x, rightPupil.y);
  }

  float getPupilDiameter() {
    return pupilDiameter;
  }

  float getEyeWidth() {
    return eyeWidth;
  }

  float getEyeHeight() {
    return eyeHeight;
  }

  float getEyeDistance() {
    return eyeDistance;
  }

  PVector getLeftEyeCenter() {
    return leftEyeCenter.copy();
  }

  PVector getRightEyeCenter() {
    return rightEyeCenter.copy();
  }
}
