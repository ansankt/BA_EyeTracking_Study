class VisualAngleConverter {
  StudyConfig config;
  float pixelsPerCmX;
  float pixelsPerCmY;

  VisualAngleConverter(StudyConfig config) {
    this.config = config;
    pixelsPerCmX = width / config.screenWidthCm;
    pixelsPerCmY = height / config.screenHeightCm;
  }

  float degToPxX(float degrees) {
    return visualAngleToCm(degrees) * pixelsPerCmX;
  }

  float degToPxY(float degrees) {
    return visualAngleToCm(degrees) * pixelsPerCmY;
  }

  float visualAngleToCm(float degrees) {
    return 2.0 * config.viewingDistanceCm * tan(radians(degrees / 2.0));
  }
}
