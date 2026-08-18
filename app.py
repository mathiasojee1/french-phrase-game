import streamlit as st
import random
import spacy
import language_tool_python
import re
import json

# Page configuration
st.set_page_config(
    page_title="French Phrase Game",
    page_icon="🇫🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #c9d1d9;
    }
    .stButton>button {
        background-color: #1f6aa5;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #0d47a1;
    }
    .word-card {
        background-color: #35353f;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        color: #1f6aa5;
    }
    .success-feedback {
        color: #2ecc71;
        font-weight: bold;
    }
    .error-feedback {
        color: #e74c3c;
        font-weight: bold;
    }
    .info-feedback {
        color: #3498db;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Load spaCy and language tool
nlp = spacy.load("fr_core_news_sm")
tool = language_tool_python.LanguageToolPublicAPI('fr')
PARTICIPLE_RE = re.compile(r".*(é|ée|és|ées|i|is|it|u|us|ut|ant|onné|ée)$", re.IGNORECASE)

# Word lists
WORD_LISTS = {
    "Easy": [
        {"word": "chat", "en": "cat"},
        {"word": "maison", "en": "house"},
        {"word": "soleil", "en": "sun"},
        {"word": "chien", "en": "dog"},
        {"word": "eau", "en": "water"},
    ],
    "Medium": [
        {"word": "manger", "en": "eating"},
        {"word": "grand", "en": "big"},
        {"word": "dormir", "en": "sleeping"},
        {"word": "ville", "en": "city"},
        {"word": "nuit", "en": "night"},
    ],
    "Hard": [
        {"word": "magnifique", "en": "magnificent"},
        {"word": "extraordinaire", "en": "extraordinary"},
        {"word": "néanmoins", "en": "nevertheless"},
        {"word": "splendide", "en": "splendid"},
        {"word": "délicieux", "en": "delicious"},
    ],
}

TENSES = [
    "Présent",
    "Imparfait",
    "Passé composé",
    "Futur simple",
    "Conditionnel",
    "Impératif",
    "Subjonctif"
]


def is_likely_verb(token_text):
    """Check if a token is likely to be a verb form."""
    common_verbs = {
        "manger", "aller", "venir", "voir", "faire", "dire", "prendre",
        "laisser", "pouvoir", "vouloir", "devoir", "savoir", "avoir", "être",
        "parler", "donner", "travailler", "penser", "chercher", "porter",
        "dormir", "sortir", "partir", "arriver", "demander", "entendre",
        "finir", "remplir", "servir", "tenir", "venir", "trouver",
        "croire", "connaitre", "suivre", "jouer", "perdre", "courir",
        "tomber", "comprendre", "mettre", "commencer", "appeler", "revenir",
        "lever", "asseoir", "coucher", "laver", "habiller", "habiter",
        "aimer", "adorer", "oublier", "apprendre", "enseigner", "montrer",
        "ouvrir", "fermer", "casser", "garder", "passer", "rester",
        "mangé", "allé", "venu", "vu", "fait", "dit", "pris",
        "mange", "manges", "mangeons", "mangez", "mangent",
        "va", "vas", "allons", "allez", "vont",
        "viens", "venons", "venez", "viennent",
        "vois", "voit", "voyons", "voyez", "voient",
    }
    
    text_lower = token_text.lower()
    if text_lower in common_verbs:
        return True
    
    if text_lower.endswith(("er", "ir", "oir", "re")):
        return True
    if text_lower.endswith(("ais", "ait", "aient", "ions", "iez")):
        return True
    if text_lower.endswith(("ai", "as", "ons", "ez")):
        return True
    
    return False


def get_verb_infinitive(token_text):
    """Convert a conjugated verb to infinitive."""
    text_lower = token_text.lower()
    
    if text_lower in {"manger", "aller", "venir", "voir", "faire", "dire", "prendre"}:
        return text_lower
    
    if text_lower.endswith("e") and len(text_lower) > 1:
        base = text_lower[:-1]
        if base + "er" in {"manger", "aller", "parler", "donner", "travailler", "penser"}:
            return base + "er"
    
    if text_lower.endswith("es") and len(text_lower) > 2:
        base = text_lower[:-2]
        if base + "er" in {"manger", "aller", "parler", "donner", "travailler"}:
            return base + "er"
    
    if text_lower.endswith("ons") and len(text_lower) > 3:
        base = text_lower[:-3]
        if base + "er" in {"manger", "aller", "parler"}:
            return base + "er"
    
    return None


def tense_matches(token, required_tense, doc=None):
    """Robust tense/mood detection."""
    morph = token.morph
    tense_vals = morph.get("Tense") or []
    mood_vals = morph.get("Mood") or []
    verbform_vals = morph.get("VerbForm") or []
    tag = getattr(token, "tag_", "") or ""
    pos = getattr(token, "pos_", "") or ""
    text = token.text.lower()
    lemma = token.lemma_.lower()

    def has(attr_list, value):
        return value in attr_list if attr_list else False

    if required_tense == "Présent":
        return has(tense_vals, "Pres") or ("Pres" in tag)
    
    if required_tense == "Imparfait":
        return has(tense_vals, "Imp") or ("Imp" in tag)
    
    if required_tense == "Futur simple":
        return has(tense_vals, "Fut") or ("Fut" in tag)
    
    if required_tense == "Conditionnel":
        if has(mood_vals, "Cnd") or ("Cnd" in tag):
            return True
        if has(verbform_vals, "Fin") and ("ais" in text or "rait" in text or "rais" in text):
            return True
        return False
    
    if required_tense == "Subjonctif":
        if has(mood_vals, "Sub") or ("Sub" in tag):
            return True
        if has(verbform_vals, "Fin") and ("e" in text or "es" in text or "ent" in text):
            if doc is not None:
                sent_text = doc.text.lower()
                if "que" in sent_text or "faut" in sent_text:
                    return True
        return False
    
    if required_tense == "Impératif":
        if has(mood_vals, "Imp") or ("Imp" in tag):
            return True
        if doc is not None and token.i == 0:
            if is_likely_verb(token.text):
                return True
        if doc is not None and token.i == 0 and is_likely_verb(lemma):
            return True
        if doc is not None:
            for tok in doc:
                if getattr(tok, "pos_", "") in ("VERB", "AUX"):
                    if tok.i == 0:
                        return True
        if pos == "VERB" and has(verbform_vals, "Fin"):
            if not has(mood_vals, "Cnd") and not has(mood_vals, "Sub"):
                if doc is not None and token.i is not None:
                    prev_has_pron = any(t.pos_ == "PRON" and t.i < token.i for t in doc)
                    if not prev_has_pron:
                        return True
        return False

    if required_tense == "Passé composé":
        if doc is None:
            return False
        auxiliaries = {"avoir", "être"}
        
        def token_is_particip(tok):
            t_morph = tok.morph
            t_verbform = t_morph.get("VerbForm") or []
            t_tense = t_morph.get("Tense") or []
            t_tag = getattr(tok, "tag_", "") or ""
            if "Part" in (t_verbform or []) or "Past" in t_tense:
                return True
            if "Part" in t_tag or "VPP" in t_tag.upper():
                return True
            txt = tok.text.lower().strip(" ''")
            if PARTICIPLE_RE.match(txt):
                return True
            return False

        has_aux = False
        has_part = False

        for tok in doc:
            if tok.lemma_.lower() in auxiliaries or getattr(tok, "pos_", "") == "AUX":
                if "Pres" in tok.morph.get("Tense", []) or "Ind" in tok.morph.get("Mood", []) or "Fin" in tok.morph.get("VerbForm", []):
                    has_aux = True
                    next_i = tok.i + 1
                    if next_i < len(doc) and token_is_particip(doc[next_i]):
                        has_part = True
                        break
            if token_is_particip(tok):
                has_part = True

        return has_aux and has_part

    return bool(tense_vals or mood_vals or verbform_vals or tag)


def check_french_sentence(sentence, word_list, required_tense):
    """Check if a French sentence is correct."""
    doc = nlp(sentence)
    sentence_lemmas = [token.lemma_.lower() for token in doc]
    sentence_texts = [token.text.lower() for token in doc]

    # Find verbs
    verbs = [token for token in doc if token.pos_ in ("VERB", "AUX")]
    
    if required_tense == "Impératif" and len(doc) > 0 and not verbs:
        first_token = doc[0]
        if is_likely_verb(first_token.text):
            verbs = [first_token]

    if not verbs:
        return False, "✗ Your sentence needs a verb."

    # Check tense
    correct_tense = False
    for verb in verbs:
        if tense_matches(verb, required_tense, doc):
            correct_tense = True
            break

    if not correct_tense:
        return False, f"✗ Use the {required_tense} tense."

    # Check words
    words_found = []
    for word_dict in word_list:
        word = word_dict["word"].lower()
        
        if word in sentence_texts:
            words_found.append(word)
        elif word in sentence_lemmas:
            words_found.append(word)
        elif word.endswith("er") or word.endswith("ir") or word.endswith("oir") or word.endswith("re"):
            for token in doc:
                token_text_lower = token.text.lower()
                token_lemma_lower = token.lemma_.lower()
                
                if token_lemma_lower == word:
                    words_found.append(word)
                    break
                
                if is_likely_verb(token_text_lower):
                    if word == "manger":
                        if token_text_lower in {"mange", "manges", "mangeons", "mangez", "mangent", "mangerai", "mangerais", "mangeait", "mangeais", "mangé"}:
                            words_found.append(word)
                            break
                    inferred_inf = get_verb_infinitive(token_text_lower)
                    if inferred_inf == word:
                        words_found.append(word)
                        break

    if len(words_found) != len(word_list):
        missing = [w["word"] for w in word_list if w["word"].lower() not in words_found]
        return False, f"✗ Missing words: {', '.join(missing)}"

    # Check grammar
    matches = tool.check(sentence)
    grammar_errors = [
        m for m in matches 
        if m.category not in ('TYPOS', 'STYLE', 'REDUNDANCY', 'CASING', 'PUNCT_WHITESPACE', 'CAT_GRAMMAIRE')
    ]

    if grammar_errors:
        error_messages = [m.message for m in grammar_errors[:2]]
        return False, f"✗ Grammar: {', '.join(error_messages)}"

    # Check sentence structure
    has_verb = any(token.pos_ in ("VERB", "AUX") for token in doc)
    if not has_verb and required_tense == "Impératif" and len(doc) > 0:
        if is_likely_verb(doc[0].text):
            has_verb = True
    
    min_length = len(word_list) + 1

    if len(doc) < min_length or not has_verb:
        return False, "✗ Sentence too short or needs a verb"

    return True, "✓ CORRECT!"


# Initialize session state
if "score" not in st.session_state:
    st.session_state.score = 0
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "Easy"
if "tense" not in st.session_state:
    st.session_state.tense = "Présent"
if "words" not in st.session_state:
    st.session_state.words = random.sample(WORD_LISTS["Easy"], 3)
if "custom_words" not in st.session_state:
    st.session_state.custom_words = {"Easy": [], "Medium": [], "Hard": []}

# Sidebar
st.sidebar.title("🇫🇷 French Phrase Game")
st.sidebar.markdown("---")

# Difficulty selector
difficulty = st.sidebar.radio(
    "**Game Difficulty:**",
    ["Easy", "Medium", "Hard"],
    index=["Easy", "Medium", "Hard"].index(st.session_state.difficulty)
)

if difficulty != st.session_state.difficulty:
    st.session_state.difficulty = difficulty
    st.session_state.score = 0
    word_list = WORD_LISTS[difficulty] + st.session_state.custom_words[difficulty]
    st.session_state.words = random.sample(word_list, min(3, len(word_list)))
    st.rerun()

# Tense selector
tense = st.sidebar.selectbox(
    "**Verb Tense:**",
    TENSES,
    index=TENSES.index(st.session_state.tense)
)
st.session_state.tense = tense

# Score display
st.sidebar.markdown(f"### Score: {st.session_state.score}")

# Custom words section
st.sidebar.markdown("---")
st.sidebar.markdown("### Add Custom Words")

for diff in ["Easy", "Medium", "Hard"]:
    with st.sidebar.expander(f"Add word to {diff}"):
        col1, col2 = st.columns([3, 1])
        with col1:
            word = st.text_input(f"French word ({diff})", key=f"word_{diff}")
        with col2:
            if st.button("Add", key=f"btn_{diff}"):
                if word:
                    st.session_state.custom_words[diff].append({"word": word.lower(), "en": "custom"})
                    st.success(f"Added '{word}'!")
                    st.rerun()

# Main content
st.title("🇫🇷 French Phrase Game")
st.markdown(f"**Current Tense:** {st.session_state.tense} | **Difficulty:** {st.session_state.difficulty}")
st.markdown("---")

# Display word cards
st.markdown("### Required Words:")
cols = st.columns(3)
for i, word_dict in enumerate(st.session_state.words):
    with cols[i]:
        st.markdown(f"""
        <div class="word-card">
            <div>{word_dict['word']}</div>
            <div style="font-size: 12px; color: #888;">({word_dict['en']})</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Input area
st.markdown("### Write Your Sentence:")
user_sentence = st.text_area(
    "Enter your French sentence:",
    placeholder="Write a French sentence using all three words in the specified tense...",
    height=100,
    label_visibility="collapsed"
)

# Submit button
col1, col2 = st.columns(2)

with col1:
    if st.button("✓ Check Sentence", use_container_width=True):
        if user_sentence.strip():
            is_correct, feedback = check_french_sentence(
                user_sentence,
                st.session_state.words,
                st.session_state.tense
            )
            
            if is_correct:
                st.session_state.score += 1
                st.success(feedback)
                st.balloons()
                
                # Get new words
                word_list = WORD_LISTS[st.session_state.difficulty] + st.session_state.custom_words[st.session_state.difficulty]
                st.session_state.words = random.sample(word_list, min(3, len(word_list)))
                st.rerun()
            else:
                st.error(feedback)
        else:
            st.warning("Please write a sentence first!")

with col2:
    if st.button("🔄 New Words", use_container_width=True):
        word_list = WORD_LISTS[st.session_state.difficulty] + st.session_state.custom_words[st.session_state.difficulty]
        st.session_state.words = random.sample(word_list, min(3, len(word_list)))
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 12px;">
    Made with ❤️ | French Learning Game
</div>
""", unsafe_allow_html=True)
