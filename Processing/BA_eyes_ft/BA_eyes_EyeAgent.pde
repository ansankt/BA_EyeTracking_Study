class EyeAgent {
  PVector leftPupil;
  PVector rightPupil;

  PVector leftTarget;
  PVector rightTarget;

  float movementSpeed = 3.0;
  float eyeDistance = 300;
  float targetRadiusX;
  float targetRadiusY;
  PVector leftEyeCenter;
  PVector rightEyeCenter;

  EyeAgent(PVector leftStart, PVector rightStart, float eyeWidth, float eyeHeight, float pupilDiameter) {
    leftPupil = leftStart.copy();
    rightPupil = rightStart.copy();

    leftTarget = leftStart.copy();
    rightTarget = rightStart.copy();

    eyeDistance = rightStart.x - leftStart.x;
    targetRadiusX = eyeWidth / 2 - pupilDiameter / 2;
    targetRadiusY = eyeHeight / 2 - pupilDiameter / 2;
    leftEyeCenter = leftStart.copy();
    rightEyeCenter = rightStart.copy();
  }

  void update() {
    leftPupil = moveTowards(leftPupil, leftTarget, movementSpeed);
    rightPupil = moveTowards(rightPupil, rightTarget, movementSpeed);
  }

  void setSharedTargetFromLeftEye(PVector newLeftTarget) {
    leftTarget = constrainTargetToEye(newLeftTarget, leftEyeCenter);
    rightTarget = new PVector(leftTarget.x + eyeDistance, leftTarget.y);
  }

  void setTargets(PVector newLeftTarget, PVector newRightTarget) {
    leftTarget = constrainTargetToEye(newLeftTarget, leftEyeCenter);
    rightTarget = constrainTargetToEye(newRightTarget, rightEyeCenter);
  }

  void setMovementSpeed(float newMovementSpeed) {
    movementSpeed = max(0.1, newMovementSpeed);
  }

  boolean hasReachedTarget() {
    return leftPupil.dist(leftTarget) < 0.5 && rightPupil.dist(rightTarget) < 0.5;
  }

  PVector getLeftPupilPosition() {
    return leftPupil.copy();
  }

  PVector getRightPupilPosition() {
    return rightPupil.copy();
  }

  PVector getLeftTarget() {
    return leftTarget.copy();
  }

  PVector getRightTarget() {
    return rightTarget.copy();
  }

  float getMovementSpeed() {
    return movementSpeed;
  }

  PVector moveTowards(PVector current, PVector target, float speed) {
    PVector direction = PVector.sub(target, current);
    float distance = direction.mag();

    if (distance <= speed || distance == 0) {
      return target.copy();
    }

    direction.normalize();
    direction.mult(speed);
    return PVector.add(current, direction);
  }

  PVector constrainTargetToEye(PVector target, PVector eyeCenter) {
    float dx = target.x - eyeCenter.x;
    float dy = target.y - eyeCenter.y;

    if (dx == 0 && dy == 0) {
      return eyeCenter.copy();
    }

    float ellipseValue = sq(dx) / sq(targetRadiusX) + sq(dy) / sq(targetRadiusY); //Point inside the ellipse

    if (ellipseValue <= 1) {
      return target.copy();
    }

    float scale = 1 / sqrt(ellipseValue); //calculate the ratio of the original target to the closest point on the edge of the ellipse
    return new PVector(
      eyeCenter.x + dx * scale,
      eyeCenter.y + dy * scale
    );
  }
}
