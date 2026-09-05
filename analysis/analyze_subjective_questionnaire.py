#!/usr/bin/env python3
"""Analyse der subjektiven Fragebogendaten der Gaze-Studie.

Die beiden SoSci-Survey-CSV-Dateien werden über die Participant ID gepaart.
Gerade IDs sahen zuerst das gaze-aware Modell, ungerade IDs zuerst das
gaze-unaware Modell. Das Skript schreibt keine Rohdaten um, sondern erzeugt
abgeleitete, anonymisierte Analyse-CSV-Dateien.

Beispiel:
    python3 analysis/analyze_subjective_questionnaire.py \
      --trial1 /pfad/zu/trial1.csv \
      --trial2 /pfad/zu/trial2.csv

Die SoSci-Exporte müssen UTF-16-kodiert und tab-separiert sein.
"""

from __future__ import annotations

import argparse
import csv
import html
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median, stdev, variance
from typing import Iterable


TRIAL_ITEMS = {
    "TQ01_01": "The eyes appeared to be aware of my presence.",
    "TQ01_02": "The eyes appeared to react to me.",
    "TQ01_03": "The eye movements appeared natural.",
    "TQ01_04": "The behaviour of the eyes appeared believable.",
    "TQ01_05": "The eyes seemed attentive.",
    "TQ01_06": "I felt that the eyes were interacting with me.",
    "TQ01_07": "I was satisfied with the interaction.",
    "TQ01_08": "I found the interaction engaging.",
}

COMPARISON_ITEMS = {
    "UT01_01": "Which version felt more natural?",
    "UT01_02": "Which version appeared more responsive?",
    "UT01_03": "Which version would you prefer to use in an interactive application?",
    "UT01_04": "Overall, which version did you prefer?",
}

TRIAL_SCALE = range(1, 6)  # Im vorliegenden Export: 1 bis 5.
COMPARISON_SCALE = range(1, 8)
RESULT_FIELDS = [
    "analysis_section",
    "result_id",
    "question_text",
    "test_description",
    "n",
    "median_gaze_aware",
    "iqr_gaze_aware",
    "median_gaze_unaware",
    "iqr_gaze_unaware",
    "median_difference_aware_minus_unaware",
    "n_nonzero_differences",
    "wilcoxon_w_plus",
    "wilcoxon_w_minus",
    "rank_biserial_correlation",
    "p_value_exact",
    "p_value_holm",
    "n_prefer_gaze_aware",
    "n_neutral",
    "n_prefer_gaze_unaware",
    "percent_prefer_gaze_aware",
    "mean",
    "standard_deviation",
    "minimum",
    "maximum",
    "percentage",
    "value",
    "note",
]

BASELINE_COLOR = "#4C78A8"
GAZE_AWARE_COLOR = "#E45756"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trial1", required=True, type=Path, help="SoSci-CSV nach Trial 1")
    parser.add_argument("--trial2", required=True, type=Path, help="SoSci-CSV nach Trial 2")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("analysis/subjective_results"),
        help="Zielordner für die Ergebnisdateien (Standard: analysis/subjective_results)",
    )
    return parser.parse_args()


def read_sosci_csv(path: Path) -> list[dict[str, str]]:
    """Liest den tab-separierten UTF-16-Export und entfernt die Beschreibungszeile."""
    with path.open("r", encoding="utf-16", newline="") as file:
        rows = list(csv.reader(file, delimiter="\t"))

    if len(rows) < 3:
        raise ValueError(f"{path} enthält keine verwertbaren Datenzeilen.")

    header = rows[0]
    records = []
    for row in rows[2:]:  # rows[1] enthält die SoSci-Fragebeschreibungen.
        record = dict(zip(header, row))
        participant_id = record.get("DD03_01", "").strip()
        if participant_id.isdigit():
            records.append({key: value.strip() for key, value in record.items()})
    return records


def number(value: str, field: str, participant_id: int, valid_values: Iterable[int]) -> int:
    """Liest eine Pflichtantwort und prüft ihre Skalenwerte."""
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(
            f"Participant {participant_id}: fehlender oder ungültiger Wert in {field!r}: {value!r}"
        ) from error
    if parsed not in valid_values:
        raise ValueError(
            f"Participant {participant_id}: Wert {parsed} in {field!r} liegt außerhalb "
            f"der erwarteten Skala {min(valid_values)}–{max(valid_values)}."
        )
    return parsed


def optional_number(value: str, field: str, participant_id: int, valid_values: Iterable[int]) -> int | None:
    if not value.strip():
        return None
    return number(value, field, participant_id, valid_values)


def participant_models(participant_id: int) -> tuple[str, str, str]:
    """Gibt Modell in Trial 1, Modell in Trial 2 und Reihenfolgegruppe zurück."""
    if participant_id % 2 == 0:
        return "gaze_aware", "gaze_unaware", "aware_first"
    return "gaze_unaware", "gaze_aware", "unaware_first"


def percentile(values: list[float], fraction: float) -> float:
    """Lineare Quantile für die IQR-Berechnung."""
    ordered = sorted(values)
    if not ordered:
        return math.nan
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (position - lower) * (ordered[upper] - ordered[lower])


def iqr(values: list[float]) -> float:
    return percentile(values, 0.75) - percentile(values, 0.25)


def rank_absolute_values(values: list[float]) -> list[float]:
    """Mittlere Ränge für Beträge, einschließlich gebundener Werte."""
    order = sorted(range(len(values)), key=lambda index: abs(values[index]))
    ranks = [0.0] * len(values)
    position = 0
    while position < len(order):
        end = position
        current = abs(values[order[position]])
        while end + 1 < len(order) and abs(values[order[end + 1]]) == current:
            end += 1
        average_rank = (position + 1 + end + 1) / 2
        for rank_position in range(position, end + 1):
            ranks[order[rank_position]] = average_rank
        position = end + 1
    return ranks


def exact_wilcoxon_signed_rank(differences: list[float]) -> dict[str, float | int]:
    """Exakter zweiseitiger Wilcoxon-Test via Sign-Flip-Verteilung.

    Null-Differenzen werden ausgeschlossen. Bei gebundenen Rängen wird die
    exakte Permutationsverteilung der beobachteten mittleren Ränge verwendet.
    Dadurch sind keine externen Statistikpakete nötig.
    """
    nonzero = [difference for difference in differences if difference != 0]
    if not nonzero:
        return {"n_nonzero": 0, "w_plus": 0.0, "w_minus": 0.0, "rank_biserial": 0.0, "p_value": 1.0}

    ranks = rank_absolute_values(nonzero)
    w_plus = sum(rank for difference, rank in zip(nonzero, ranks) if difference > 0)
    total_rank = sum(ranks)
    w_minus = total_rank - w_plus

    # Ränge sind ganz- oder halbzahlig. Skalierung um zwei erlaubt eine
    # exakte dynamische Programmierung mit ganzzahligen Summen.
    scaled_ranks = [round(rank * 2) for rank in ranks]
    observed = round(w_plus * 2)
    distribution: dict[int, int] = {0: 1}
    for rank in scaled_ranks:
        updated = defaultdict(int)
        for partial_sum, count in distribution.items():
            updated[partial_sum] += count
            updated[partial_sum + rank] += count
        distribution = dict(updated)

    permutations = 2 ** len(scaled_ranks)
    lower_probability = sum(count for score, count in distribution.items() if score <= observed) / permutations
    upper_probability = sum(count for score, count in distribution.items() if score >= observed) / permutations
    p_value = min(1.0, 2 * min(lower_probability, upper_probability))
    rank_biserial = (w_plus - w_minus) / total_rank
    return {
        "n_nonzero": len(nonzero),
        "w_plus": w_plus,
        "w_minus": w_minus,
        "rank_biserial": rank_biserial,
        "p_value": p_value,
    }


def holm_adjust(rows: list[dict[str, object]]) -> None:
    """Ergänzt Holm-korrigierte p-Werte in einer zusammengehörigen Testfamilie."""
    indexed = sorted(enumerate(rows), key=lambda pair: float(pair[1]["p_value_exact"]))
    running_maximum = 0.0
    count = len(indexed)
    for rank, (_, row) in enumerate(indexed):
        adjusted = min(1.0, (count - rank) * float(row["p_value_exact"]))
        running_maximum = max(running_maximum, adjusted)
        row["p_value_holm"] = running_maximum


def cronbach_alpha(matrix: list[list[float]]) -> float:
    """Cronbachs Alpha für eine vollständige Personen-mal-Items-Matrix."""
    if len(matrix) < 2 or not matrix or len(matrix[0]) < 2:
        return math.nan
    item_count = len(matrix[0])
    item_variances = [variance([row[index] for row in matrix]) for index in range(item_count)]
    total_variance = variance([sum(row) for row in matrix])
    if total_variance == 0:
        return math.nan
    return item_count / (item_count - 1) * (1 - sum(item_variances) / total_variance)


def csv_value(value: object) -> object:
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        return f"{value:.6f}"
    return value


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_value(row.get(field, "")) for field in fieldnames})


def svg_text_lines(lines: list[str], x: float, y: float, line_height: float, css_class: str = "label") -> str:
    spans = []
    for index, line in enumerate(lines):
        dy = "0" if index == 0 else str(line_height)
        spans.append(f'<tspan x="{x:.1f}" dy="{dy}">{html.escape(line)}</tspan>')
    return f'<text class="{css_class}" text-anchor="middle" x="{x:.1f}" y="{y:.1f}">' + "".join(spans) + "</text>"


def significance_label(p_value: float) -> str:
    """Signifikanzmarker für die unkorrektierten exakten p-Werte, sonst leer."""
    if p_value < 0.001:
        return "***"
    if p_value < 0.01:
        return "**"
    if p_value < 0.05:
        return "*"
    return ""


def write_trial_rating_chart(
    path: Path,
    processed_rows: list[dict[str, object]],
    results_by_id: dict[str, dict[str, object]],
) -> None:
    """Gruppiertes Balkendiagramm der acht Trial-Ratings mit Mittelwert ± SD."""
    labels = [
        ["Presence", "(Q1)"],
        ["Reaction", "(Q2)"],
        ["Naturalness", "(Q3)"],
        ["Believability", "(Q4)"],
        ["Attentiveness", "(Q5)"],
        ["Interaction", "(Q6)"],
        ["Satisfaction", "(Q7)"],
        ["Engagement", "(Q8)"],
    ]
    summaries = []
    maximum_value = 5.0
    for item in TRIAL_ITEMS:
        aware = [float(row[f"aware_{item}"]) for row in processed_rows]
        baseline = [float(row[f"unaware_{item}"]) for row in processed_rows]
        aware_mean = sum(aware) / len(aware)
        baseline_mean = sum(baseline) / len(baseline)
        aware_sd = stdev(aware)
        baseline_sd = stdev(baseline)
        maximum_value = max(maximum_value, aware_mean + aware_sd, baseline_mean + baseline_sd)
        summaries.append((item, baseline_mean, baseline_sd, aware_mean, aware_sd))

    y_max = math.ceil((maximum_value + 0.55) * 2) / 2
    width, height = 1800, 720
    left, right, top, bottom = 165, 1730, 50, 510
    plot_width, plot_height = right - left, bottom - top
    group_width = plot_width / len(summaries)
    bar_width = min(68, group_width * 0.29)

    def y_position(value: float) -> float:
        return bottom - value / y_max * plot_height

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Subjective Trial Ratings</title>',
        '<desc id="desc">Grouped bar chart comparing baseline and gaze-aware ratings. Error bars show sample standard deviations; significance markers use exact Wilcoxon signed-rank p-values.</desc>',
        '<style>.title{font:600 30px Arial,Helvetica,sans-serif;fill:#1b1b1b}.axis{font:28px Arial,Helvetica,sans-serif;fill:#1b1b1b}.label{font:24px Arial,Helvetica,sans-serif;fill:#1b1b1b}.small{font:21px Arial,Helvetica,sans-serif;fill:#1b1b1b}.grid{stroke:#d5d9dc;stroke-width:1}.frame{fill:none;stroke:#767d82;stroke-width:1}.error{stroke:#202124;stroke-width:1.5}.significance{fill:none;stroke:#202124;stroke-width:1.5}.significance-label{font:600 22px Arial,Helvetica,sans-serif;fill:#202124}</style>',
        '<rect width="100%" height="100%" fill="white"/>',
    ]

    for tick in range(0, math.floor(y_max) + 1):
        y = y_position(tick)
        svg.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}"/>')
        svg.append(f'<text class="small" x="{left - 14}" y="{y + 5:.1f}" text-anchor="end">{tick}</text>')
    svg.append(f'<rect class="frame" x="{left}" y="{top}" width="{plot_width}" height="{plot_height}"/>')
    svg.append(f'<text class="axis" transform="translate(35 {top + plot_height / 2:.1f}) rotate(-90)" text-anchor="middle">Agreement rating (1–5)</text>')

    for index, ((item, baseline_mean, baseline_sd, aware_mean, aware_sd), label) in enumerate(zip(summaries, labels)):
        center = left + group_width * (index + 0.5)
        baseline_x = center - (bar_width + 9) / 2
        aware_x = center + (bar_width + 9) / 2
        for x, mean_value, sd_value, color in (
            (baseline_x, baseline_mean, baseline_sd, BASELINE_COLOR),
            (aware_x, aware_mean, aware_sd, GAZE_AWARE_COLOR),
        ):
            y = y_position(mean_value)
            svg.append(f'<rect x="{x - bar_width / 2:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bottom - y:.1f}" fill="{color}"/>')
            upper_y = y_position(min(y_max, mean_value + sd_value))
            lower_y = y_position(max(0, mean_value - sd_value))
            svg.append(f'<line class="error" x1="{x:.1f}" y1="{upper_y:.1f}" x2="{x:.1f}" y2="{lower_y:.1f}"/>')
            svg.append(f'<line class="error" x1="{x - 7:.1f}" y1="{upper_y:.1f}" x2="{x + 7:.1f}" y2="{upper_y:.1f}"/>')
            svg.append(f'<line class="error" x1="{x - 7:.1f}" y1="{lower_y:.1f}" x2="{x + 7:.1f}" y2="{lower_y:.1f}"/>')

        p_value = float(results_by_id[item]["p_value_exact"])
        marker = significance_label(p_value)
        if marker:
            bracket_value = min(y_max - 0.13, max(baseline_mean + baseline_sd, aware_mean + aware_sd) + 0.28)
            bracket_y = y_position(bracket_value)
            bracket_bottom = bracket_y + 8
            svg.append(f'<path class="significance" d="M {baseline_x - bar_width / 2 - 5:.1f} {bracket_bottom:.1f} V {bracket_y:.1f} H {aware_x + bar_width / 2 + 5:.1f} V {bracket_bottom:.1f}"/>')
            svg.append(f'<text class="significance-label" x="{center:.1f}" y="{bracket_y - 6:.1f}" text-anchor="middle">{marker}</text>')
        svg.append(svg_text_lines(label, center, bottom + 38, 26))

    legend_x = width / 2 - 180
    for index, (label, color) in enumerate((("Baseline", BASELINE_COLOR), ("Gaze-aware", GAZE_AWARE_COLOR))):
        x = legend_x + index * 230
        svg.append(f'<rect x="{x:.1f}" y="625" width="22" height="22" fill="{color}"/>')
        svg.append(f'<text class="label" x="{x + 32:.1f}" y="644">{label}</text>')
    svg.append('</svg>')
    path.write_text("\n".join(svg), encoding="utf-8")


def write_direct_comparison_chart(
    path: Path,
    processed_rows: list[dict[str, object]],
    results_by_id: dict[str, dict[str, object]],
) -> None:
    """Gruppiertes Balkendiagramm der modellbezogen ausgerichteten Vergleichsskala."""
    labels = [
        ["Perceived", "naturalness", "(CQ1)"],
        ["Responsiveness", "(CQ2)"],
        ["Preference for use", "in interactive applications", "(CQ3)"],
        ["Overall preference", "(CQ4)"],
    ]
    summaries = []
    for item in COMPARISON_ITEMS:
        preference_values = [
            float(row[f"{item}_aware_preference"])
            for row in processed_rows
            if row[f"{item}_aware_preference"] != ""
        ]
        # Die ursprüngliche Antwort ist eine bipolare 1–7-Skala. Die beiden
        # Werte eines Paars sind daher spiegelbildlich um den Neutralwert 4.
        # Die Rangfolge der Differenzen und damit p_value_exact bleiben gleich.
        baseline_values = [4 - value for value in preference_values]
        aware_values = [4 + value for value in preference_values]
        summaries.append((
            item,
            sum(baseline_values) / len(baseline_values),
            stdev(baseline_values),
            sum(aware_values) / len(aware_values),
            stdev(aware_values),
            len(preference_values),
        ))

    width, height = 1400, 720
    left, right, top, bottom = 165, 1335, 50, 485
    plot_width, plot_height = right - left, bottom - top
    y_min, y_max = 0, 7.6
    group_width = plot_width / len(summaries)
    bar_width = min(95, group_width * 0.30)

    def y_position(value: float) -> float:
        return bottom - (value - y_min) / (y_max - y_min) * plot_height

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Direct Comparison Ratings</title>',
        '<desc id="desc">Grouped bar chart of condition-aligned direct comparison ratings. Baseline and gaze-aware values are mirrored around the neutral midpoint 4. Error bars show sample standard deviations.</desc>',
        '<style>.title{font:600 30px Arial,Helvetica,sans-serif;fill:#1b1b1b}.axis{font:28px Arial,Helvetica,sans-serif;fill:#1b1b1b}.label{font:24px Arial,Helvetica,sans-serif;fill:#1b1b1b}.small{font:21px Arial,Helvetica,sans-serif;fill:#1b1b1b}.grid{stroke:#d5d9dc;stroke-width:1}.neutral{stroke:#202124;stroke-width:2}.frame{fill:none;stroke:#767d82;stroke-width:1}.error{stroke:#202124;stroke-width:1.5}.significance{fill:none;stroke:#202124;stroke-width:1.5}.significance-label{font:600 22px Arial,Helvetica,sans-serif;fill:#202124}</style>',
        '<rect width="100%" height="100%" fill="white"/>',
    ]

    for tick in range(0, 8):
        y = y_position(tick)
        css_class = "neutral" if tick == 4 else "grid"
        svg.append(f'<line class="{css_class}" x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}"/>')
        svg.append(f'<text class="small" x="{left - 14}" y="{y + 5:.1f}" text-anchor="end">{tick}</text>')
    svg.append(f'<rect class="frame" x="{left}" y="{top}" width="{plot_width}" height="{plot_height}"/>')
    svg.append(f'<text class="axis" transform="translate(35 {top + plot_height / 2:.1f}) rotate(-90)" text-anchor="middle">Condition-aligned comparison rating (1–7)</text>')

    for index, ((item, baseline_mean, baseline_sd, aware_mean, aware_sd, _), label) in enumerate(zip(summaries, labels)):
        center = left + group_width * (index + 0.5)
        baseline_x = center - (bar_width + 10) / 2
        aware_x = center + (bar_width + 10) / 2
        for x, mean_value, sd_value, color in (
            (baseline_x, baseline_mean, baseline_sd, BASELINE_COLOR),
            (aware_x, aware_mean, aware_sd, GAZE_AWARE_COLOR),
        ):
            top_y = y_position(mean_value)
            svg.append(f'<rect x="{x - bar_width / 2:.1f}" y="{top_y:.1f}" width="{bar_width:.1f}" height="{bottom - top_y:.1f}" fill="{color}"/>')
            upper_y = y_position(min(y_max, mean_value + sd_value))
            lower_y = y_position(max(y_min, mean_value - sd_value))
            svg.append(f'<line class="error" x1="{x:.1f}" y1="{upper_y:.1f}" x2="{x:.1f}" y2="{lower_y:.1f}"/>')
            svg.append(f'<line class="error" x1="{x - 7:.1f}" y1="{upper_y:.1f}" x2="{x + 7:.1f}" y2="{upper_y:.1f}"/>')
            svg.append(f'<line class="error" x1="{x - 7:.1f}" y1="{lower_y:.1f}" x2="{x + 7:.1f}" y2="{lower_y:.1f}"/>')

        p_value = float(results_by_id[item]["p_value_exact"])
        marker = significance_label(p_value)
        if marker:
            bracket_value = min(y_max - 0.13, max(baseline_mean + baseline_sd, aware_mean + aware_sd) + 0.25)
            bracket_y = y_position(bracket_value)
            bracket_bottom = bracket_y + 8
            svg.append(f'<path class="significance" d="M {baseline_x - bar_width / 2 - 5:.1f} {bracket_bottom:.1f} V {bracket_y:.1f} H {aware_x + bar_width / 2 + 5:.1f} V {bracket_bottom:.1f}"/>')
            svg.append(f'<text class="significance-label" x="{center:.1f}" y="{bracket_y - 6:.1f}" text-anchor="middle">{marker}</text>')
        svg.append(svg_text_lines(label, center, bottom + 38, 26))

    legend_x = width / 2 - 180
    for index, (label, color) in enumerate((("Baseline", BASELINE_COLOR), ("Gaze-aware", GAZE_AWARE_COLOR))):
        x = legend_x + index * 230
        svg.append(f'<rect x="{x:.1f}" y="625" width="22" height="22" fill="{color}"/>')
        svg.append(f'<text class="label" x="{x + 32:.1f}" y="644">{label}</text>')
    svg.append('</svg>')
    path.write_text("\n".join(svg), encoding="utf-8")


def latex_number(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def latex_p_value(value: float) -> str:
    if value < 0.001:
        return "< .001"
    return f"{value:.3f}".lstrip("0")


def write_latex_trial_rating_table(
    path: Path,
    processed_rows: list[dict[str, object]],
    results_by_id: dict[str, dict[str, object]],
) -> None:
    labels = [
        "Presence (Q1)",
        "Reaction (Q2)",
        "Naturalness (Q3)",
        "Believability (Q4)",
        "Attentiveness (Q5)",
        "Interaction (Q6)",
        "Satisfaction (Q7)",
        "Engagement (Q8)",
    ]
    lines = [
        "% Requires: \\usepackage{booktabs}",
        "\\begin{table}[htbp]",
        "  \\centering",
        "  \\small",
        "  \\caption{Subjective trial ratings by condition.}",
        "  \\label{tab:subjective-trial-ratings}",
        "  \\begin{tabular}{lrrrrr}",
        "    \\toprule",
        "    Item & Baseline, $M$ (SD) & Gaze-aware, $M$ (SD) & $n_{\\mathrm{eff}}$ & $p_{\\mathrm{exact}}$ & $r_{\\mathrm{rb}}$ \\\\",
        "    \\midrule",
    ]
    for item, label in zip(TRIAL_ITEMS, labels):
        baseline = [float(row[f"unaware_{item}"]) for row in processed_rows]
        aware = [float(row[f"aware_{item}"]) for row in processed_rows]
        result = results_by_id[item]
        lines.append(
            f"    {label} & {latex_number(sum(baseline) / len(baseline))} ({latex_number(stdev(baseline))}) "
            f"& {latex_number(sum(aware) / len(aware))} ({latex_number(stdev(aware))}) "
            f"& {int(result['n_nonzero_differences'])} & {latex_p_value(float(result['p_value_exact']))} "
            f"& {latex_number(float(result['rank_biserial_correlation']))} \\\\")
    lines.extend([
        "    \\bottomrule",
        "  \\end{tabular}",
        "  \\begin{flushleft}",
        "    \\footnotesize Note. $N = 18$. Values are mean (sample standard deviation). $n_{\\mathrm{eff}}$ is the number of non-zero paired differences included in the Wilcoxon test. $p_{\\mathrm{exact}}$ is the uncorrected two-sided exact Wilcoxon signed-rank p-value. Positive $r_{\\mathrm{rb}}$ values favour gaze-aware.",
        "  \\end{flushleft}",
        "\\end{table}",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_latex_direct_comparison_table(
    path: Path,
    processed_rows: list[dict[str, object]],
    results_by_id: dict[str, dict[str, object]],
) -> None:
    labels = [
        "Perceived naturalness (CQ1)",
        "Responsiveness (CQ2)",
        "Preference for use in interactive applications (CQ3)",
        "Overall preference (CQ4)",
    ]
    lines = [
        "% Requires: \\usepackage{booktabs}",
        "\\begin{table}[htbp]",
        "  \\centering",
        "  \\small",
        "  \\caption{Direct comparison ratings by condition.}",
        "  \\label{tab:subjective-direct-comparisons}",
        "  \\begin{tabular}{p{6.0cm}rrrr}",
        "    \\toprule",
        "    Item & Baseline, $M$ (SD) & Gaze-aware, $M$ (SD) & $p_{\\mathrm{exact}}$ & $r_{\\mathrm{rb}}$ \\\\",
        "    \\midrule",
    ]
    for item, label in zip(COMPARISON_ITEMS, labels):
        preference_values = [
            float(row[f"{item}_aware_preference"])
            for row in processed_rows
            if row[f"{item}_aware_preference"] != ""
        ]
        baseline = [4 - value for value in preference_values]
        aware = [4 + value for value in preference_values]
        result = results_by_id[item]
        lines.append(
            f"    {label} & {latex_number(sum(baseline) / len(baseline))} ({latex_number(stdev(baseline))}) "
            f"& {latex_number(sum(aware) / len(aware))} ({latex_number(stdev(aware))}) "
            f"& {latex_p_value(float(result['p_value_exact']))} & {latex_number(float(result['rank_biserial_correlation']))} \\\\")
    lines.extend([
        "    \\bottomrule",
        "  \\end{tabular}",
        "  \\begin{flushleft}",
        "    \\footnotesize Note. $N = 14$ participants reported noticing a difference. Values are condition-aligned means (sample standard deviations) on the 1--7 bipolar comparison scale, mirrored around the neutral midpoint of 4. $p_{\\mathrm{exact}}$ is the uncorrected two-sided exact Wilcoxon signed-rank p-value against the neutral midpoint. Positive $r_{\\mathrm{rb}}$ values favour gaze-aware.",
        "  \\end{flushleft}",
        "\\end{table}",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    trial1_rows = read_sosci_csv(args.trial1)
    trial2_rows = read_sosci_csv(args.trial2)
    trial1_by_id = {int(row["DD03_01"]): row for row in trial1_rows}
    trial2_by_id = {int(row["DD03_01"]): row for row in trial2_rows}

    if len(trial1_by_id) != len(trial1_rows) or len(trial2_by_id) != len(trial2_rows):
        raise ValueError("Participant IDs müssen innerhalb jedes Trials eindeutig sein.")
    if set(trial1_by_id) != set(trial2_by_id):
        only_trial1 = sorted(set(trial1_by_id) - set(trial2_by_id))
        only_trial2 = sorted(set(trial2_by_id) - set(trial1_by_id))
        raise ValueError(f"Teilnehmende können nicht gepaart werden. Nur Trial 1: {only_trial1}; nur Trial 2: {only_trial2}")

    processed_rows: list[dict[str, object]] = []
    paired_values: dict[str, list[tuple[float, float]]] = {item: [] for item in TRIAL_ITEMS}
    aware_matrix: list[list[float]] = []
    unaware_matrix: list[list[float]] = []
    comparison_values: dict[str, list[float]] = {item: [] for item in COMPARISON_ITEMS}
    difference_counts: Counter[str] = Counter()
    ages: list[int] = []
    gender_counts: Counter[str] = Counter()

    for participant_id in sorted(trial1_by_id):
        first = trial1_by_id[participant_id]
        second = trial2_by_id[participant_id]
        if first.get("STATUS") != "complete" or second.get("STATUS") != "complete":
            raise ValueError(f"Participant {participant_id} hat nicht beide Fragebögen vollständig abgeschlossen.")

        trial1_model, trial2_model, order_group = participant_models(participant_id)
        age = number(first["DD02_01"], "DD02_01", participant_id, range(1, 121))
        gender_code = first.get("DD01", "").strip()
        if not gender_code:
            raise ValueError(f"Participant {participant_id}: fehlender Wert in DD01 (Geschlecht).")
        output: dict[str, object] = {
            "participant_id": participant_id,
            "age_years": age,
            "gender_response_code": gender_code,
            "order_group": order_group,
            "trial1_model": trial1_model,
            "trial2_model": trial2_model,
        }
        aware_answers: list[float] = []
        unaware_answers: list[float] = []

        for item in TRIAL_ITEMS:
            trial1_value = number(first[item], item, participant_id, TRIAL_SCALE)
            trial2_value = number(second[item], item, participant_id, TRIAL_SCALE)
            aware_value = trial1_value if trial1_model == "gaze_aware" else trial2_value
            unaware_value = trial2_value if trial2_model == "gaze_unaware" else trial1_value
            output[f"trial1_{item}"] = trial1_value
            output[f"trial2_{item}"] = trial2_value
            output[f"aware_{item}"] = aware_value
            output[f"unaware_{item}"] = unaware_value
            output[f"aware_minus_unaware_{item}"] = aware_value - unaware_value
            aware_answers.append(aware_value)
            unaware_answers.append(unaware_value)
            paired_values[item].append((aware_value, unaware_value))

        output["gaze_aware_composite_mean"] = sum(aware_answers) / len(aware_answers)
        output["gaze_unaware_composite_mean"] = sum(unaware_answers) / len(unaware_answers)
        output["aware_minus_unaware_composite_mean"] = output["gaze_aware_composite_mean"] - output["gaze_unaware_composite_mean"]
        paired_values["composite_mean"] = paired_values.get("composite_mean", []) + [
            (output["gaze_aware_composite_mean"], output["gaze_unaware_composite_mean"])
        ]
        aware_matrix.append(aware_answers)
        unaware_matrix.append(unaware_answers)

        difference_code = number(second["UT02"], "UT02", participant_id, (1, 2))
        difference_noticed = "yes" if difference_code == 1 else "no"
        difference_counts[difference_noticed] += 1
        output["difference_noticed"] = difference_noticed
        output["difference_description"] = second.get("UT03_01", "")

        for item in COMPARISON_ITEMS:
            raw = optional_number(second[item], item, participant_id, COMPARISON_SCALE)
            output[f"{item}_raw_trial1_to_trial2"] = raw if raw is not None else ""
            if difference_noticed == "yes" and raw is None:
                raise ValueError(f"Participant {participant_id} bemerkte einen Unterschied, beantwortete aber {item} nicht.")
            if raw is None:
                output[f"{item}_aware_preference"] = ""
                continue
            # Positiv = Präferenz gaze-aware, negativ = Präferenz gaze-unaware.
            aware_preference = (4 - raw) if trial1_model == "gaze_aware" else (raw - 4)
            output[f"{item}_aware_preference"] = aware_preference
            if difference_noticed == "yes":
                comparison_values[item].append(aware_preference)

        processed_rows.append(output)
        ages.append(age)
        gender_counts[gender_code] += 1

    total_participants = len(processed_rows)
    result_rows: list[dict[str, object]] = []
    item_test_rows: list[dict[str, object]] = []
    for item, question in TRIAL_ITEMS.items():
        pairs = paired_values[item]
        aware = [pair[0] for pair in pairs]
        unaware = [pair[1] for pair in pairs]
        differences = [aware_value - unaware_value for aware_value, unaware_value in pairs]
        test = exact_wilcoxon_signed_rank(differences)
        row = {
            "analysis_section": "trial_ratings",
            "result_id": item,
            "question_text": question,
            "test_description": "Two-sided exact Wilcoxon signed-rank test: gaze-aware minus gaze-unaware",
            "n": len(pairs),
            "median_gaze_aware": median(aware),
            "iqr_gaze_aware": iqr(aware),
            "median_gaze_unaware": median(unaware),
            "iqr_gaze_unaware": iqr(unaware),
            "median_difference_aware_minus_unaware": median(differences),
            "n_nonzero_differences": test["n_nonzero"],
            "wilcoxon_w_plus": test["w_plus"],
            "wilcoxon_w_minus": test["w_minus"],
            "rank_biserial_correlation": test["rank_biserial"],
            "p_value_exact": test["p_value"],
            "note": "Positive values favour gaze-aware.",
        }
        item_test_rows.append(row)
        result_rows.append(row)
    holm_adjust(item_test_rows)

    composite_pairs = paired_values["composite_mean"]
    aware_composite = [pair[0] for pair in composite_pairs]
    unaware_composite = [pair[1] for pair in composite_pairs]
    composite_differences = [aware - unaware for aware, unaware in composite_pairs]
    composite_test = exact_wilcoxon_signed_rank(composite_differences)
    result_rows.append({
        "analysis_section": "trial_composite",
        "result_id": "composite_mean",
        "question_text": "Mean of all eight trial-rating items",
        "test_description": "Two-sided exact Wilcoxon signed-rank test: gaze-aware minus gaze-unaware",
        "n": len(composite_pairs),
        "median_gaze_aware": median(aware_composite),
        "iqr_gaze_aware": iqr(aware_composite),
        "median_gaze_unaware": median(unaware_composite),
        "iqr_gaze_unaware": iqr(unaware_composite),
        "median_difference_aware_minus_unaware": median(composite_differences),
        "n_nonzero_differences": composite_test["n_nonzero"],
        "wilcoxon_w_plus": composite_test["w_plus"],
        "wilcoxon_w_minus": composite_test["w_minus"],
        "rank_biserial_correlation": composite_test["rank_biserial"],
        "p_value_exact": composite_test["p_value"],
        "note": "Interpret only if the scale reliability is adequate. Positive values favour gaze-aware.",
    })

    result_rows.extend([
        {
            "analysis_section": "demographics",
            "result_id": "age_years",
            "question_text": "Age in years",
            "n": len(ages),
            "mean": sum(ages) / len(ages),
            "standard_deviation": stdev(ages),
            "minimum": min(ages),
            "maximum": max(ages),
            "note": "Sample standard deviation; age data are taken from Trial 1.",
        },
        {
            "analysis_section": "reliability",
            "result_id": "cronbach_alpha_gaze_aware",
            "question_text": "Internal consistency of the eight trial-rating items",
            "n": len(aware_matrix),
            "value": cronbach_alpha(aware_matrix),
            "note": "Cronbach's alpha for gaze-aware ratings.",
        },
        {
            "analysis_section": "reliability",
            "result_id": "cronbach_alpha_gaze_unaware",
            "question_text": "Internal consistency of the eight trial-rating items",
            "n": len(unaware_matrix),
            "value": cronbach_alpha(unaware_matrix),
            "note": "Cronbach's alpha for gaze-unaware ratings.",
        },
    ])
    for gender_code, count in sorted(gender_counts.items()):
        result_rows.append({
            "analysis_section": "demographics",
            "result_id": f"gender_response_code_{gender_code}",
            "question_text": "Reported gender (export code)",
            "n": count,
            "percentage": 100 * count / total_participants if total_participants else "",
            "note": "Use the questionnaire's response-label mapping to interpret this export code.",
        })

    comparison_test_rows: list[dict[str, object]] = []
    for item, question in COMPARISON_ITEMS.items():
        values = comparison_values[item]
        test = exact_wilcoxon_signed_rank(values)  # Test gegen den neutralen Wert 4.
        counts = Counter("aware" if value > 0 else "unaware" if value < 0 else "neutral" for value in values)
        row = {
            "analysis_section": "direct_comparisons",
            "result_id": item,
            "question_text": question,
            "test_description": "Two-sided exact Wilcoxon signed-rank test against the neutral midpoint; positive = gaze-aware",
            "n": len(values),
            "median_difference_aware_minus_unaware": median(values) if values else "",
            "n_nonzero_differences": test["n_nonzero"],
            "wilcoxon_w_plus": test["w_plus"],
            "wilcoxon_w_minus": test["w_minus"],
            "rank_biserial_correlation": test["rank_biserial"],
            "p_value_exact": test["p_value"],
            "n_prefer_gaze_aware": counts["aware"],
            "n_neutral": counts["neutral"],
            "n_prefer_gaze_unaware": counts["unaware"],
            "percent_prefer_gaze_aware": 100 * counts["aware"] / len(values) if values else "",
            "note": "Only participants who reported noticing a difference are included.",
        }
        comparison_test_rows.append(row)
        result_rows.append(row)
    holm_adjust(comparison_test_rows)

    result_rows.append({
        "analysis_section": "difference_detection",
        "result_id": "difference_noticed",
        "question_text": "Did the participant report noticing a difference between versions?",
        "n": total_participants,
        "n_prefer_gaze_aware": difference_counts["yes"],
        "n_prefer_gaze_unaware": difference_counts["no"],
        "percent_prefer_gaze_aware": 100 * difference_counts["yes"] / total_participants,
        "note": "n_prefer_gaze_aware means 'yes' here; n_prefer_gaze_unaware means 'no'.",
    })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    processed_fields = list(processed_rows[0])
    write_csv(args.output_dir / "subjective_questionnaire_processed.csv", processed_rows, processed_fields)
    write_csv(args.output_dir / "subjective_questionnaire_results.csv", result_rows, RESULT_FIELDS)
    codebook_rows = [
        {"variable": "participant_id", "description": "Anonymised participant ID used to pair trials."},
        {"variable": "age_years", "description": "Age in years, recorded in Trial 1."},
        {"variable": "gender_response_code", "description": "Unmodified gender response code from Trial 1."},
        {"variable": "order_group", "description": "aware_first for even IDs; unaware_first for odd IDs."},
        {"variable": "aware_TQ01_XX / unaware_TQ01_XX", "description": "Raw trial rating, 1–5. Higher values indicate stronger agreement."},
        {"variable": "aware_minus_unaware_TQ01_XX", "description": "Paired difference. Positive values favour gaze-aware."},
        {"variable": "UT01_XX_raw_trial1_to_trial2", "description": "Original 1–7 comparison rating: 1 favours Trial 1, 4 neutral, 7 favours Trial 2."},
        {"variable": "UT01_XX_aware_preference", "description": "Mapped comparison score: −3 strongly gaze-unaware to +3 strongly gaze-aware."},
        {"variable": "difference_noticed", "description": "yes/no response to UT02."},
        {"variable": "difference_description", "description": "Unmodified free-text response to UT03_01."},
    ]
    write_csv(args.output_dir / "subjective_questionnaire_codebook.csv", codebook_rows, ["variable", "description"])
    figures_dir = args.output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    results_by_id = {str(row["result_id"]): row for row in result_rows}
    trial_chart_path = figures_dir / "subjective_trial_ratings.svg"
    direct_chart_path = figures_dir / "subjective_direct_comparisons.svg"
    trial_table_path = args.output_dir / "subjective_trial_ratings_table.tex"
    direct_table_path = args.output_dir / "subjective_direct_comparisons_table.tex"
    write_trial_rating_chart(trial_chart_path, processed_rows, results_by_id)
    write_direct_comparison_chart(direct_chart_path, processed_rows, results_by_id)
    write_latex_trial_rating_table(trial_table_path, processed_rows, results_by_id)
    write_latex_direct_comparison_table(direct_table_path, processed_rows, results_by_id)

    print(f"Analysed {total_participants} paired participants.")
    print(f"Wrote: {args.output_dir / 'subjective_questionnaire_results.csv'}")
    print(f"Wrote: {args.output_dir / 'subjective_questionnaire_processed.csv'}")
    print(f"Wrote: {args.output_dir / 'subjective_questionnaire_codebook.csv'}")
    print(f"Wrote: {trial_chart_path}")
    print(f"Wrote: {direct_chart_path}")
    print(f"Wrote: {trial_table_path}")
    print(f"Wrote: {direct_table_path}")


if __name__ == "__main__":
    main()
