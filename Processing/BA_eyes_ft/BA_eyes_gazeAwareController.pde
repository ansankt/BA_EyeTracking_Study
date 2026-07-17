class GazeAwareController implements EyeController {
  EyeAgent eyeAgent;

  GazeAwareController(EyeAgent eyeAgent) {
    this.eyeAgent = eyeAgent;
  }

  void update() {
    // Placeholder: later this will read gaze data and set targets on the EyeAgent.
  }
}
