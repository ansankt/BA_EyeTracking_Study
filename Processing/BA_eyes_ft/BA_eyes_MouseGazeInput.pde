class MouseGazeInput implements GazeInput {
  GazeSample getCurrentSample() {
    return new GazeSample(mouseX, mouseY, true, millis());
  }
}
