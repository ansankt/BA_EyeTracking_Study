# Auswertung

## Separate Mutual-Gaze-Aversion

Die bisherige allgemeine Aversion bleibt unveraendert. Zusaetzlich werden nur
direkte Uebergaenge vom geloggten `MUTUAL_GAZE` nach `LOOKING_AT_FACE` oder
`LOOKING_AWAY` als Mutual-Gaze-Aversion gewertet. Ein zwischenzeitliches
`LOOKING_AT_EYES` schliesst diese Zuordnung aus. Damit wird ein Ende des
Mutual Gaze allein durch die gezeichneten Augen nicht als Nutzeraversion gezählt.
Es wird der klassifizierte Blickzustand verwendet, nicht der Controller-Modus.

- `mutual_gaze_aversion_rate_per_second`: Anzahl / gesamte beobachtete Trialzeit in Sekunden.
- `mutual_gaze_aversion_rate_per_mutual_gaze_second`: Anzahl / beobachtete Zeit im gueltigen Zustand `MUTUAL_GAZE` in Sekunden. Ohne diese Exposition bleibt der Wert leer.
- `mean_mutual_gaze_aversion_duration_ms`: Mittelwert ausschliesslich abgeschlossener Aversionen bis zur Rueckkehr nach `LOOKING_AT_EYES` oder `MUTUAL_GAZE`. Ohne abgeschlossene Episode bleibt der Wert leer.

Wechsel zwischen Gesicht und ausserhalb bleiben Teil derselben Aversion.
Trackingverlust, unbekannte Zustaende und Trialende beenden eine Episode als
zensiert: Der beobachtete Beginn zaehlt fuer die Rate, die unvollstaendige Dauer
geht nicht in den Mittelwert ein. Die neue Datei
`*_mutual_gaze_aversion_episodes.csv` dokumentiert Endgrund, Abschlussstatus und
beobachtete Dauer. Samples gelten bis zum folgenden Zeitstempel; es wird keine
zusaetzliche Glaettung oder zeitliche Lueckenschwelle eingefuehrt.

Bei mehreren Trials pro Person und Bedingung werden Anzahlen und Zeiten zuerst
summiert, dann die Kennzahlen berechnet. Alte Ausgaben ohne neue Spalten liefern
fehlende Werte statt scheinbarer Nullwerte und sollten erneut ausgewertet werden.
Die Gesamtauswertung erstellt fuer jede der drei Kennzahlen ein separates
Säulendiagramm (M und SD) und einen Boxplot mit vollstaendigen Personenpaaren.
Die Saeulendiagramme verwenden alle jeweils verfuegbaren Personen pro Bedingung.
Gepaarte Tests verwenden nur vollstaendige Paare der jeweiligen Kennzahl.
Signifikanzsterne beziehen sich weiterhin auf den unkorrigierten gepaarten t-Test.
Die zusaetzlich exportierte Holm-Korrektur umfasst jetzt alle 14 Metriken;
dadurch koennen sich auch bisherige korrigierte p-Werte aendern.

Regressionstests: `python3 -B -m unittest discover -s analysis -p 'test_mutual_gaze_aversion.py'`.

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

Bei null Blickaversionen werden aversionsbezogene Dauerkennwerte, beispielsweise `mean_aversion_duration_ms`, als fehlend gespeichert. Ein Wert von `0` bleibt ausschließlich für Kennwerte sinnvoll, bei denen null eine reale Beobachtung bedeutet, etwa `gaze_aversion_rate_per_second` oder `total_aversion_duration_ms`. Dadurch beschreibt die mittlere Aversiondauer ausschließlich die Dauer tatsächlich beobachteter Aversionen.

Episoden- und Blickaversionraten werden als Ereignisse pro Sekunde gespeichert (`*_episode_rate_per_second`, `gaze_aversion_rate_per_second`).

Die Diagramme sind skalierbare SVG-Dateien. Jeder Balken zeigt den Mittelwert eines Modells, jeder Fehlerbalken die Standardabweichung.

Sternmarker in den Diagrammen beruhen auf den unkorrierten p-Werten des gepaarten t-Tests: `* p < .05`, `** p < .01`, `*** p < .001`. Sie dienen der schnellen visuellen Einordnung und ersetzen nicht die Holm-korrigierten p-Werte in `paired_condition_tests.csv`.
