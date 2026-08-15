# BA Eye-Tracking Study

Processing software for a Bachelor thesis on gaze behavior in response to simple animated eyes. The study compares a non-reactive eye model with a gaze-aware model that responds to the participant's gaze.

## Study Design

| Condition | Behavior |
| --- | --- |
| `GAZE_UNAWARE` | Autonomous, saccade-like idle movements. The eyes do not react to the participant. |
| `GAZE_AWARE` | A finite-state model switches between random gaze, mutual gaze, and gaze break. |

The condition order is counterbalanced from the numeric participant ID: even IDs start with `GAZE_AWARE`, odd IDs start with `GAZE_UNAWARE`.

## Requirements

- [Processing](https://processing.org/) with Java mode
- Processing Sound Library for audio playback and microphone input
- Python 3 for data analysis
- [GazeTrack](https://github.com/AugustoEst/gazetrack) for the Tobii 4C workflow

The sketch is opened through `Processing/BA_eyes_ft/BA_eyes_ft.pde`. `gazetrack.*` is imported by the sketch, so GazeTrack must be installed even when testing with mouse input.

### Tobii 4C

The real study is intended for Windows with a calibrated Tobii 4C. Start the GazeTrack companion application `TobiiStream.exe` before starting the Processing sketch.

The input mode is configured in `Processing/BA_eyes_ft/BA_eyes_StudyConfig.pde`:

```java
String gazeInputMode = "MOUSE"; // Development and macOS testing
// String gazeInputMode = "TOBII"; // Windows study setup
```

## Running the Study

1. Set `participantId`, input mode, display values, and other settings in `BA_eyes_StudyConfig.pde`.
2. Start the sketch in Processing.
3. Press `SPACE` to start. If microphone answers are enabled, a short silence calibration runs first.
4. Each trial contains a randomized subset of audio questions.
5. With microphone answers enabled, a response is completed after speech has been detected followed by the configured silence duration. `ENTER` and left mouse click remain manual fallbacks.
6. After a trial, complete the external questionnaire and press `SPACE` to start the next condition.

### Keyboard Controls

| Control | Action |
| --- | --- |
| `SPACE` | Start from the intro or continue after a break |
| `ENTER` or left mouse click | Start/complete a question manually |
| `D` | Toggle debug mode |
| `1` | Switch to `GAZE_UNAWARE` in debug mode |
| `2` | Switch to `GAZE_AWARE` in debug mode |

## Gaze-Aware Model

```text
RANDOM_GAZE
  [participant looks in mutual-gaze area for >= 300 ms]
  -> MUTUAL_GAZE

MUTUAL_GAZE
  [participant leaves area for >= 200 ms]
  -> RANDOM_GAZE
  [mutual gaze lasts >= 3600 ms]
  -> GAZE_BREAK

GAZE_BREAK
  [participant leaves area for >= 200 ms]
  -> RANDOM_GAZE
  [break lasts >= 1250 ms and participant looks in area]
  -> MUTUAL_GAZE
```

The logged `MUTUAL_GAZE` state requires both conditions below:

1. The participant's gaze is inside the configured mutual-gaze area.
2. The avatar is looking at the participant, operationalized as pupils close to the eye centers.

## Architecture

| Component | Responsibility |
| --- | --- |
| `StudyController` | Study flow, trials, conditions, rendering order, debug mode, and logging context |
| `StudyConfig` | Central configuration for the study, display, Tobii, microphone, and eye behavior |
| `GazeInput` | Common input interface |
| `MouseGazeInput` | Uses mouse coordinates as gaze data |
| `TobiiGazeInput` | Reads GazeTrack data and maps it to Processing coordinates |
| `GazeMapper` | Maps samples to eye, face, outside, and mutual-gaze regions |
| `GazeClassifier` | Produces stable gaze states and determines whether the avatar looks at the participant |
| `EyeAgent` | Stores pupil positions, targets, movement speed, and eye-boundary constraints |
| `EyeRenderer` | Draws the eye ellipses and pupils |
| `IdleMovementController` | Controls the autonomous saccade-like idle movement |
| `GazeAwareController` | Implements the gaze-aware finite-state model |
| `QuestionController` | Plays question audio and manages answer phases |
| `MicrophoneAnswerController` | Calibrates noise and detects the end of spoken answers |
| `EventLogger` | Writes event and gaze-sample CSV files |

## Core Configuration

All values are located in `Processing/BA_eyes_ft/BA_eyes_StudyConfig.pde`.

| Area | Important values |
| --- | --- |
| Participant and debug | `participantId`, `debugMode` |
| Trials | `questionsPerTrial`, `totalQuestionCount` |
| Input | `gazeInputMode`, Tobii display resolution and desktop origin |
| Visual angles | `screenWidthCm`, `screenHeightCm`, `viewingDistanceCm` |
| Eyes | `eyeWidthDeg = 4.0`, `eyeHeightDeg = 6.0`, `eyeDistanceDeg = 4.5`, `pupilDiameterDeg = 1.0` |
| Mutual gaze | `mutualGazeAreaWidthDeg = 8.0`, `mutualGazeAreaHeightDeg = 5.0`, `agentLooksAtUserToleranceDeg = 0.5` |
| Gaze-aware timing | `lookingAtEyesToMutualGazeMs`, `lostGazeToRandomMs`, `maxMutualGazeDurationMs`, `gazeBreakDurationMs` |
| Idle behavior | `idleMovementPattern`, saccade interval, radius, and speed |
| Microphone | calibration duration, lockout, silence duration, input device, and gain |

Eye and mutual-gaze dimensions are configured in degrees of visual angle. `VisualAngleConverter` converts them to Processing pixels using the entered physical display dimensions and viewing distance.

### Tobii Coordinate Transformation

At 125% Windows display scaling, Tobii can supply physical monitor pixels while Processing uses logical pixels. `TobiiGazeInput` transforms the raw sample before it becomes a `GazeSample`:

```text
processingX = (tobiiX - screenOriginX) * processingWidth / physicalScreenWidth
processingY = (tobiiY - screenOriginY) * processingHeight / physicalScreenHeight
```

Set the physical resolution of the study monitor and, when necessary, its global desktop origin:

```java
int tobiiPhysicalScreenWidthPx = 1920;
int tobiiPhysicalScreenHeightPx = 1080;
int tobiiScreenOriginXPx = 0;
int tobiiScreenOriginYPx = 0;
```

For a primary single monitor, both origins remain `0`. The red Tobii trace in debug mode must match the participant's visible gaze position before a real run.

### Optional Background Image

`BA_eyes_StudyController.pde` contains this switch:

```java
boolean showParticipantBackgroundImage = true;
```

Set it to `false` to use a white background instead. If the image file is absent, the sketch also falls back to white.

## Audio and Microphone

Question audio files are stored in `Processing/BA_eyes_ft/questions/` and are named `question_1.mp3` through `question_10.mp3` by default.

With microphone answer advance enabled, the software:

1. Calibrates silence before the first trial.
2. Plays the question audio.
3. Waits for the configured answer lockout.
4. Detects speech over the calibrated threshold.
5. Starts the next question once the configured silence duration has elapsed.

A visible warning and a `MIC_SIGNAL_WARNING` event are created if no valid microphone signal is detected during calibration.

## Data Logging

Every sketch run creates two files in `Processing/BA_eyes_ft/data/`:

```text
<participant>_<session>_events.csv
<participant>_<session>_samples.csv
```

`events.csv` records study and trial events, question events, mode changes, gaze-state changes, and microphone calibration information.

```text
timestamp_ms, trial_time_ms, participant_id, trial_id, condition,
event_type, gaze_region, gaze_state, question_id,
question_order_in_trial, details
```

`samples.csv` is written during active trials at the configured sample interval:

```text
timestamp_ms, trial_time_ms, participant_id, trial_id, condition,
gaze_x, gaze_y, gaze_valid, gaze_region, gaze_state,
in_mutual_gaze_area, agent_looks_at_user,
left_pupil_x, left_pupil_y, right_pupil_x, right_pupil_y
```

For Tobii input, `gaze_x` and `gaze_y` are already transformed Processing coordinates.

## Analysis Workflow

The Python analysis uses current `*_samples.csv` files. A shorter reference is available in [analysis/README.md](analysis/README.md).

### 1. Analyze Each Recording

```bash
python3 analysis/analyze_gaze_aversion.py \
  Processing/BA_eyes_ft/data/P01_20260815_120000_samples.csv \
  --out-dir analysis/individual_results
```

The script creates:

- `*_state_episodes.csv`
- `*_interaction_episodes.csv`
- `*_gaze_aversion_metrics.csv`
- `*_interaction_metrics.csv`

Interaction definitions:

| Metric | Definition |
| --- | --- |
| `user_looks_at_avatar` | Gaze is inside the mutual-gaze area |
| `avatar_looks_at_user` | Pupils are within the configured center tolerance |
| `mutual_gaze` | Both conditions hold at the same time |

A gaze aversion is an episode of `LOOKING_AT_FACE` or `LOOKING_AWAY` immediately following eye contact.

### 2. Aggregate the Study

After all individual results are stored in the same folder:

```bash
python3 analysis/aggregate_study_results.py \
  analysis/individual_results \
  --out-dir analysis/study_results
```

The script creates:

- `participant_condition_metrics.csv`: metrics per participant and model
- `condition_summary.csv`: model means and standard deviations
- `paired_condition_tests.csv`: paired permutation tests, Cohen's dz, and Holm-corrected p-values
- `figures/`: grouped bar charts for interaction metrics and bar charts plus boxplots for gaze aversion metrics

The bar charts show mean and standard deviation. The gaze-aversion boxplots show the median, interquartile range, whiskers, and individual participant values.

### Batch Analysis

```bash
for file in Processing/BA_eyes_ft/data/*_samples.csv; do
  python3 analysis/analyze_gaze_aversion.py "$file" --out-dir analysis/individual_results
done
```

Run the aggregation command afterwards. `analysis/example_individual_results/` contains synthetic test data and must not be mixed with real study results.

## Repository Layout

```text
BA_EyeTracking_Study/
├── Processing/
│   └── BA_eyes_ft/
│       ├── BA_eyes_ft.pde                 # Processing entry point
│       ├── BA_eyes_StudyController.pde    # study flow and rendering
│       ├── BA_eyes_StudyConfig.pde        # central settings
│       ├── BA_eyes_*.pde                  # input, eyes, audio, and logging components
│       ├── data/                          # generated raw data
│       ├── picture/background.png         # optional background image
│       └── questions/                     # question audio files
├── analysis/
│   ├── analyze_gaze_aversion.py           # individual recording analysis
│   ├── aggregate_study_results.py         # aggregation, tests, and figures
│   ├── example_individual_results/        # synthetic test data
│   ├── individual_results/                # per-session analysis results
│   └── study_results/                     # study-level results and figures
└── README.md
```

## Pre-Run Checklist

1. Set a unique `participantId`.
2. Enter the actual monitor size in centimeters and the viewing distance.
3. For Tobii, verify physical monitor resolution, display origin, calibration, and the debug gaze trace.
4. Test microphone calibration and spoken-answer detection.
5. Confirm that question audio files are present.
6. Set `debugMode = false` for the real study.
7. Keep pilot/test data separate from the real participant dataset.
