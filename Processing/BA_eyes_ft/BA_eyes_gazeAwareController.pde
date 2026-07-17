class GazeAwareController implements EyeController {
  EyeAgent eyeAgent;
  GazeInput gazeInput;

  GazeAwareController(EyeAgent eyeAgent, GazeInput gazeInput) {
    this.eyeAgent = eyeAgent;
    this.gazeInput = gazeInput;
  }

  void update() {
    GazeSample currentSample = gazeInput.getCurrentSample();

    if (!currentSample.valid) {
      return;
    }

    // Placeholder: later this will map gaze data to an eye target.
  }
}
