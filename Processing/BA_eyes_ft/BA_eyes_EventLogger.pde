class EventLogger {
  PrintWriter eventWriter;
  PrintWriter sampleWriter;

  String participantId = "P_TEST";
  int trialId = 0;
  String condition = "TEST";
  int trialStartTime = 0;

  EventLogger() {
    java.io.File dataDirectory = new java.io.File(sketchPath("data"));
    dataDirectory.mkdirs();

    eventWriter = createWriter(dataDirectory.getAbsolutePath() + "/events.csv");
    sampleWriter = createWriter(dataDirectory.getAbsolutePath() + "/samples.csv");

    eventWriter.println("timestamp_ms,trial_time_ms,participant_id,trial_id,condition,event_type,gaze_region,gaze_state,details");
    sampleWriter.println("timestamp_ms,trial_time_ms,participant_id,trial_id,condition,gaze_x,gaze_y,gaze_valid,gaze_region,gaze_state,left_pupil_x,left_pupil_y,right_pupil_x,right_pupil_y");

    flush();
  }

  void setContext(String participantId, int trialId, String condition) {
    this.participantId = participantId;
    this.trialId = trialId;
    this.condition = condition;
    trialStartTime = millis();
  }

  void setCondition(String condition) {
    this.condition = condition;
  }

  void startTrial(int trialId, String condition) {
    this.trialId = trialId;
    this.condition = condition;
    trialStartTime = millis();
  }

  void logEvent(String eventType, GazeRegion region, GazeState state, String details) {
    eventWriter.println(
      millis() + ","
      + trialTime() + ","
      + csv(participantId) + ","
      + trialId + ","
      + csv(condition) + ","
      + csv(eventType) + ","
      + csv(value(region)) + ","
      + csv(value(state)) + ","
      + csv(details)
    );
    eventWriter.flush();
  }

  void logSample(GazeSample sample, GazeRegion region, GazeState state, EyeAgent eyeAgent) {
    PVector leftPupil = eyeAgent.getLeftPupilPosition();
    PVector rightPupil = eyeAgent.getRightPupilPosition();

    float gazeX = sample != null ? sample.x : 0;
    float gazeY = sample != null ? sample.y : 0;
    boolean gazeValid = sample != null && sample.valid;

    sampleWriter.println(
      millis() + ","
      + trialTime() + ","
      + csv(participantId) + ","
      + trialId + ","
      + csv(condition) + ","
      + gazeX + ","
      + gazeY + ","
      + gazeValid + ","
      + csv(value(region)) + ","
      + csv(value(state)) + ","
      + leftPupil.x + ","
      + leftPupil.y + ","
      + rightPupil.x + ","
      + rightPupil.y
    );
  }

  void flush() {
    eventWriter.flush();
    sampleWriter.flush();
  }

  void close() {
    flush();
    eventWriter.close();
    sampleWriter.close();
  }

  int trialTime() {
    return millis() - trialStartTime;
  }

  String csv(String value) {
    if (value == null) {
      return "";
    }

    String escapedValue = value.replace("\"", "\"\"");

    if (escapedValue.indexOf(",") >= 0 || escapedValue.indexOf("\"") >= 0 || escapedValue.indexOf("\n") >= 0) {
      return "\"" + escapedValue + "\"";
    }

    return escapedValue;
  }

  String value(Object object) {
    if (object == null) {
      return "";
    }

    return object.toString();
  }
}
