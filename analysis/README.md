# Auswertung

Die Gesamtauswertung benötigt SciPy. Mit Anaconda kann die Abhängigkeit beispielsweise wie folgt installiert werden:

```bash
python3 -m pip install -r analysis/requirements.txt
```

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
- `aversion_incidence_summary.csv`: Anzahl und Anteil der Personen mit mindestens einer Blickaversion pro Modell.
- `paired_condition_tests.csv`: gepaarter Vergleich `GAZE_AWARE - GAZE_UNAWARE`, Effektstärke `Cohen's dz` sowie Ergebnisse des Permutations- und des gepaarten t-Tests.
- `figures/interaction_proportion_time.svg`: Anteil der Zeit für die drei Interaktionszustände.
- `figures/interaction_mean_episode_duration.svg`: mittlere Episodendauer für die drei Interaktionszustände.
- `figures/interaction_episode_rate.svg`: Episodenrate für die drei Interaktionszustände.
- `figures/gaze_aversion_rate.svg`: Blickaversionen pro Minute.
- `figures/gaze_aversion_mean_duration.svg`: mittlere Dauer der Blickaversionen.
- `figures/gaze_aversion_rate_boxplot.svg`: Verteilung der individuellen Aversion-Raten.
- `figures/gaze_aversion_mean_duration_boxplot.svg`: Verteilung der individuellen mittleren Aversion-Dauern.

Für jede Metrik berechnet das Skript einen zweiseitigen gepaarten Permutationstest und einen zweiseitigen gepaarten t-Test. Der t-Test wird mit `scipy.stats.ttest_rel` durchgeführt. Beide Tests passen zum Within-Subject-Design, weil jede Person beide Modelle erlebt. Die Holm-Korrektur wird getrennt für die p-Werte beider Testfamilien berechnet.

Die Spalten `p_value_permutation_raw` und `p_value_permutation_holm` enthalten die unkorrierten beziehungsweise Holm-korrigierten p-Werte des Permutationstests. Die Spalten `p_value_t_test_raw` und `p_value_t_test_holm` enthalten die entsprechenden p-Werte des gepaarten t-Tests. `t_statistic` und `t_degrees_of_freedom` dokumentieren zusätzlich die Teststatistik und Freiheitsgrade des t-Tests.

Bei null Blickaversionen werden aversionsbezogene Dauerkennwerte, beispielsweise `mean_aversion_duration_ms`, als fehlend gespeichert. Ein Wert von `0` bleibt ausschließlich für Kennwerte sinnvoll, bei denen null eine reale Beobachtung bedeutet, etwa `gaze_aversion_rate_per_minute` oder `total_aversion_duration_ms`. Dadurch beschreibt die mittlere Aversiondauer ausschließlich die Dauer tatsächlich beobachteter Aversionen.

Die Diagramme sind skalierbare SVG-Dateien. Jeder Balken zeigt den Mittelwert eines Modells, jeder Fehlerbalken die Standardabweichung.
