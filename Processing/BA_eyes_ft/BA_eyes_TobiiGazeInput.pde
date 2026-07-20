class TobiiGazeInput implements GazeInput {
  GazeTrack gazeTrack;

  TobiiGazeInput(PApplet parent) {
    gazeTrack = new GazeTrack(parent);
  }

  GazeSample getCurrentSample() {
    boolean valid = gazeTrack.gazePresent();

    if (!valid) {
      return new GazeSample(0, 0, false, millis());
    }

    return new GazeSample(gazeTrack.getGazeX(), gazeTrack.getGazeY(), true, millis());
  }
}
