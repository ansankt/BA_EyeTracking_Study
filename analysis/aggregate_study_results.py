#!/usr/bin/env python3
"""Aggregate individual gaze-analysis outputs into model-level study results."""

import argparse
import csv
import html
import itertools
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path


INTERACTIONS = (
    "user_looks_at_avatar",
    "avatar_looks_at_user",
    "mutual_gaze",
)

METRICS = (
    ("user_looks_at_avatar_proportion_time", "User looks at avatar: proportion of time", "proportion"),
    ("user_looks_at_avatar_mean_episode_duration_ms", "User looks at avatar: mean episode duration", "ms"),
    ("user_looks_at_avatar_episode_rate_per_minute", "User looks at avatar: episode rate", "episodes/min"),
    ("avatar_looks_at_user_proportion_time", "Avatar looks at user: proportion of time", "proportion"),
    ("avatar_looks_at_user_mean_episode_duration_ms", "Avatar looks at user: mean episode duration", "ms"),
    ("avatar_looks_at_user_episode_rate_per_minute", "Avatar looks at user: episode rate", "episodes/min"),
    ("mutual_gaze_proportion_time", "Mutual gaze: proportion of time", "proportion"),
    ("mutual_gaze_mean_episode_duration_ms", "Mutual gaze: mean episode duration", "ms"),
    ("mutual_gaze_episode_rate_per_minute", "Mutual gaze: episode rate", "episodes/min"),
    ("gaze_aversion_rate_per_minute", "Gaze aversion: rate", "aversions/min"),
    ("mean_aversion_duration_ms", "Gaze aversion: mean duration", "ms"),
)

FIGURES = (
    {
        "filename": "interaction_proportion_time.svg",
        "title": "Interaction States: Proportion of Time",
        "y_label": "Proportion of Trial Time",
        "metrics": (
            "user_looks_at_avatar_proportion_time",
            "avatar_looks_at_user_proportion_time",
            "mutual_gaze_proportion_time",
        ),
        "labels": ("User Looks at\nAvatar", "Avatar Looks at\nUser", "Mutual Gaze"),
        "proportion_axis": True,
    },
    {
        "filename": "interaction_mean_episode_duration.svg",
        "title": "Interaction States: Mean Episode Duration",
        "y_label": "Mean Episode Duration (ms)",
        "metrics": (
            "user_looks_at_avatar_mean_episode_duration_ms",
            "avatar_looks_at_user_mean_episode_duration_ms",
            "mutual_gaze_mean_episode_duration_ms",
        ),
        "labels": ("User Looks at\nAvatar", "Avatar Looks at\nUser", "Mutual Gaze"),
        "proportion_axis": False,
    },
    {
        "filename": "interaction_episode_rate.svg",
        "title": "Interaction States: Episode Rate",
        "y_label": "Episodes per Minute",
        "metrics": (
            "user_looks_at_avatar_episode_rate_per_minute",
            "avatar_looks_at_user_episode_rate_per_minute",
            "mutual_gaze_episode_rate_per_minute",
        ),
        "labels": ("User Looks at\nAvatar", "Avatar Looks at\nUser", "Mutual Gaze"),
        "proportion_axis": False,
    },
    {
        "filename": "gaze_aversion_rate.svg",
        "title": "Gaze Aversion: Rate",
        "y_label": "Aversions per Minute",
        "metrics": ("gaze_aversion_rate_per_minute",),
        "labels": ("Gaze Aversion",),
        "proportion_axis": False,
    },
    {
        "filename": "gaze_aversion_mean_duration.svg",
        "title": "Gaze Aversion: Mean Duration",
        "y_label": "Mean Aversion Duration (ms)",
        "metrics": ("mean_aversion_duration_ms",),
        "labels": ("Gaze Aversion",),
        "proportion_axis": False,
    },
)

BOXPLOTS = (
    {
        "filename": "gaze_aversion_rate_boxplot.svg",
        "title": "Gaze Aversion Rate",
        "y_label": "Aversions per Minute",
        "metric": "gaze_aversion_rate_per_minute",
    },
    {
        "filename": "gaze_aversion_mean_duration_boxplot.svg",
        "title": "Mean Gaze Aversion Duration",
        "y_label": "Mean Aversion Duration (ms)",
        "metric": "mean_aversion_duration_ms",
    },
)

MODEL_COLORS = ("#4C78A8", "#E45756")


def read_csv(path):
    with open(path, newline="") as file:
        return list(csv.DictReader(file))


def to_float(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def mean(values):
    return statistics.mean(values) if values else None


def sample_sd(values):
    return statistics.stdev(values) if len(values) > 1 else None


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def condition_label(condition, aware_condition, unaware_condition):
    if condition == unaware_condition:
        return "Gaze-Unaware"
    if condition == aware_condition:
        return "Gaze-Aware"
    return condition


def nice_upper_bound(value):
    if value <= 0:
        return 1

    magnitude = 10 ** math.floor(math.log10(value))
    normalized = value / magnitude

    if normalized <= 1:
        return magnitude
    if normalized <= 2:
        return 2 * magnitude
    if normalized <= 5:
        return 5 * magnitude
    return 10 * magnitude


def format_tick(value, proportion_axis):
    if proportion_axis:
        return f"{value:.1f}"
    if value >= 100:
        return f"{value:.0f}"
    return f"{value:.1f}".rstrip("0").rstrip(".")


def svg_text_lines(lines, x, y, line_height, anchor="middle", css_class="label"):
    spans = []
    for index, line in enumerate(lines):
        dy = "0" if index == 0 else str(line_height)
        spans.append(f'<tspan x="{x:.1f}" dy="{dy}">{html.escape(line)}</tspan>')
    return f'<text class="{css_class}" text-anchor="{anchor}" x="{x:.1f}" y="{y:.1f}">' + "".join(spans) + "</text>"


def summary_index(summaries):
    return {
        (row["condition"], row["metric"]): row
        for row in summaries
    }


def write_grouped_bar_chart(path, figure, summaries, unaware_condition, aware_condition):
    lookup = summary_index(summaries)
    conditions = (unaware_condition, aware_condition)
    values = []
    bars = []

    for metric in figure["metrics"]:
        for condition in conditions:
            row = lookup.get((condition, metric))
            mean_value = to_float(row.get("mean")) if row else None
            sd_value = to_float(row.get("standard_deviation")) if row else None
            if mean_value is None:
                return False
            bars.append((metric, condition, mean_value, sd_value or 0))
            values.append(mean_value + (sd_value or 0))

    upper_value = max(values) if values else 0
    if figure["proportion_axis"]:
        y_max = max(1.0, nice_upper_bound(upper_value * 1.1))
    else:
        y_max = nice_upper_bound(upper_value * 1.1)

    width = 1000
    height = 620
    left = 115
    right = 950
    top = 105
    bottom = 455
    plot_width = right - left
    plot_height = bottom - top
    group_count = len(figure["metrics"])
    group_width = plot_width / group_count
    bar_width = min(72, group_width * 0.3)
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{html.escape(figure["title"])}</title>',
        '<desc id="desc">Grouped bar chart with means and standard deviations for the Gaze-Unaware and Gaze-Aware models.</desc>',
        '<style>.title{font:600 24px Arial,Helvetica,sans-serif;fill:#1b1b1b}.axis{font:14px Arial,Helvetica,sans-serif;fill:#1b1b1b}.label{font:15px Arial,Helvetica,sans-serif;fill:#1b1b1b}.small{font:13px Arial,Helvetica,sans-serif;fill:#1b1b1b}.grid{stroke:#d5d9dc;stroke-width:1}.frame{fill:none;stroke:#767d82;stroke-width:1}.error{stroke:#202124;stroke-width:1.5}</style>',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text class="title" x="{width / 2:.1f}" y="48" text-anchor="middle">{html.escape(figure["title"])}</text>',
    ]

    for tick_index in range(6):
        tick_value = y_max * tick_index / 5
        y = bottom - (tick_value / y_max) * plot_height
        svg.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}"/>')
        svg.append(f'<text class="small" x="{left - 12}" y="{y + 4:.1f}" text-anchor="end">{format_tick(tick_value, figure["proportion_axis"])}</text>')

    svg.append(f'<rect class="frame" x="{left}" y="{top}" width="{plot_width}" height="{plot_height}"/>')
    svg.append(f'<text class="axis" transform="translate(30 {top + plot_height / 2:.1f}) rotate(-90)" text-anchor="middle">{html.escape(figure["y_label"])}</text>')

    for group_index, (metric, label) in enumerate(zip(figure["metrics"], figure["labels"])):
        group_center = left + group_width * (group_index + 0.5)
        for condition_index, condition in enumerate(conditions):
            row = lookup[(condition, metric)]
            mean_value = to_float(row["mean"])
            sd_value = to_float(row.get("standard_deviation")) or 0
            x = group_center + (condition_index - 0.5) * (bar_width + 10)
            bar_height = mean_value / y_max * plot_height
            y = bottom - bar_height
            color = MODEL_COLORS[condition_index]
            svg.append(f'<rect x="{x - bar_width / 2:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" fill="{color}"/>')

            if sd_value > 0:
                upper_y = bottom - min(y_max, mean_value + sd_value) / y_max * plot_height
                lower_y = bottom - max(0, mean_value - sd_value) / y_max * plot_height
                svg.append(f'<line class="error" x1="{x:.1f}" y1="{upper_y:.1f}" x2="{x:.1f}" y2="{lower_y:.1f}"/>')
                svg.append(f'<line class="error" x1="{x - 7:.1f}" y1="{upper_y:.1f}" x2="{x + 7:.1f}" y2="{upper_y:.1f}"/>')
                svg.append(f'<line class="error" x1="{x - 7:.1f}" y1="{lower_y:.1f}" x2="{x + 7:.1f}" y2="{lower_y:.1f}"/>')

        svg.append(svg_text_lines(label.split("\n"), group_center, bottom + 33, 18))

    legend_x = width / 2 - 155
    for index, condition in enumerate(conditions):
        x = legend_x + index * 230
        svg.append(f'<rect x="{x:.1f}" y="535" width="18" height="18" fill="{MODEL_COLORS[index]}"/>')
        svg.append(f'<text class="label" x="{x + 26:.1f}" y="550">{html.escape(condition_label(condition, aware_condition, unaware_condition))}</text>')
    svg.append(f'<text class="small" x="{width / 2:.1f}" y="586" text-anchor="middle">Bars: mean; error bars: standard deviation</text>')
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")
    return True


def write_figures(out_dir, summaries, unaware_condition, aware_condition):
    figures_dir = out_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    written_paths = []
    skipped = []

    for figure in FIGURES:
        path = figures_dir / figure["filename"]
        if write_grouped_bar_chart(path, figure, summaries, unaware_condition, aware_condition):
            written_paths.append(path)
        else:
            skipped.append(figure["filename"])

    return written_paths, skipped


def percentile(values, fraction):
    if len(values) == 1:
        return values[0]

    position = (len(values) - 1) * fraction
    lower_index = math.floor(position)
    upper_index = math.ceil(position)

    if lower_index == upper_index:
        return values[lower_index]

    return (
        values[lower_index] * (upper_index - position)
        + values[upper_index] * (position - lower_index)
    )


def boxplot_statistics(values):
    sorted_values = sorted(values)
    q1 = percentile(sorted_values, 0.25)
    median = percentile(sorted_values, 0.5)
    q3 = percentile(sorted_values, 0.75)
    iqr = q3 - q1
    lower_limit = q1 - 1.5 * iqr
    upper_limit = q3 + 1.5 * iqr
    inliers = [value for value in sorted_values if lower_limit <= value <= upper_limit]

    return {
        "q1": q1,
        "median": median,
        "q3": q3,
        "lower_whisker": min(inliers),
        "upper_whisker": max(inliers),
        "outliers": [
            value for value in sorted_values
            if value < lower_limit or value > upper_limit
        ],
    }


def write_boxplot(path, figure, participant_rows, unaware_condition, aware_condition):
    conditions = (unaware_condition, aware_condition)
    values_by_condition = {}

    for condition in conditions:
        values = [
            to_float(row.get(figure["metric"]))
            for row in participant_rows
            if row["condition"] == condition
        ]
        values = [value for value in values if value is not None]
        if not values:
            return False
        values_by_condition[condition] = values

    statistics_by_condition = {
        condition: boxplot_statistics(values)
        for condition, values in values_by_condition.items()
    }
    maximum_value = max(
        value for values in values_by_condition.values() for value in values
    )
    y_max = nice_upper_bound(maximum_value * 1.1)

    width, height = 820, 620
    left, right, top, bottom = 115, 760, 105, 455
    plot_width = right - left
    plot_height = bottom - top
    centers = (left + plot_width * 0.3, left + plot_width * 0.7)
    box_width = 130
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{html.escape(figure["title"])}</title>',
        '<desc id="desc">Boxplot comparing individual participant values for the Gaze-Unaware and Gaze-Aware models.</desc>',
        '<style>.title{font:600 24px Arial,Helvetica,sans-serif;fill:#1b1b1b}.axis{font:14px Arial,Helvetica,sans-serif;fill:#1b1b1b}.label{font:15px Arial,Helvetica,sans-serif;fill:#1b1b1b}.small{font:13px Arial,Helvetica,sans-serif;fill:#1b1b1b}.grid{stroke:#d5d9dc;stroke-width:1}.frame{fill:none;stroke:#767d82;stroke-width:1}.box{stroke:#202124;stroke-width:1.5}.median{stroke:#202124;stroke-width:2.5}.whisker{stroke:#202124;stroke-width:1.5}.point{fill:#202124;fill-opacity:0.55}</style>',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text class="title" x="{width / 2:.1f}" y="48" text-anchor="middle">{html.escape(figure["title"])}</text>',
    ]

    for tick_index in range(6):
        tick_value = y_max * tick_index / 5
        y = bottom - (tick_value / y_max) * plot_height
        svg.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}"/>')
        svg.append(f'<text class="small" x="{left - 12}" y="{y + 4:.1f}" text-anchor="end">{format_tick(tick_value, False)}</text>')

    svg.append(f'<rect class="frame" x="{left}" y="{top}" width="{plot_width}" height="{plot_height}"/>')
    svg.append(f'<text class="axis" transform="translate(30 {top + plot_height / 2:.1f}) rotate(-90)" text-anchor="middle">{html.escape(figure["y_label"])}</text>')

    for index, condition in enumerate(conditions):
        center_x = centers[index]
        stats = statistics_by_condition[condition]
        scale_y = lambda value: bottom - value / y_max * plot_height
        q1_y, median_y, q3_y = scale_y(stats["q1"]), scale_y(stats["median"]), scale_y(stats["q3"])
        lower_y, upper_y = scale_y(stats["lower_whisker"]), scale_y(stats["upper_whisker"])

        svg.append(f'<line class="whisker" x1="{center_x:.1f}" y1="{upper_y:.1f}" x2="{center_x:.1f}" y2="{q3_y:.1f}"/>')
        svg.append(f'<line class="whisker" x1="{center_x:.1f}" y1="{q1_y:.1f}" x2="{center_x:.1f}" y2="{lower_y:.1f}"/>')
        svg.append(f'<line class="whisker" x1="{center_x - 24:.1f}" y1="{upper_y:.1f}" x2="{center_x + 24:.1f}" y2="{upper_y:.1f}"/>')
        svg.append(f'<line class="whisker" x1="{center_x - 24:.1f}" y1="{lower_y:.1f}" x2="{center_x + 24:.1f}" y2="{lower_y:.1f}"/>')
        svg.append(f'<rect class="box" x="{center_x - box_width / 2:.1f}" y="{q3_y:.1f}" width="{box_width}" height="{q1_y - q3_y:.1f}" fill="{MODEL_COLORS[index]}" fill-opacity="0.55"/>')
        svg.append(f'<line class="median" x1="{center_x - box_width / 2:.1f}" y1="{median_y:.1f}" x2="{center_x + box_width / 2:.1f}" y2="{median_y:.1f}"/>')

        for value_index, value in enumerate(values_by_condition[condition]):
            jitter = ((value_index % 5) - 2) * 9
            svg.append(f'<circle class="point" cx="{center_x + jitter:.1f}" cy="{scale_y(value):.1f}" r="4.5"/>')

        svg.append(f'<text class="label" x="{center_x:.1f}" y="{bottom + 34:.1f}" text-anchor="middle">{html.escape(condition_label(condition, aware_condition, unaware_condition))}</text>')
        svg.append(f'<text class="small" x="{center_x:.1f}" y="{bottom + 57:.1f}" text-anchor="middle">n = {len(values_by_condition[condition])}</text>')

    svg.append(f'<text class="small" x="{width / 2:.1f}" y="586" text-anchor="middle">Box: interquartile range; line: median; whiskers: 1.5 IQR; dots: individual participants</text>')
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")
    return True


def write_boxplots(out_dir, participant_rows, unaware_condition, aware_condition):
    figures_dir = out_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    written_paths = []
    skipped = []

    for figure in BOXPLOTS:
        path = figures_dir / figure["filename"]
        if write_boxplot(path, figure, participant_rows, unaware_condition, aware_condition):
            written_paths.append(path)
        else:
            skipped.append(figure["filename"])

    return written_paths, skipped


def source_name(path):
    return path.name.removesuffix("_interaction_metrics.csv")


def load_trial_rows(input_dir):
    interaction_paths = sorted(input_dir.rglob("*_interaction_metrics.csv"))
    if not interaction_paths:
        raise ValueError(
            "No *_interaction_metrics.csv files found. Run analyze_gaze_aversion.py for each samples.csv first."
        )

    rows = []
    missing_aversion_files = []

    for interaction_path in interaction_paths:
        source = source_name(interaction_path)
        aversion_path = interaction_path.with_name(f"{source}_gaze_aversion_metrics.csv")
        aversion_by_key = {}

        if aversion_path.exists():
            for aversion_row in read_csv(aversion_path):
                key = (
                    aversion_row["participant_id"],
                    aversion_row["trial_id"],
                    aversion_row["condition"],
                )
                aversion_by_key[key] = aversion_row
        else:
            missing_aversion_files.append(aversion_path.name)

        for interaction_row in read_csv(interaction_path):
            key = (
                interaction_row["participant_id"],
                interaction_row["trial_id"],
                interaction_row["condition"],
            )
            combined = dict(interaction_row)
            combined["source_session"] = source
            combined.update(aversion_by_key.get(key, {}))
            rows.append(combined)

    return rows, missing_aversion_files


def aggregate_participant_condition_rows(trial_rows):
    grouped = defaultdict(list)
    for row in trial_rows:
        grouped[(row["participant_id"], row["condition"])].append(row)

    results = []
    for (participant_id, condition), rows in sorted(grouped.items()):
        trial_durations = [to_float(row.get("trial_duration_ms")) or 0 for row in rows]
        total_trial_duration_ms = sum(trial_durations)
        result = {
            "participant_id": participant_id,
            "condition": condition,
            "trial_count": len(rows),
            "source_sessions": ";".join(sorted({row["source_session"] for row in rows})),
            "total_trial_duration_ms": round(total_trial_duration_ms, 3),
        }

        for interaction in INTERACTIONS:
            count_key = f"{interaction}_episode_count"
            duration_key = f"{interaction}_total_episode_duration_ms"
            counts = [to_float(row.get(count_key)) for row in rows]
            durations = [to_float(row.get(duration_key)) for row in rows]

            if any(value is None for value in counts) or any(value is None for value in durations):
                result[f"{interaction}_proportion_time"] = None
                result[f"{interaction}_mean_episode_duration_ms"] = None
                result[f"{interaction}_episode_rate_per_minute"] = None
                result[count_key] = None
                result[duration_key] = None
                continue

            episode_count = sum(counts)
            total_episode_duration_ms = sum(durations)
            result[f"{interaction}_proportion_time"] = round(
                total_episode_duration_ms / total_trial_duration_ms, 6,
            ) if total_trial_duration_ms > 0 else None
            result[f"{interaction}_mean_episode_duration_ms"] = round(
                total_episode_duration_ms / episode_count, 3,
            ) if episode_count > 0 else 0
            result[f"{interaction}_episode_rate_per_minute"] = round(
                episode_count / (total_trial_duration_ms / 60000), 6,
            ) if total_trial_duration_ms > 0 else None
            result[count_key] = int(episode_count)
            result[duration_key] = round(total_episode_duration_ms, 3)

        aversion_count = sum(to_float(row.get("gaze_aversion_count")) or 0 for row in rows)
        aversion_duration = sum(
            to_float(row.get("total_aversion_duration_ms"))
            if to_float(row.get("total_aversion_duration_ms")) is not None
            else (to_float(row.get("gaze_aversion_count")) or 0) * (to_float(row.get("mean_aversion_duration_ms")) or 0)
            for row in rows
        )
        has_aversion_data = any("gaze_aversion_count" in row for row in rows)
        result["gaze_aversion_count"] = int(aversion_count) if has_aversion_data else None
        result["gaze_aversion_rate_per_minute"] = round(
            aversion_count / (total_trial_duration_ms / 60000), 6,
        ) if has_aversion_data and total_trial_duration_ms > 0 else None
        result["mean_aversion_duration_ms"] = round(
            aversion_duration / aversion_count, 3,
        ) if has_aversion_data and aversion_count > 0 else None
        result["total_aversion_duration_ms"] = round(aversion_duration, 3) if has_aversion_data else None
        results.append(result)

    return results


def build_condition_summary(rows):
    summaries = []
    for condition in sorted({row["condition"] for row in rows}):
        condition_rows = [row for row in rows if row["condition"] == condition]
        for metric, label, unit in METRICS:
            values = [to_float(row.get(metric)) for row in condition_rows]
            values = [value for value in values if value is not None]
            summaries.append({
                "condition": condition,
                "metric": metric,
                "metric_label": label,
                "unit": unit,
                "participant_count": len(values),
                "mean": round(mean(values), 6) if values else None,
                "standard_deviation": round(sample_sd(values), 6) if len(values) > 1 else None,
            })
    return summaries


def paired_permutation_test(differences, seed):
    observed = abs(mean(differences))
    if observed == 0:
        return 1.0, "exact paired sign-permutation", 1

    exact_count = 2 ** len(differences)
    if exact_count <= 65536:
        extreme = 0
        for signs in itertools.product((-1, 1), repeat=len(differences)):
            statistic = abs(sum(value * sign for value, sign in zip(differences, signs)) / len(differences))
            if statistic >= observed - 1e-12:
                extreme += 1
        return extreme / exact_count, "exact paired sign-permutation", exact_count

    simulations = 100000
    generator = random.Random(seed)
    extreme = 0
    for _ in range(simulations):
        statistic = abs(sum(value if generator.random() < 0.5 else -value for value in differences) / len(differences))
        if statistic >= observed - 1e-12:
            extreme += 1
    return (extreme + 1) / (simulations + 1), "Monte-Carlo paired sign-permutation", simulations


def holm_adjust(rows):
    valid = [(index, row["p_value_raw"]) for index, row in enumerate(rows) if row["p_value_raw"] is not None]
    valid.sort(key=lambda item: item[1])
    adjusted = 0
    total = len(valid)
    for rank, (index, raw_p) in enumerate(valid):
        adjusted = max(adjusted, min(1.0, raw_p * (total - rank)))
        rows[index]["p_value_holm"] = round(adjusted, 6)
        rows[index]["significant_holm_0_05"] = adjusted < 0.05


def build_paired_tests(rows, unaware_condition, aware_condition):
    by_participant = defaultdict(dict)
    for row in rows:
        by_participant[row["participant_id"]][row["condition"]] = row

    tests = []
    for metric_index, (metric, label, unit) in enumerate(METRICS):
        pairs = []
        for participant_id, condition_rows in by_participant.items():
            unaware_value = to_float(condition_rows.get(unaware_condition, {}).get(metric))
            aware_value = to_float(condition_rows.get(aware_condition, {}).get(metric))
            if unaware_value is not None and aware_value is not None:
                pairs.append((participant_id, unaware_value, aware_value))

        unaware_values = [pair[1] for pair in pairs]
        aware_values = [pair[2] for pair in pairs]
        differences = [aware - unaware for _, unaware, aware in pairs]
        test_row = {
            "metric": metric,
            "metric_label": label,
            "unit": unit,
            "comparison": f"{aware_condition} minus {unaware_condition}",
            "paired_participant_count": len(pairs),
            "unaware_mean": round(mean(unaware_values), 6) if unaware_values else None,
            "unaware_standard_deviation": round(sample_sd(unaware_values), 6) if len(unaware_values) > 1 else None,
            "aware_mean": round(mean(aware_values), 6) if aware_values else None,
            "aware_standard_deviation": round(sample_sd(aware_values), 6) if len(aware_values) > 1 else None,
            "mean_difference_aware_minus_unaware": round(mean(differences), 6) if differences else None,
            "difference_standard_deviation": round(sample_sd(differences), 6) if len(differences) > 1 else None,
            "cohen_dz": None,
            "test": None,
            "permutation_count": None,
            "p_value_raw": None,
            "p_value_holm": None,
            "significant_holm_0_05": None,
            "note": "",
        }

        difference_sd = sample_sd(differences)
        if difference_sd and difference_sd > 0:
            test_row["cohen_dz"] = round(mean(differences) / difference_sd, 6)

        if len(differences) < 2:
            test_row["note"] = "At least two paired participants are required for a comparison."
        else:
            p_value, test_name, permutation_count = paired_permutation_test(differences, 20260810 + metric_index)
            test_row["test"] = test_name
            test_row["permutation_count"] = permutation_count
            test_row["p_value_raw"] = round(p_value, 6)
            if len(differences) < 5:
                test_row["note"] = "Fewer than five paired participants: interpret this result as exploratory."
        tests.append(test_row)

    holm_adjust(tests)
    return tests


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate individual gaze-analysis outputs and compare GAZE_AWARE with GAZE_UNAWARE."
    )
    parser.add_argument("input_dir", help="Directory containing individual *_interaction_metrics.csv and *_gaze_aversion_metrics.csv files.")
    parser.add_argument("--out-dir", default=None, help="Output directory. Defaults to <input_dir>/study_results.")
    parser.add_argument("--unaware-condition", default="GAZE_UNAWARE")
    parser.add_argument("--aware-condition", default="GAZE_AWARE")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    out_dir = Path(args.out_dir) if args.out_dir else input_dir / "study_results"
    out_dir.mkdir(parents=True, exist_ok=True)

    trial_rows, missing_aversion_files = load_trial_rows(input_dir)
    participant_rows = aggregate_participant_condition_rows(trial_rows)
    summaries = build_condition_summary(participant_rows)
    tests = build_paired_tests(participant_rows, args.unaware_condition, args.aware_condition)

    participant_fields = [
        "participant_id", "condition", "trial_count", "source_sessions", "total_trial_duration_ms",
    ]
    for interaction in INTERACTIONS:
        participant_fields.extend([
            f"{interaction}_proportion_time",
            f"{interaction}_mean_episode_duration_ms",
            f"{interaction}_episode_rate_per_minute",
            f"{interaction}_episode_count",
            f"{interaction}_total_episode_duration_ms",
        ])
    participant_fields.extend([
        "gaze_aversion_count", "gaze_aversion_rate_per_minute",
        "mean_aversion_duration_ms", "total_aversion_duration_ms",
    ])

    summary_fields = [
        "condition", "metric", "metric_label", "unit", "participant_count", "mean", "standard_deviation",
    ]
    test_fields = [
        "metric", "metric_label", "unit", "comparison", "paired_participant_count",
        "unaware_mean", "unaware_standard_deviation", "aware_mean", "aware_standard_deviation",
        "mean_difference_aware_minus_unaware", "difference_standard_deviation", "cohen_dz",
        "test", "permutation_count", "p_value_raw", "p_value_holm", "significant_holm_0_05", "note",
    ]

    participant_path = out_dir / "participant_condition_metrics.csv"
    summary_path = out_dir / "condition_summary.csv"
    tests_path = out_dir / "paired_condition_tests.csv"
    write_csv(participant_path, participant_rows, participant_fields)
    write_csv(summary_path, summaries, summary_fields)
    write_csv(tests_path, tests, test_fields)
    figure_paths, skipped_figures = write_figures(
        out_dir,
        summaries,
        args.unaware_condition,
        args.aware_condition,
    )
    boxplot_paths, skipped_boxplots = write_boxplots(
        out_dir,
        participant_rows,
        args.unaware_condition,
        args.aware_condition,
    )

    print(f"Wrote {participant_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {tests_path}")
    for figure_path in figure_paths:
        print(f"Wrote {figure_path}")
    for boxplot_path in boxplot_paths:
        print(f"Wrote {boxplot_path}")
    print(f"Participants with both conditions: {max((row['paired_participant_count'] for row in tests), default=0)}")
    if missing_aversion_files:
        print("Warning: missing aversion files: " + ", ".join(sorted(missing_aversion_files)))
    if skipped_figures:
        print("Warning: skipped figures with missing data: " + ", ".join(skipped_figures))
    if skipped_boxplots:
        print("Warning: skipped boxplots with missing data: " + ", ".join(skipped_boxplots))


if __name__ == "__main__":
    main()
