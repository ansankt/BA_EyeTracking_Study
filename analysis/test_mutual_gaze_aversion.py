import unittest

import mutual_gaze_aversion as aversion
from aggregate_study_results import aggregate_participant_condition_rows


def samples(*states):
    return [dict(participant_id="P1", trial_id=1, condition="GAZE_AWARE",
                 timestamp_ms=i * 1000, gaze_state=state,
                 gaze_valid=state != "INVALID") for i, state in enumerate(states)]


class MutualAversionTests(unittest.TestCase):
    def test_completed_face_and_away_are_one_episode(self):
        metrics, episodes = aversion.analyze(samples(
            "MUTUAL_GAZE", "LOOKING_AT_FACE", "LOOKING_AWAY", "LOOKING_AT_EYES"))
        self.assertEqual(metrics[aversion.FIELDS[0]], 1)
        self.assertEqual(metrics[aversion.METRICS[0][0]], 0.333333)
        self.assertEqual(metrics[aversion.METRICS[1][0]], 1)
        self.assertEqual(metrics[aversion.METRICS[2][0]], 2000)
        self.assertEqual(episodes[0]["end_reason"], "return_to_eyes")

    def test_only_direct_mutual_transition(self):
        for states in (
            ("LOOKING_AT_EYES", "LOOKING_AWAY"),
            ("MUTUAL_GAZE", "LOOKING_AT_EYES", "LOOKING_AWAY"),
            ("MUTUAL_GAZE", "INVALID", "LOOKING_AWAY"),
            ("LOOKING_AWAY", "MUTUAL_GAZE"),
        ):
            with self.subTest(states=states):
                metrics, episodes = aversion.analyze(samples(*states))
                self.assertEqual(episodes, [])
                self.assertIsNone(metrics[aversion.METRICS[2][0]])

    def test_censoring(self):
        for end, reason in (("INVALID", "tracking_loss_or_unknown"),
                            ("LOOKING_AWAY", "trial_end")):
            metrics, episodes = aversion.analyze(samples("MUTUAL_GAZE", "LOOKING_AWAY", end))
            self.assertEqual(metrics["mutual_gaze_aversion_count"], 1)
            self.assertEqual(metrics["mutual_gaze_aversion_censored_count"], 1)
            self.assertIsNone(metrics[aversion.METRICS[2][0]])
            self.assertIsNone(episodes[0]["duration_ms"])
            self.assertEqual(episodes[0]["end_reason"], reason)

    def test_no_exposure(self):
        metrics, _ = aversion.analyze(samples("LOOKING_AT_EYES", "LOOKING_AWAY"))
        self.assertEqual(metrics[aversion.METRICS[0][0]], 0)
        self.assertIsNone(metrics[aversion.METRICS[1][0]])

    def test_aggregate_pools_counts_not_means(self):
        rows = []
        for states in (("MUTUAL_GAZE", "LOOKING_AWAY", "LOOKING_AT_EYES"),
                       ("MUTUAL_GAZE", "LOOKING_AWAY", "LOOKING_AWAY", "LOOKING_AT_EYES")):
            metrics, _ = aversion.analyze(samples(*states))
            rows.append(dict(metrics, participant_id="P1", condition="GAZE_AWARE",
                             source_session="test", trial_duration_ms=(len(states)-1)*1000))
        result = aggregate_participant_condition_rows(rows)[0]
        self.assertEqual(result[aversion.METRICS[0][0]], 0.4)
        self.assertEqual(result[aversion.METRICS[1][0]], 1)
        self.assertEqual(result[aversion.METRICS[2][0]], 1500)
        del rows[0]["mutual_gaze_aversion_count"]
        result = aggregate_participant_condition_rows(rows)[0]
        self.assertIsNone(result[aversion.METRICS[0][0]])


if __name__ == "__main__":
    unittest.main()
