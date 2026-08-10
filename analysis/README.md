# Auswertung

## 1. Einzelne Aufzeichnung auswerten

Für jede `*_samples.csv`-Datei:

```bash
python3 analysis/analyze_gaze_aversion.py Processing/BA_eyes_ft/data/P01_20260810_120000_samples.csv --out-dir analysis/individual_results
```

Das erzeugt pro Aufzeichnung vier Dateien: Zustands-Episoden, Interaktions-Episoden, Aversion-Metriken und Interaktions-Metriken.

Die Interaktionsdefinitionen sind:

- `user_looks_at_avatar`: Der Blick liegt in der konfigurierten Mutual-Gaze-Fläche.
- `avatar_looks_at_user`: Die Pupillen liegen innerhalb der konfigurierten Zentrierungstoleranz.
- `mutual_gaze`: Beide Bedingungen gelten gleichzeitig.

Neue Aufzeichnungen enthalten dafür die Sample-Spalte `agent_looks_at_user`. Bei älteren Aufzeichnungen bleibt die Avatar- und Mutual-Gaze-Auswertung bewusst leer, statt falsche Werte zu erzeugen.

## 2. Gesamte Studie auswerten

Lege alle Ergebnisse der Einzelanalyse in einen gemeinsamen Ordner, beispielsweise `analysis/individual_results`, und führe aus:

```bash
python3 analysis/aggregate_study_results.py analysis/individual_results --out-dir analysis/study_results
```

Das Skript erzeugt:

- `participant_condition_metrics.csv`: eine Zeile pro Person und Modell.
- `condition_summary.csv`: Mittelwert und Standardabweichung pro Modell und Metrik.
- `paired_condition_tests.csv`: gepaarter Vergleich `GAZE_AWARE - GAZE_UNAWARE`, Effektstärke `Cohen's dz`, unkorriertes `p` und Holm-korrigiertes `p`.

Der Signifikanztest ist ein gepaarter Permutationstest. Das passt zum Within-Subject-Design, weil jede Person beide Modelle erlebt. Die Holm-Korrektur berücksichtigt, dass mehrere Metriken gleichzeitig geprüft werden.
