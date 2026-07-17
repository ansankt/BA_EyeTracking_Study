EyeRenderer eyeRenderer;
EyeAgent eyeAgent;
GazeInput gazeInput;

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
  gazeInput = new MouseGazeInput();

  idleMovementController = new IdleMovementController(eyeAgent);
  gazeAwareController = new GazeAwareController(eyeAgent, gazeInput);

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
