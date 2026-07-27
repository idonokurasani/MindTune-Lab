import unittest
from pathlib import Path

APP_JS = Path(__file__).resolve().parents[1] / "app.js"


class FrontendContractTests(unittest.TestCase):
    def test_conjugation_domino_keeps_the_same_verb(self):
        source = APP_JS.read_text(encoding="utf-8")

        self.assertIn(
            "const verb = previousStep?.verb || randomItem(activeConjugationVerbs());", source
        )
        self.assertIn("const previousEntry = previousStep?.target || null;", source)
        self.assertIn("nextConjugationDominoStep(conjugationDomino)", source)
        self.assertNotIn("nextConjugationDominoStep(previousTarget)", source)

    def test_conjugation_accepts_modern_future_feminine_plural_forms(self):
        source = APP_JS.read_text(encoding="utf-8")

        self.assertIn('const modernSourcePerson = { "אתן": "אתם", "הן": "הם" }[personHe];', source)
        self.assertIn("verb.targets[`בעתיד · ${modernSourcePerson}`]", source)
        self.assertIn('uniqueConjugationForms([modernForm, pealimForm]).join("|")', source)
        self.assertIn("function conjugationAcceptedPhrases", source)

    def test_hebrew_recovery_replaces_flashcards_as_the_active_course(self):
        source = APP_JS.read_text(encoding="utf-8")

        preset_block = source[
            source.index("memory: {") : source.index("piano: {", source.index("memory: {"))
        ]
        startup_block = source[source.index("populateFamilies();") :]
        self.assertIn('id: "hebrew_recovery"', preset_block)
        self.assertIn("hebrew: true", preset_block)
        self.assertNotIn("flashcards: true", preset_block)
        self.assertNotIn('id: "hebrew_flashcards"', preset_block)
        self.assertNotIn("loadFlashcardCatalog();", startup_block)
        self.assertIn('if (preset.id === "hebrew_recovery")', source)
        self.assertIn("startHebrewRecoveryFlow();", source)
        self.assertIn('phase: "preview"', source)
        self.assertIn('phase = "activation"', source)
        self.assertIn('phase = "lexical"', source)
        self.assertIn('phase = "domino"', source)
        self.assertIn('phase = "comprehension"', source)
        self.assertIn('phase = "reentry"', source)
        self.assertIn('phase = "complete"', source)
        self.assertIn("before_accuracy:", source)
        self.assertIn("after_accuracy:", source)

    def test_recovery_domino_is_hidden_until_preflight_finishes(self):
        source = APP_JS.read_text(encoding="utf-8")

        self.assertIn('hebrewRecoveryFlow?.phase === "domino"', source)
        self.assertIn("els.conjugationWorkspace.hidden = false;", source)
        self.assertIn("els.conjugationWorkspace.hidden = true;", source)
        self.assertIn(
            'if (preset.id === "hebrew_recovery") {\n    startHebrewRecoveryFlow();', source
        )

    def test_recovery_events_keep_before_work_and_after_separate(self):
        source = APP_JS.read_text(encoding="utf-8")

        self.assertIn("reentryResults: []", source)
        self.assertIn("if (trial.reentry) flow.reentryResults.push(result);", source)
        self.assertIn('"hebrew_recovery_activation_response"', source)
        self.assertIn('"hebrew_recovery_lexical_response"', source)
        self.assertIn('"hebrew_recovery_comprehension_response"', source)
        self.assertIn('"hebrew_recovery_reentry_response"', source)

    def test_recovery_errors_show_the_expected_answer_before_advancing(self):
        source = APP_JS.read_text(encoding="utf-8")

        self.assertIn("function showRecoveryAnswerFeedback", source)
        self.assertIn("Risposta corretta:", source)
        self.assertIn("La correzione resta visibile. Premi Invio oppure Continua.", source)
        self.assertNotIn("window.setTimeout(renderRecoveryLexicalTrial, 250)", source)
        self.assertNotIn("window.setTimeout(renderRecoveryComprehensionTrial, 250)", source)

    def test_recovery_sources_use_server_summary_label(self):
        source = APP_JS.read_text(encoding="utf-8")

        self.assertIn("const sourceLabel = evidence.resources_label", source)
        self.assertIn("fonti operative", source)
        self.assertNotIn("fonti pronte", source)

    def test_unvalidated_games_are_not_offered_as_scientific_tasks(self):
        source = APP_JS.read_text(encoding="utf-8")

        apk_block = source[
            source.index("apk_lab: {") : source.index("memory: {", source.index("apk_lab: {"))
        ]
        self.assertIn('label: "Test cognitivi"', apk_block)
        self.assertNotIn("apk_stability_balloon", apk_block)
        self.assertNotIn("apk_airballoon", apk_block)
        self.assertNotIn("apk_starship", apk_block)
        self.assertNotIn("apk_hand_eye", apk_block)
        self.assertNotIn("apk_treasure_tracker", apk_block)


if __name__ == "__main__":
    unittest.main()
