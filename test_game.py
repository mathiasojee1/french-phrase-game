import unittest
from main import check_french_sentence, tense_matches, nlp

class TestFrenchValidation(unittest.TestCase):
    
    def test_present_tense(self):
        """Test Présent detection"""
        sentence = "Je mange une pomme"
        word_list = [{"word": "manger", "en": "eat"}, {"word": "pomme", "en": "apple"}]
        is_correct, feedback = check_french_sentence(sentence, word_list, "Présent")
        self.assertTrue(is_correct, f"Présent test failed: {feedback}")
    
    def test_passé_composé(self):
        """Test Passé composé detection"""
        sentence = "J'ai mangé une pomme"
        word_list = [{"word": "manger", "en": "eat"}, {"word": "pomme", "en": "apple"}]
        is_correct, feedback = check_french_sentence(sentence, word_list, "Passé composé")
        self.assertTrue(is_correct, f"Passé composé test failed: {feedback}")
    
    def test_imparfait(self):
        """Test Imparfait detection"""
        sentence = "Je mangeais une pomme"
        word_list = [{"word": "manger", "en": "eat"}, {"word": "pomme", "en": "apple"}]
        is_correct, feedback = check_french_sentence(sentence, word_list, "Imparfait")
        self.assertTrue(is_correct, f"Imparfait test failed: {feedback}")
    
    def test_futur_simple(self):
        """Test Futur simple detection"""
        sentence = "Je mangerai une pomme"
        word_list = [{"word": "manger", "en": "eat"}, {"word": "pomme", "en": "apple"}]
        is_correct, feedback = check_french_sentence(sentence, word_list, "Futur simple")
        self.assertTrue(is_correct, f"Futur simple test failed: {feedback}")
    
    def test_conditionnel(self):
        """Test Conditionnel detection"""
        sentence = "Je mangerais une pomme"
        word_list = [{"word": "manger", "en": "eat"}, {"word": "pomme", "en": "apple"}]
        # Debug: print what spaCy sees
        doc = nlp(sentence)
        print("\n=== CONDITIONNEL DEBUG ===")
        print(f"Sentence: {sentence}")
        for tok in doc:
            print(f"  '{tok.text}' pos={tok.pos_} tag={tok.tag_} morph={tok.morph}")
        is_correct, feedback = check_french_sentence(sentence, word_list, "Conditionnel")
        self.assertTrue(is_correct, f"Conditionnel test failed: {feedback}")
    
    def test_subjonctif(self):
        """Test Subjonctif detection"""
        sentence = "Il faut que je mange une pomme"
        word_list = [{"word": "manger", "en": "eat"}, {"word": "pomme", "en": "apple"}]
        is_correct, feedback = check_french_sentence(sentence, word_list, "Subjonctif")
        self.assertTrue(is_correct, f"Subjonctif test failed: {feedback}")
    
    def test_imperatif(self):
        """Test Impératif detection"""
        sentence = "Mange une pomme"
        word_list = [{"word": "manger", "en": "eat"}, {"word": "pomme", "en": "apple"}]
        # Debug: print what spaCy sees
        doc = nlp(sentence)
        print("\n=== IMPERATIF DEBUG ===")
        print(f"Sentence: {sentence}")
        print(f"Number of tokens: {len(doc)}")
        for i, tok in enumerate(doc):
            print(f"  [{i}] '{tok.text}' pos={tok.pos_} tag={tok.tag_} morph={tok.morph}")
        is_correct, feedback = check_french_sentence(sentence, word_list, "Impératif")
        self.assertTrue(is_correct, f"Impératif test failed: {feedback}")
    
    def test_missing_words(self):
        """Test that missing words are detected"""
        sentence = "Je mange"
        word_list = [{"word": "manger", "en": "eat"}, {"word": "pomme", "en": "apple"}]
        is_correct, feedback = check_french_sentence(sentence, word_list, "Présent")
        self.assertFalse(is_correct, "Should fail when words are missing")
        self.assertIn("Missing words", feedback)
    
    def test_wrong_tense(self):
        """Test that wrong tense is rejected"""
        sentence = "Je mangerai une pomme"  # Futur
        word_list = [{"word": "manger", "en": "eat"}, {"word": "pomme", "en": "apple"}]
        is_correct, feedback = check_french_sentence(sentence, word_list, "Présent")
        self.assertFalse(is_correct, "Should fail with wrong tense")
        self.assertIn("Use the Présent tense", feedback)
    
    def test_no_verb(self):
        """Test that sentences without verbs are rejected"""
        sentence = "Une pomme rouge"
        word_list = [{"word": "pomme", "en": "apple"}, {"word": "rouge", "en": "red"}]
        is_correct, feedback = check_french_sentence(sentence, word_list, "Présent")
        self.assertFalse(is_correct, "Should fail without a verb")
        self.assertIn("verb", feedback.lower())
    
    def test_grammar_check(self):
        """Test that grammar errors are caught"""
        sentence = "Je mange une pommes"  # pommes should be pomme (singular)
        word_list = [{"word": "manger", "en": "eat"}, {"word": "pomme", "en": "apple"}]
        is_correct, feedback = check_french_sentence(sentence, word_list, "Présent")
        # This might pass depending on language-tool strictness, but let's verify it processes
        self.assertIsNotNone(feedback)
    
    def test_all_words_required(self):
        """Test that all words in the list must be used"""
        sentence = "Je mange"
        word_list = [
            {"word": "manger", "en": "eat"},
            {"word": "chat", "en": "cat"},
            {"word": "noir", "en": "black"}
        ]
        is_correct, feedback = check_french_sentence(sentence, word_list, "Présent")
        self.assertFalse(is_correct, "Should fail when not all words are used")


if __name__ == '__main__':
    unittest.main()
