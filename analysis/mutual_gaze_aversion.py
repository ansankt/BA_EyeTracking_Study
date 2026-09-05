"""Strict, user-initiated aversions directly following classified mutual gaze."""

METRICS = (
    ("mutual_gaze_aversion_rate_per_second", "Mutual-gaze aversion: trial-time rate", "aversions/s"),
    ("mutual_gaze_aversion_rate_per_mutual_gaze_second", "Mutual-gaze aversion: exposure-time rate", "aversions/mutual-gaze s"),
    ("mean_mutual_gaze_aversion_duration_ms", "Mutual-gaze aversion: mean completed duration", "ms"),
)
TOTAL_FIELDS = (
    "mutual_gaze_aversion_count",
    "mutual_gaze_aversion_completed_count",
    "mutual_gaze_aversion_censored_count",
    "mutual_gaze_aversion_total_completed_duration_ms",
    "mutual_gaze_aversion_exposure_ms",
)
FIELDS = TOTAL_FIELDS + tuple(metric[0] for metric in METRICS)
EPISODE_FIELDS = (
    "participant_id", "trial_id", "condition", "start_timestamp_ms",
    "end_timestamp_ms", "initial_state", "completed", "end_reason",
    "observed_duration_ms", "duration_ms",
)


def summarize(totals, trial_duration_ms):
    result = dict(totals)
    count, completed, _, duration, exposure = (totals[key] for key in TOTAL_FIELDS)
    result[METRICS[0][0]] = round(count * 1000 / trial_duration_ms, 6) if trial_duration_ms > 0 else None
    result[METRICS[1][0]] = round(count * 1000 / exposure, 6) if exposure > 0 else None
    result[METRICS[2][0]] = round(duration / completed, 3) if completed > 0 else None
    return result


def analyze(rows):
    episodes = []
    active = None
    previous_state = None
    previous_time = None
    exposure = 0
    eyes = {"LOOKING_AT_EYES", "MUTUAL_GAZE"}
    away = {"LOOKING_AT_FACE", "LOOKING_AWAY"}

    def close(timestamp, reason):
        active.update(end_timestamp_ms=timestamp, end_reason=reason,
                      completed=reason == "return_to_eyes",
                      observed_duration_ms=timestamp - active["start_timestamp_ms"])
        active["duration_ms"] = active["observed_duration_ms"] if active["completed"] else None
        episodes.append(active)

    for row in rows:
        timestamp = row["timestamp_ms"]
        valid = str(row.get("gaze_valid", "true")).lower() in {"true", "1", "yes"}
        state = row["gaze_state"] if valid else "INVALID"
        # Samples define piecewise-constant intervals up to the next timestamp.
        if previous_state == "MUTUAL_GAZE":
            exposure += timestamp - previous_time
        if active is not None and state not in away:
            close(timestamp, "return_to_eyes" if state in eyes else "tracking_loss_or_unknown")
            active = None
        if previous_state == "MUTUAL_GAZE" and state in away:
            active = {key: row[key] for key in ("participant_id", "trial_id", "condition")}
            active.update(start_timestamp_ms=timestamp, initial_state=state)
        previous_state, previous_time = state, timestamp
    if active is not None:
        close(rows[-1]["timestamp_ms"], "trial_end")
    completed = [episode for episode in episodes if episode["completed"]]
    totals = dict(zip(TOTAL_FIELDS, (
        len(episodes), len(completed), len(episodes) - len(completed),
        sum(episode["duration_ms"] for episode in completed), exposure,
    )))
    duration = rows[-1]["timestamp_ms"] - rows[0]["timestamp_ms"] if rows else 0
    return summarize(totals, duration), episodes
