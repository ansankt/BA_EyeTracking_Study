class EyeRenderer {
  final int backgroundColor = 255;

  final float pupilDiameter = 75;
  final float eyeWidth = 250;
  final float eyeHeight = 400;
  final float eyeDistance = 300;

  final PVector leftEyeCenter = new PVector(250, 400);
  final PVector rightEyeCenter = new PVector(leftEyeCenter.x + eyeDistance, leftEyeCenter.y);

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
    strokeWeight(4);
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

  PVector getLeftEyeCenter() {
    return leftEyeCenter.copy();
  }

  PVector getRightEyeCenter() {
    return rightEyeCenter.copy();
  }
}
