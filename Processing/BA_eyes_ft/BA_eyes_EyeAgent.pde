class EyeAgent {
  PVector leftPupil;
  PVector rightPupil;

  PVector leftTarget;
  PVector rightTarget;

  float movementSpeed = 3.0;
  float eyeDistance = 300;

  EyeAgent(PVector leftStart, PVector rightStart) {
    leftPupil = leftStart.copy();
    rightPupil = rightStart.copy();

    leftTarget = leftStart.copy();
    rightTarget = rightStart.copy();

    eyeDistance = rightStart.x - leftStart.x;
  }

  void update() {
    leftPupil = moveTowards(leftPupil, leftTarget, movementSpeed);
    rightPupil = moveTowards(rightPupil, rightTarget, movementSpeed);
  }

  void setSharedTargetFromLeftEye(PVector newLeftTarget) {
    leftTarget = newLeftTarget.copy();
    rightTarget = new PVector(newLeftTarget.x + eyeDistance, newLeftTarget.y);
  }

  void setTargets(PVector newLeftTarget, PVector newRightTarget) {
    leftTarget = newLeftTarget.copy();
    rightTarget = newRightTarget.copy();
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
}
