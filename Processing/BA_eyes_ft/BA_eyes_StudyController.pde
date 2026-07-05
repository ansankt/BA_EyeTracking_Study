EyeRenderer eyeRenderer;
EyeAgent eyeAgent;

void setup() {
  size(800, 800);
  eyeRenderer = new EyeRenderer();
  eyeAgent = new EyeAgent(eyeRenderer.getLeftEyeCenter(), eyeRenderer.getRightEyeCenter());
}

void draw() {
  eyeAgent.update();

  eyeRenderer.clear();
  eyeRenderer.drawEyes(
    eyeAgent.getLeftPupilPosition(),
    eyeAgent.getRightPupilPosition()
  );
}
