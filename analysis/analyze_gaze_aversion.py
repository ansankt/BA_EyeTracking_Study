#!/usr/bin/env python3
import argparse
import csv
import statistics
from pathlib import Path


EYE_CONTACT_STATES = {"LOOKING_AT_EYES", "MUTUAL_GAZE"}
AVERSION_STATES = {"LOOKING_AT_FACE", "LOOKING_AWAY"}
MUTUAL_GAZE_AREA_COLUMN = "in_mutual_gaze_area"
AGENT_LOOKS_AT_USER_COLUMN = "agent_looks_at_user"


def read_samples(path):
    with open(path, newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    for row in rows:
        row["timestamp_ms"] = int(float(row["timestamp_ms"]))
        row["trial_time_ms"] = int(float(row["trial_time_ms"]))
        row["trial_id"] = int(row["trial_id"])
        row[MUTUAL_GAZE_AREA_COLUMN] = parse_optional_bool(row.get(MUTUAL_GAZE_AREA_COLUMN))
        row[AGENT_LOOKS_AT_USER_COLUMN] = parse_optional_bool(row.get(AGENT_LOOKS_AT_USER_COLUMN))

    return rows


def parse_optional_bool(value):
    if value is None or value == "":
        return None

    return str(value).strip().lower() in {"true", "1", "yes"}


def grouped_by_trial(rows):
    groups = {}

    for row in rows:
        key = (row["participant_id"], row["trial_id"], row["condition"])
        groups.setdefault(key, []).append(row)

    for key in groups:
        groups[key].sort(key=lambda row: row["timestamp_ms"])

    return groups


def state_category(gaze_state):
    if gaze_state in EYE_CONTACT_STATES:
        return "EYE_CONTACT"

    if gaze_state in AVERSION_STATES:
        return "AVERSION"

    return "OTHER"


def build_state_episodes(rows):
    if not rows:
        return []

    episodes = []
    current = new_episode(rows[0])

    for row in rows[1:]:
        if row["gaze_state"] == current["gaze_state"]:
            current["end_timestamp_ms"] = row["timestamp_ms"]
            current["end_trial_time_ms"] = row["trial_time_ms"]
            current["sample_count"] += 1
            current["in_mutual_gaze_area_sample_count"] += mutual_gaze_area_sample_value(row)
        else:
            close_episode(current, row)
            episodes.append(current)
            current = new_episode(row)

    close_episode(current, None)
    episodes.append(current)
    return episodes


def new_episode(row):
    return {
        "participant_id": row["participant_id"],
        "trial_id": row["trial_id"],
        "condition": row["condition"],
        "gaze_state": row["gaze_state"],
        "state_category": state_category(row["gaze_state"]),
        "start_timestamp_ms": row["timestamp_ms"],
        "end_timestamp_ms": row["timestamp_ms"],
        "start_trial_time_ms": row["trial_time_ms"],
        "end_trial_time_ms": row["trial_time_ms"],
        "sample_count": 1,
        "in_mutual_gaze_area_sample_count": mutual_gaze_area_sample_value(row),
    }


def close_episode(episode, next_row):
    if next_row is not None:
        episode["end_timestamp_ms"] = next_row["timestamp_ms"]
        episode["end_trial_time_ms"] = next_row["trial_time_ms"]

    episode["duration_ms"] = max(
        0,
        episode["end_timestamp_ms"] - episode["start_timestamp_ms"],
    )
    episode["in_mutual_gaze_area_ratio"] = (
        episode["in_mutual_gaze_area_sample_count"] / episode["sample_count"]
        if episode["sample_count"] > 0
        else 0
    )


def mutual_gaze_area_sample_value(row):
    return 1 if row.get(MUTUAL_GAZE_AREA_COLUMN) is True else 0


def build_category_episodes(state_episodes):
    if not state_episodes:
        return []

    category_episodes = []
    current = new_category_episode(state_episodes[0])

    for episode in state_episodes[1:]:
        if episode["state_category"] == current["state_category"]:
            current["end_timestamp_ms"] = episode["end_timestamp_ms"]
            current["end_trial_time_ms"] = episode["end_trial_time_ms"]
            current["states"].append(episode["gaze_state"])
            current["sample_count"] += episode["sample_count"]
        else:
            close_category_episode(current)
            category_episodes.append(current)
            current = new_category_episode(episode)

    close_category_episode(current)
    category_episodes.append(current)
    return category_episodes


def new_category_episode(episode):
    return {
        "participant_id": episode["participant_id"],
        "trial_id": episode["trial_id"],
        "condition": episode["condition"],
        "state_category": episode["state_category"],
        "start_timestamp_ms": episode["start_timestamp_ms"],
        "end_timestamp_ms": episode["end_timestamp_ms"],
        "start_trial_time_ms": episode["start_trial_time_ms"],
        "end_trial_time_ms": episode["end_trial_time_ms"],
        "states": [episode["gaze_state"]],
        "sample_count": episode["sample_count"],
    }


def close_category_episode(episode):
    episode["duration_ms"] = max(
        0,
        episode["end_timestamp_ms"] - episode["start_timestamp_ms"],
    )


def mean(values):
    return statistics.mean(values) if values else 0


def median(values):
    return statistics.median(values) if values else 0


def mean_or_none(values):
    return statistics.mean(values) if values else None


def median_or_none(values):
    return statistics.median(values) if values else None


def analyze_trial(participant_id, trial_id, condition, trial_rows, state_episodes):
    category_episodes = build_category_episodes(state_episodes)
    trial_duration_ms = 0

    if category_episodes:
      trial_duration_ms = category_episodes[-1]["end_timestamp_ms"] - category_episodes[0]["start_timestamp_ms"]

    aversions = []

    for index, episode in enumerate(category_episodes):
        if episode["state_category"] != "AVERSION" or index == 0:
            continue

        previous_episode = category_episodes[index - 1]

        if previous_episode["state_category"] != "EYE_CONTACT":
            continue

        next_eye_contact = None
        for later_episode in category_episodes[index + 1:]:
            if later_episode["state_category"] == "EYE_CONTACT":
                next_eye_contact = later_episode
                break

            if later_episode["state_category"] == "OTHER":
                break

        aversions.append({
            "aversion_duration_ms": episode["duration_ms"],
            "eye_contact_before_aversion_ms": previous_episode["duration_ms"],
            "returned_to_eyes": next_eye_contact is not None,
            "return_to_eyes_latency_ms": (
                next_eye_contact["start_timestamp_ms"] - episode["start_timestamp_ms"]
                if next_eye_contact is not None
                else 0
            ),
            "first_aversion_state": episode["states"][0],
            "aversion_after_mutual_gaze": "MUTUAL_GAZE" in previous_episode["states"],
            "time_from_mutual_gaze_to_aversion_ms": time_from_mutual_to_aversion(
                state_episodes,
                previous_episode,
                episode,
            ),
        })

    aversion_durations = [item["aversion_duration_ms"] for item in aversions]
    eye_contact_before = [item["eye_contact_before_aversion_ms"] for item in aversions]
    return_latencies = [
        item["return_to_eyes_latency_ms"]
        for item in aversions
        if item["returned_to_eyes"]
    ]
    mutual_to_aversion = [
        item["time_from_mutual_gaze_to_aversion_ms"]
        for item in aversions
        if item["time_from_mutual_gaze_to_aversion_ms"] > 0
    ]

    aversion_count = len(aversions)
    trial_duration_min = trial_duration_ms / 60000 if trial_duration_ms > 0 else 0
    return_to_eyes_count = sum(1 for item in aversions if item["returned_to_eyes"])
    mutual_area_metrics = analyze_mutual_gaze_area(trial_rows, trial_duration_ms)

    return {
        "participant_id": participant_id,
        "trial_id": trial_id,
        "condition": condition,
        "trial_duration_ms": round(trial_duration_ms, 3),
        "gaze_aversion_count": aversion_count,
        "gaze_aversion_rate_per_minute": round(aversion_count / trial_duration_min, 6) if trial_duration_min > 0 else 0,
        "mean_eye_contact_before_aversion_ms": round(mean_or_none(eye_contact_before), 3) if eye_contact_before else None,
        "median_eye_contact_before_aversion_ms": round(median_or_none(eye_contact_before), 3) if eye_contact_before else None,
        "mean_aversion_duration_ms": round(mean_or_none(aversion_durations), 3) if aversion_durations else None,
        "median_aversion_duration_ms": round(median_or_none(aversion_durations), 3) if aversion_durations else None,
        "total_aversion_duration_ms": round(sum(aversion_durations), 3),
        "return_to_eyes_count": return_to_eyes_count,
        "return_to_eyes_rate": round(return_to_eyes_count / aversion_count, 6) if aversion_count > 0 else 0,
        "mean_return_to_eyes_latency_ms": round(mean_or_none(return_latencies), 3) if return_latencies else None,
        "face_aversion_count": sum(1 for item in aversions if item["first_aversion_state"] == "LOOKING_AT_FACE"),
        "away_aversion_count": sum(1 for item in aversions if item["first_aversion_state"] == "LOOKING_AWAY"),
        "aversion_after_mutual_gaze_count": sum(1 for item in aversions if item["aversion_after_mutual_gaze"]),
        "mean_time_from_mutual_gaze_to_aversion_ms": round(mean_or_none(mutual_to_aversion), 3) if mutual_to_aversion else None,
        **mutual_area_metrics,
    }


def trial_duration_ms(rows):
    if len(rows) < 2:
        return 0

    return max(0, rows[-1]["timestamp_ms"] - rows[0]["timestamp_ms"])


def build_boolean_episodes(rows, interaction_name, predicate):
    episodes = []
    current = None

    for row in rows:
        if predicate(row):
            if current is None:
                current = {
                    "participant_id": row["participant_id"],
                    "trial_id": row["trial_id"],
                    "condition": row["condition"],
                    "interaction": interaction_name,
                    "start_timestamp_ms": row["timestamp_ms"],
                    "end_timestamp_ms": row["timestamp_ms"],
                    "sample_count": 1,
                }
            else:
                current["end_timestamp_ms"] = row["timestamp_ms"]
                current["sample_count"] += 1
        elif current is not None:
            current["end_timestamp_ms"] = row["timestamp_ms"]
            close_boolean_episode(current)
            episodes.append(current)
            current = None

    if current is not None:
        close_boolean_episode(current)
        episodes.append(current)

    return episodes


def close_boolean_episode(episode):
    episode["duration_ms"] = max(
        0,
        episode["end_timestamp_ms"] - episode["start_timestamp_ms"],
    )


def interaction_metrics(interaction_name, episodes, duration_ms):
    episode_count = len(episodes)
    total_episode_duration_ms = sum(episode["duration_ms"] for episode in episodes)
    trial_duration_min = duration_ms / 60000 if duration_ms > 0 else 0

    return {
        f"{interaction_name}_proportion_time": round(
            total_episode_duration_ms / duration_ms, 6,
        ) if duration_ms > 0 else 0,
        f"{interaction_name}_mean_episode_duration_ms": round(
            mean([episode["duration_ms"] for episode in episodes]), 3,
        ),
        f"{interaction_name}_episode_rate_per_minute": round(
            episode_count / trial_duration_min, 6,
        ) if trial_duration_min > 0 else 0,
        f"{interaction_name}_episode_count": episode_count,
        f"{interaction_name}_total_episode_duration_ms": round(total_episode_duration_ms, 3),
    }


def empty_interaction_metrics(interaction_name):
    return {
        f"{interaction_name}_proportion_time": None,
        f"{interaction_name}_mean_episode_duration_ms": None,
        f"{interaction_name}_episode_rate_per_minute": None,
        f"{interaction_name}_episode_count": None,
        f"{interaction_name}_total_episode_duration_ms": None,
    }


def analyze_interactions(participant_id, trial_id, condition, rows):
    duration_ms = trial_duration_ms(rows)
    user_looks_at_avatar = build_boolean_episodes(
        rows,
        "user_looks_at_avatar",
        lambda row: row.get(MUTUAL_GAZE_AREA_COLUMN) is True,
    )
    has_agent_look_column = any(
        row.get(AGENT_LOOKS_AT_USER_COLUMN) is not None for row in rows
    )

    result = {
        "participant_id": participant_id,
        "trial_id": trial_id,
        "condition": condition,
        "trial_duration_ms": round(duration_ms, 3),
        "has_agent_looks_at_user_column": has_agent_look_column,
        **interaction_metrics("user_looks_at_avatar", user_looks_at_avatar, duration_ms),
    }

    if not has_agent_look_column:
        result.update(empty_interaction_metrics("avatar_looks_at_user"))
        result.update(empty_interaction_metrics("mutual_gaze"))
        return result, user_looks_at_avatar

    avatar_looks_at_user = build_boolean_episodes(
        rows,
        "avatar_looks_at_user",
        lambda row: row.get(AGENT_LOOKS_AT_USER_COLUMN) is True,
    )
    mutual_gaze = build_boolean_episodes(
        rows,
        "mutual_gaze",
        lambda row: row.get(MUTUAL_GAZE_AREA_COLUMN) is True
        and row.get(AGENT_LOOKS_AT_USER_COLUMN) is True,
    )
    result.update(interaction_metrics("avatar_looks_at_user", avatar_looks_at_user, duration_ms))
    result.update(interaction_metrics("mutual_gaze", mutual_gaze, duration_ms))
    return result, user_looks_at_avatar + avatar_looks_at_user + mutual_gaze


def analyze_mutual_gaze_area(rows, trial_duration_ms):
    has_column = any(row.get(MUTUAL_GAZE_AREA_COLUMN) is not None for row in rows)

    if not has_column:
        return {
            "has_mutual_gaze_area_column": False,
            "mutual_gaze_area_sample_count": 0,
            "mutual_gaze_area_sample_ratio": 0,
            "mutual_gaze_area_duration_ms": 0,
            "mutual_gaze_area_duration_ratio": 0,
            "mutual_gaze_area_entry_count": 0,
        }

    sample_count = len(rows)
    area_sample_count = sum(1 for row in rows if row.get(MUTUAL_GAZE_AREA_COLUMN) is True)
    area_duration_ms = 0
    entry_count = 0
    was_inside = False

    for index, row in enumerate(rows):
        is_inside = row.get(MUTUAL_GAZE_AREA_COLUMN) is True

        if is_inside and not was_inside:
            entry_count += 1

        if index < len(rows) - 1 and is_inside:
            area_duration_ms += max(0, rows[index + 1]["timestamp_ms"] - row["timestamp_ms"])

        was_inside = is_inside

    return {
        "has_mutual_gaze_area_column": True,
        "mutual_gaze_area_sample_count": area_sample_count,
        "mutual_gaze_area_sample_ratio": round(area_sample_count / sample_count, 6) if sample_count > 0 else 0,
        "mutual_gaze_area_duration_ms": round(area_duration_ms, 3),
        "mutual_gaze_area_duration_ratio": round(area_duration_ms / trial_duration_ms, 6) if trial_duration_ms > 0 else 0,
        "mutual_gaze_area_entry_count": entry_count,
    }


def time_from_mutual_to_aversion(state_episodes, eye_contact_episode, aversion_episode):
    mutual_starts = [
        episode["start_timestamp_ms"]
        for episode in state_episodes
        if episode["gaze_state"] == "MUTUAL_GAZE"
        and episode["start_timestamp_ms"] >= eye_contact_episode["start_timestamp_ms"]
        and episode["end_timestamp_ms"] <= eye_contact_episode["end_timestamp_ms"]
    ]

    if not mutual_starts:
        return 0

    return aversion_episode["start_timestamp_ms"] - mutual_starts[-1]


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Analyze gaze aversion metrics from samples.csv.")
    parser.add_argument("samples_csv", help="Path to a *_samples.csv file.")
    parser.add_argument("--out-dir", default=None, help="Output directory. Defaults to the samples file directory.")
    args = parser.parse_args()

    samples_path = Path(args.samples_csv)
    out_dir = Path(args.out_dir) if args.out_dir else samples_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = read_samples(samples_path)
    groups = grouped_by_trial(rows)

    all_state_episodes = []
    all_interaction_episodes = []
    metric_rows = []
    interaction_metric_rows = []

    for (participant_id, trial_id, condition), trial_rows in sorted(groups.items(), key=lambda item: item[0]):
        state_episodes = build_state_episodes(trial_rows)
        all_state_episodes.extend(state_episodes)
        metric_rows.append(analyze_trial(participant_id, trial_id, condition, trial_rows, state_episodes))
        interaction_row, interaction_episodes = analyze_interactions(
            participant_id,
            trial_id,
            condition,
            trial_rows,
        )
        interaction_metric_rows.append(interaction_row)
        all_interaction_episodes.extend(interaction_episodes)

    base_name = samples_path.stem.replace("_samples", "")
    episodes_path = out_dir / f"{base_name}_state_episodes.csv"
    metrics_path = out_dir / f"{base_name}_gaze_aversion_metrics.csv"
    interaction_episodes_path = out_dir / f"{base_name}_interaction_episodes.csv"
    interaction_metrics_path = out_dir / f"{base_name}_interaction_metrics.csv"

    episode_fields = [
        "participant_id",
        "trial_id",
        "condition",
        "gaze_state",
        "state_category",
        "start_timestamp_ms",
        "end_timestamp_ms",
        "start_trial_time_ms",
        "end_trial_time_ms",
        "duration_ms",
        "sample_count",
        "in_mutual_gaze_area_sample_count",
        "in_mutual_gaze_area_ratio",
    ]

    metric_fields = [
        "participant_id",
        "trial_id",
        "condition",
        "trial_duration_ms",
        "gaze_aversion_count",
        "gaze_aversion_rate_per_minute",
        "mean_eye_contact_before_aversion_ms",
        "median_eye_contact_before_aversion_ms",
        "mean_aversion_duration_ms",
        "median_aversion_duration_ms",
        "total_aversion_duration_ms",
        "return_to_eyes_count",
        "return_to_eyes_rate",
        "mean_return_to_eyes_latency_ms",
        "face_aversion_count",
        "away_aversion_count",
        "aversion_after_mutual_gaze_count",
        "mean_time_from_mutual_gaze_to_aversion_ms",
        "has_mutual_gaze_area_column",
        "mutual_gaze_area_sample_count",
        "mutual_gaze_area_sample_ratio",
        "mutual_gaze_area_duration_ms",
        "mutual_gaze_area_duration_ratio",
        "mutual_gaze_area_entry_count",
    ]

    interaction_episode_fields = [
        "participant_id",
        "trial_id",
        "condition",
        "interaction",
        "start_timestamp_ms",
        "end_timestamp_ms",
        "duration_ms",
        "sample_count",
    ]

    interaction_metric_fields = [
        "participant_id",
        "trial_id",
        "condition",
        "trial_duration_ms",
        "has_agent_looks_at_user_column",
    ]
    for interaction_name in ["user_looks_at_avatar", "avatar_looks_at_user", "mutual_gaze"]:
        interaction_metric_fields.extend([
            f"{interaction_name}_proportion_time",
            f"{interaction_name}_mean_episode_duration_ms",
            f"{interaction_name}_episode_rate_per_minute",
            f"{interaction_name}_episode_count",
            f"{interaction_name}_total_episode_duration_ms",
        ])

    write_csv(episodes_path, all_state_episodes, episode_fields)
    write_csv(metrics_path, metric_rows, metric_fields)
    write_csv(interaction_episodes_path, all_interaction_episodes, interaction_episode_fields)
    write_csv(interaction_metrics_path, interaction_metric_rows, interaction_metric_fields)

    print(f"Wrote {episodes_path}")
    print(f"Wrote {metrics_path}")
    print(f"Wrote {interaction_episodes_path}")
    print(f"Wrote {interaction_metrics_path}")

    if any(not row["has_agent_looks_at_user_column"] for row in interaction_metric_rows):
        print("Warning: agent_looks_at_user is missing in this samples file; avatar and mutual-gaze metrics are blank.")

    for row in metric_rows:
        print(
            f"{row['participant_id']} trial {row['trial_id']} {row['condition']}: "
            f"{row['gaze_aversion_count']} aversions, "
            f"mean duration {row['mean_aversion_duration_ms']} ms, "
            f"return rate {row['return_to_eyes_rate']}"
        )


if __name__ == "__main__":
    main()
