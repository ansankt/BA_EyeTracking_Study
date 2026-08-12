class TobiiGazeInput implements GazeInput {
  GazeTrack gazeTrack;
  PApplet parent;
  StudyConfig config;

  TobiiGazeInput(PApplet parent, StudyConfig config) {
    this.parent = parent;
    this.config = config;
    gazeTrack = new GazeTrack(parent);
  }

  GazeSample getCurrentSample() {
    boolean valid = gazeTrack.gazePresent();

    if (!valid) {
      return new GazeSample(0, 0, false, millis());
    }

    float rawX = gazeTrack.getGazeX();
    float rawY = gazeTrack.getGazeY();
    float localPhysicalX = rawX - config.tobiiScreenOriginXPx;
    float localPhysicalY = rawY - config.tobiiScreenOriginYPx;
    float processingX = localPhysicalX * parent.width / config.tobiiPhysicalScreenWidthPx;
    float processingY = localPhysicalY * parent.height / config.tobiiPhysicalScreenHeightPx;

    return new GazeSample(processingX, processingY, true, millis());
  }
}
