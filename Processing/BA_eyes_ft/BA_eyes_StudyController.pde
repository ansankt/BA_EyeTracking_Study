EyeRenderer eyeRenderer;
EyeAgent eyeAgent;

EyeController activeEyeController;
IdleMovementController idleMovementController;
GazeAwareController gazeAwareController;

void setup() {
  //size(800, 800);
  fullScreen();
  eyeRenderer = new EyeRenderer();
  eyeAgent = new EyeAgent(
    eyeRenderer.getLeftEyeCenter(),
    eyeRenderer.getRightEyeCenter(),
    eyeRenderer.getEyeWidth(),
    eyeRenderer.getEyeHeight(),
    eyeRenderer.getPupilDiameter()
  );
  
  idleMovementController = new IdleMovementController(eyeAgent);
  gazeAwareController = new GazeAwareController(eyeAgent);

  activeEyeController = idleMovementController;
}

void draw() {
  activeEyeController.update();
  eyeAgent.update();

  eyeRenderer.clear();
  eyeRenderer.drawEyes(
    eyeAgent.getLeftPupilPosition(),
    eyeAgent.getRightPupilPosition()
  );
}
