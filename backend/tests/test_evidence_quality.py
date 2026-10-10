"""
Evidence Quality & Regression Test Suite for VERITO

Tests:
1. Regression scenario: Rumor / death hoax evidence MUST NOT be classified as SUPPORTING.
2. Questions, rumors, and biographical mentions must be treated as IRRELEVANT or CONTRADICTING.
3. Repetition of claim keywords does NOT count as corroboration.
4. Heuristic and synthesized analysis standards on sensitive claims (deaths, disasters).
5. Safe inconclusive verdicts when evidence is ambiguous or unverified.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evidence_classifier import _local_fallback_classify, _rating_classification
from analyzer import _heuristic_analysis, synthesize_analysis


class TestEvidenceQualityRegression(unittest.TestCase):
    """
    REGRESSION TEST:
    In a previous test, all 10 results were classified as supporting a sensitive death claim.
    This test verifies that:
    1. Rumors, questions, and clickbait are NOT classified as supporting.
    2. Hoax/debunked articles are classified as contradicting.
    3. The overall verdict is NOT 'supported'.
    """

    def setUp(self):
        self.death_claim = "Actor Morgan Freeman died in a tragic car accident today."

        # Realistic search results when a death rumor circulates
        self.death_rumor_results = [
            {
                "title": "Morgan Freeman death hoax debunked: Actor is alive and well",
                "source": "factcheck.org",
                "url": "https://factcheck.org/freeman-hoax",
                "snippet": "A viral Facebook post claiming Morgan Freeman passed away is completely false. The actor's representative confirmed he is in good health.",
            },
            {
                "title": "Did Morgan Freeman die? Viral rumors spread online",
                "source": "newsweek.com",
                "url": "https://newsweek.com/morgan-freeman-death-rumors",
                "snippet": "Fans were alarmed after a viral TikTok claim suggested the Oscar-winning star had passed away. However, no credible sources have reported any incident.",
            },
            {
                "title": "Morgan Freeman Death Rumors Denied by Representative",
                "source": "tmz.com",
                "url": "https://tmz.com/freeman-rep-denies",
                "snippet": "Representatives for Morgan Freeman officially refuted online death reports, calling them an internet hoax.",
            },
            {
                "title": "Fans mourn Morgan Freeman after viral social media post",
                "source": "celebritygossip.net",
                "url": "https://celebritygossip.net/freeman-post",
                "snippet": "Thousands of fans reacted to a trending post alleging that Morgan Freeman died in an accident.",
            },
            {
                "title": "Is Morgan Freeman in hospital? What we know",
                "source": "entertainmentweekly.com",
                "url": "https://ew.com/freeman-rumor-check",
                "snippet": "Unconfirmed rumors claimed the star suffered a car crash, but authorities have reported no such accident.",
            },
            {
                "title": "Morgan Freeman biography, movies, and career milestones",
                "source": "biography.com",
                "url": "https://biography.com/morgan-freeman",
                "snippet": "Morgan Freeman was born in Memphis, Tennessee and won the Academy Award for Million Dollar Baby.",
            },
            {
                "title": "Shock as viral video claims Morgan Freeman has passed away",
                "source": "youtube.com",
                "url": "https://youtube.com/watch?v=123",
                "snippet": "A trending video claiming the beloved actor died today has sparked concern among fans.",
            },
            {
                "title": "Morgan Freeman recent projects and upcoming releases",
                "source": "imdb.com",
                "url": "https://imdb.com/name/nm0000151",
                "snippet": "Explore Morgan Freeman's latest film and television roles scheduled for release this year.",
            },
            {
                "title": "Internet death hoaxes: Why celebrities are falsely reported dead",
                "source": "theverge.com",
                "url": "https://theverge.com/death-hoaxes",
                "snippet": "How fake news algorithms amplify celebrity death hoaxes on social media platforms.",
            },
            {
                "title": "Morgan Freeman quote on life and aging",
                "source": "quotes.com",
                "url": "https://quotes.com/freeman",
                "snippet": "Inspiring words from Morgan Freeman on living life with purpose and gratitude.",
            },
        ]

    def test_regression_death_rumors_not_all_supporting(self):
        """
        REGRESSION CHECK:
        Under no circumstances should the 10 rumor results be classified as supporting!
        """
        supporting, contradicting = _local_fallback_classify(
            self.death_claim,
            self.death_rumor_results,
        )

        # There must be ZERO supporting items because none of the items affirmatively confirm death!
        self.assertEqual(
            len(supporting),
            0,
            f"Expected 0 supporting items for death rumor, got {len(supporting)}: {[i['title'] for i in supporting]}",
        )

        # Hoax/debunking articles MUST be classified as contradicting
        self.assertGreater(
            len(contradicting),
            0,
            "Expected debunking/hoax reports to be classified as contradicting",
        )

    def test_verdict_for_death_rumor_is_not_supported(self):
        """
        The synthesis for the death rumor must NEVER be 'supported'.
        It must be 'contradicted' (since debunking sources are present) or 'inconclusive'.
        """
        supporting, contradicting = _local_fallback_classify(
            self.death_claim,
            self.death_rumor_results,
        )

        result = _heuristic_analysis(self.death_claim, supporting, contradicting)
        status = result["status"]

        self.assertNotEqual(
            status,
            "supported",
            "A false death rumor must NEVER receive a 'supported' verdict!",
        )
        self.assertIn(status, ["contradicted", "inconclusive"])

    def test_single_unverified_source_on_sensitive_claim_is_inconclusive(self):
        """A single uncorroborated source for a sensitive claim must be inconclusive."""
        single_supporting = [{
            "title": "Local blog says mayor was arrested",
            "source": "randomblog.com",
            "url": "https://randomblog.com/1",
            "snippet": "Unverified reports say the mayor was arrested.",
        }]
        result = _heuristic_analysis("Mayor of Metropolis was arrested today", single_supporting, [])
        self.assertEqual(result["status"], "inconclusive")

    def test_corroborated_non_sensitive_claim_is_supported(self):
        """Two independent sources corroborating a non-sensitive claim yields 'supported'."""
        multi_supporting = [
            {
                "title": "NASA announces new Mars rover discovery",
                "source": "reuters.com",
                "url": "https://reuters.com/nasa-mars",
                "snippet": "NASA confirmed the discovery of organic molecules in a crater on Mars.",
            },
            {
                "title": "Scientists confirm organic findings on Mars",
                "source": "bbc.com",
                "url": "https://bbc.com/science-mars",
                "snippet": "Independent scientists verified the data published by the space agency.",
            },
        ]
        result = _heuristic_analysis("NASA found organic molecules on Mars", multi_supporting, [])
        self.assertEqual(result["status"], "supported")

    def test_no_evidence_is_inconclusive(self):
        """Zero evidence yields 'inconclusive'."""
        result = _heuristic_analysis("Aliens landed in Central Park", [], [])
        self.assertEqual(result["status"], "inconclusive")

    def test_explicit_fact_check_ratings(self):
        """Fact check ratings are correctly classified."""
        true_item = {"_textual_rating": "Correct"}
        false_item = {"_textual_rating": "Pants on Fire"}
        misleading_item = {"_textual_rating": "Misleading"}
        unproven_item = {"_textual_rating": "Unproven"}

        self.assertEqual(_rating_classification(true_item), "supporting")
        self.assertEqual(_rating_classification(false_item), "contradicting")
        self.assertEqual(_rating_classification(misleading_item), "contradicting")
        self.assertIsNone(_rating_classification(unproven_item))


if __name__ == '__main__':
    unittest.main(verbosity=2)
