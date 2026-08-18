import customtkinter as ctk
import random
import threading
import spacy
from language_tool_python import LanguageTool
import re
import json
import os

# AI Setup
nlp = spacy.load("fr_core_news_sm")
tool = LanguageTool('fr')
PARTICIPLE_RE = re.compile(r".*(é|ée|és|ées|i|is|it|u|us|ut|ant|onné|ée)$", re.IGNORECASE)

# Settings file path
SETTINGS_FILE = "game_settings.json"

# Word Lists for Different Difficulties
easy_words = [
    {"word": "chat", "en": "cat"},
    {"word": "maison", "en": "house"},
    {"word": "soleil", "en": "sun"},
    {"word": "chien", "en": "dog"},
    {"word": "eau", "en": "water"},
]

medium_words = [
    {"word": "manger", "en": "eating"},
    {"word": "grand", "en": "big"},
    {"word": "dormir", "en": "sleeping"},
    {"word": "ville", "en": "city"},
    {"word": "nuit", "en": "night"},
]

hard_words = [
    {"word": "magnifique", "en": "magnificent"},
    {"word": "extraordinaire", "en": "extraordinary"},
    {"word": "néanmoins", "en": "nevertheless"},
    {"word": "splendide", "en": "splendid"},
    {"word": "délicieux", "en": "delicious"},
]

all_words = {
    "Easy": easy_words,
    "Medium": medium_words,
    "Hard": hard_words,
}

tenses = [
    "Présent",
    "Imparfait",
    "Passé composé",
    "Futur simple",
    "Conditionnel",
    "Impératif",
    "Subjonctif"
]

current_tense = "Présent"
current_tense_lock = threading.Lock()

score = 0
current_words = []
current_difficulty = "Easy"
words = easy_words


def load_settings():
    """Load settings from file"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
    return {
        "theme": "dark",
        "sound": True,
        "volume": 70,
        "tense": "Présent",
        "difficulty": "Easy"
    }


def save_settings(settings):
    """Save settings to file"""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")


def pick_three():
    return random.sample(words, 3)


def is_likely_verb(token_text):
    """
    Check if a token is likely to be a verb form.
    Handles cases where spaCy misparsses imperatives as nouns.
    """
    # Common French verb lemmas and conjugations
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
    
    # Check for common verb endings
    if text_lower.endswith(("er", "ir", "oir", "re")):
        return True
    if text_lower.endswith(("ais", "ait", "aient", "ions", "iez")):
        return True
    if text_lower.endswith(("ai", "as", "ons", "ez")):
        return True
    
    return False


def get_verb_infinitive(token_text):
    """
    Try to convert a conjugated verb form to its infinitive.
    For example: "Mange" -> "manger"
    """
    text_lower = token_text.lower()
    
    # Direct match
    if text_lower in {"manger", "aller", "venir", "voir", "faire", "dire", "prendre"}:
        return text_lower
    
    # Handle -e endings (présent, impératif) -> remove and add -er
    if text_lower.endswith("e") and len(text_lower) > 1:
        base = text_lower[:-1]
        if base + "er" in {"manger", "aller", "parler", "donner", "travailler", "penser"}:
            return base + "er"
    
    # Handle -es endings -> -er
    if text_lower.endswith("es") and len(text_lower) > 2:
        base = text_lower[:-2]
        if base + "er" in {"manger", "aller", "parler", "donner", "travailler"}:
            return base + "er"
    
    # Handle -ons endings -> -er
    if text_lower.endswith("ons") and len(text_lower) > 3:
        base = text_lower[:-3]
        if base + "er" in {"manger", "aller", "parler"}:
            return base + "er"
    
    return None


def tense_matches(token, required_tense, doc=None):
    """
    Robust tense/mood detection for fr_core_news_sm.
    Detects auxiliaries + participles for 'Passé composé' even if spaCy mis-tags the participle.
    """
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

    # Simple cases
    if required_tense == "Présent":
        return has(tense_vals, "Pres") or ("Pres" in tag)
    
    if required_tense == "Imparfait":
        return has(tense_vals, "Imp") or ("Imp" in tag)
    
    if required_tense == "Futur simple":
        return has(tense_vals, "Fut") or ("Fut" in tag)
    
    if required_tense == "Conditionnel":
        # Check for Conditionnel mood or tag
        if has(mood_vals, "Cnd") or ("Cnd" in tag):
            return True
        # Fallback: check VerbForm=Fin with conditional marker
        if has(verbform_vals, "Fin") and ("ais" in text or "rait" in text or "rais" in text):
            return True
        return False
    
    if required_tense == "Subjonctif":
        # Check for Subjonctif mood or tag
        if has(mood_vals, "Sub") or ("Sub" in tag):
            return True
        # Fallback: common subjunctive patterns
        if has(verbform_vals, "Fin") and ("e" in text or "es" in text or "ent" in text):
            # Check if sentence has "que" or "faut que"
            if doc is not None:
                sent_text = doc.text.lower()
                if "que" in sent_text or "faut" in sent_text:
                    return True
        return False
    
    if required_tense == "Impératif":
        # 1) Strong signal: Mood=Imp
        if has(mood_vals, "Imp") or ("Imp" in tag):
            return True

        # 2) Token at position 0 that looks like a verb (even if misparsed as NOUN)
        if doc is not None and token.i == 0:
            if is_likely_verb(token.text):
                return True

        # 3) Check if this is a verb lemma at sentence start
        if doc is not None and token.i == 0 and is_likely_verb(lemma):
            return True

        # 4) Standard heuristic: verb at start of sentence
        if doc is not None:
            for tok in doc:
                if getattr(tok, "pos_", "") in ("VERB", "AUX"):
                    if tok.i == 0:
                        return True
                    if tok.i == 1:
                        prev = doc[0].text.lower()
                        if prev in ("ne", "n'"):
                            return True
                    if tok.i <= 2:
                        prev_tok = doc[tok.i - 1] if tok.i - 1 >= 0 else None
                        if prev_tok is None or prev_tok.pos_ in ("PUNCT", "PART", "INTJ", "SCONJ", "ADV"):
                            return True

        # 5) Fallback: finite verb with no subject pronoun before it
        if pos == "VERB" and has(verbform_vals, "Fin"):
            if not has(mood_vals, "Cnd") and not has(mood_vals, "Sub"):
                if doc is not None:
                    if token.i is not None:
                        prev_has_pron = any(t.pos_ == "PRON" and t.i < token.i and t.text.lower() not in ("y", "en") for t in doc)
                        if not prev_has_pron:
                            return True
                else:
                    return True

        return False

    # Passé composé detection (robust heuristic)
    if required_tense == "Passé composé":
        if doc is None:
            return False

        auxiliaries = {"avoir", "être"}

        def token_is_particip(tok):
            t_morph = tok.morph
            t_verbform = t_morph.get("VerbForm") or []
            t_tense = t_morph.get("Tense") or []
            t_tag = getattr(tok, "tag_", "") or ""
            # strong signals
            if "Part" in (t_verbform or []) or "Past" in t_tense:
                return True
            if "Part" in t_tag or "VPP" in t_tag.upper():
                return True
            # fallback: common participle endings (covers 'bu', 'mangé', etc.)
            txt = tok.text.lower().strip(" ''")
            if PARTICIPLE_RE.match(txt):
                return True
            return False

        has_aux = False
        has_part = False

        for tok in doc:
            # detect auxiliary (avoir/être) or spaCy AUX token
            if tok.lemma_.lower() in auxiliaries or getattr(tok, "pos_", "") == "AUX":
                if "Pres" in tok.morph.get("Tense", []) or "Ind" in tok.morph.get("Mood", []) or "Fin" in tok.morph.get("VerbForm", []):
                    has_aux = True
                    # check token immediately after aux (common case: "ont bu")
                    next_i = tok.i + 1
                    if next_i < len(doc) and token_is_particip(doc[next_i]):
                        has_part = True
                        break
            if token_is_particip(tok):
                has_part = True

        return has_aux and has_part

    # fallback: accept if any tense/mood/verbform/tag info exists
    return bool(tense_vals or mood_vals or verbform_vals or tag)


def check_french_sentence(sentence, word_list, required_tense):
    """
    Check if a French sentence is correct.
    """
    result = {
        "is_correct": False,
        "feedback": [],
        "all_words_used": False,
        "no_grammar_errors": False,
    }
    doc = nlp(sentence)
    sentence_lemmas = [token.lemma_.lower() for token in doc]
    sentence_texts = [token.text.lower() for token in doc]

    # Find verbs and auxiliaries and check tense (pass doc for compound tenses)
    verbs = [token for token in doc if token.pos_ in ("VERB", "AUX")]
    
    # For Impératif: also check if first token could be a verb (spaCy sometimes mislabels)
    if required_tense == "Impératif" and len(doc) > 0 and not verbs:
        first_token = doc[0]
        if is_likely_verb(first_token.text):
            verbs = [first_token]

    if not verbs:
        return False, "✗ Your sentence needs a verb."

    correct_tense = False
    for verb in verbs:
        if tense_matches(verb, required_tense, doc):
            correct_tense = True
            break

    if not correct_tense:
        return False, f"✗ Use the {required_tense} tense."

    # Rest of original checks (words, grammar, etc.)
    words_found = []
    for word_dict in word_list:
        word = word_dict["word"].lower()
        
        # Check direct text match
        if word in sentence_texts:
            words_found.append(word)
        # Check lemma match
        elif word in sentence_lemmas:
            words_found.append(word)
        # For infinitives, check if any conjugation of that verb is in the sentence
        elif word.endswith("er") or word.endswith("ir") or word.endswith("oir") or word.endswith("re"):
            # This is likely an infinitive, check for conjugations
            for token in doc:
                token_text_lower = token.text.lower()
                token_lemma_lower = token.lemma_.lower()
                
                # Direct lemma match
                if token_lemma_lower == word:
                    words_found.append(word)
                    break
                
                # Check if this token is a conjugation of the target verb
                if is_likely_verb(token_text_lower):
                    # For "manger", check if conjugations match
                    if word == "manger":
                        if token_text_lower in {"mange", "manges", "mangeons", "mangez", "mangent", "mangerai", "mangerais", "mangeait", "mangeais", "mangé"}:
                            words_found.append(word)
                            break
                    # Try to get the infinitive and compare
                    inferred_inf = get_verb_infinitive(token_text_lower)
                    if inferred_inf == word:
                        words_found.append(word)
                        break

    if len(words_found) == len(word_list):
        result["all_words_used"] = True
        result["feedback"].append("✓ All required words used")
    else:
        missing = [w["word"] for w in word_list if w["word"].lower() not in words_found]
        result["feedback"].append(f"✗ Missing words: {', '.join(missing)}")
        return False, " | ".join(result["feedback"])

    matches = tool.check(sentence)
    # Filter out style suggestions and grammar recommendations
    # Only reject for actual errors
    grammar_errors = [
        m for m in matches 
        if m.category not in ('TYPOS', 'STYLE', 'REDUNDANCY', 'CASING', 'PUNCT_WHITESPACE', 'CAT_GRAMMAIRE')
    ]

    if not grammar_errors:
        result["no_grammar_errors"] = True
        result["feedback"].append("✓ Grammar is correct")
    else:
        error_messages = [m.message for m in grammar_errors[:2]]
        result["feedback"].append(f"✗ Grammar: {', '.join(error_messages)}")
        return False, " | ".join(result["feedback"])

    # Check for verb - including misparsed imperatives
    has_verb = any(token.pos_ in ("VERB", "AUX") for token in doc)
    
    # For Impératif, also accept if first token looks like a verb
    if not has_verb and required_tense == "Impératif" and len(doc) > 0:
        if is_likely_verb(doc[0].text):
            has_verb = True
    
    min_length = len(word_list) + 1

    if len(doc) >= min_length and has_verb:
        result["feedback"].append("✓ Sentence structure is good")
    else:
        if not has_verb:
            result["feedback"].append("✗ Sentence needs a verb")
        if len(doc) < min_length:
            result["feedback"].append(f"✗ Sentence too short")
        return False, " | ".join(result["feedback"])

    result["is_correct"] = True
    result["feedback"].append("✓ CORRECT!")

    return True, " | ".join(result["feedback"])


def _run_check_in_thread(sentence, words_snapshot, tense_snapshot):
    """
    Run sentence check in background thread.
    Takes a snapshot of tense to avoid race conditions.
    """
    try:
        is_correct, feedback = check_french_sentence(
            sentence,
            words_snapshot,
            tense_snapshot
        )
    except Exception as e:
        msg = f"Error: {str(e)}"
        print(f"Exception in check thread: {e}")
        import traceback
        traceback.print_exc()
        app.after(0, lambda: feedback_label.configure(text=msg, text_color="red"))
        return

    def finish():
        global score
        if is_correct:
            score += 1
            score_label.configure(text=f"Score: {score}")
            feedback_label.configure(text=feedback, text_color="green")
            app.after(2000, refresh_words)
        else:
            feedback_label.configure(text=feedback, text_color="red")

    app.after(0, finish)


def refresh_words():
    """Refresh the word cards with new words"""
    global current_words
    current_words = pick_three()
    for i, card in enumerate(word_cards):
        card.configure(text=f"{current_words[i]['word']}\n({current_words[i]['en']})")
    entry.delete(0, "end")
    feedback_label.configure(text="")


def on_submit():
    """Handle submission of French sentence"""
    sentence = entry.get()

    if not sentence.strip():
        feedback_label.configure(text="Please write a sentence first!", text_color="orange")
        return

    feedback_label.configure(text="Checking...", text_color="gray")
    app.update()

    words_snapshot = list(current_words)
    
    # Get tense snapshot to avoid race condition
    with current_tense_lock:
        tense_snapshot = current_tense
    
    threading.Thread(
        target=_run_check_in_thread,
        args=(sentence, words_snapshot, tense_snapshot),
        daemon=True
    ).start()


def set_difficulty(difficulty):
    """Change difficulty and reset game"""
    global score, current_words, words, current_difficulty
    current_difficulty = difficulty
    words = all_words[difficulty]
    score = 0
    score_label.configure(text=f"Score: 0")
    refresh_words()
    
    # Update sidebar button colors
    for diff_name, btn_obj in difficulty_buttons.items():
        if diff_name == difficulty:
            btn_obj.configure(fg_color="#1f6aa5")
        else:
            btn_obj.configure(fg_color="gray")
    
    sidebar_info.configure(text=f"Current:\n{difficulty}")
    
    # Save settings
    settings = load_settings()
    settings["difficulty"] = difficulty
    save_settings(settings)


def open_settings():
    """Show settings panel"""
    settings_overlay.tkraise()


def open_change_words():
    """Show change words panel"""
    change_words_overlay.tkraise()


def close_change_words():
    """Hide change words panel"""
    change_words_overlay.lower()


def close_settings():
    """Hide settings panel"""
    settings_overlay.lower()


def submit_custom_word(difficulty):
    """Submit a custom word for a difficulty"""
    word = word_entries[difficulty].get().strip()

    if word == "":
        word_feedback_labels[difficulty].configure(
            text="Enter a word!",
            text_color="orange"
        )
        return

    all_words[difficulty].append({
        "word": word,
        "en": "custom"
    })

    box = word_boxes[difficulty]

    box.configure(state="normal")
    box.insert("end", f"{word} (custom)\n")
    box.configure(state="disabled")

    word_feedback_labels[difficulty].configure(
        text=f"Added '{word}'!",
        text_color="green"
    )

    word_entries[difficulty].delete(0, "end")


def set_tense(tense):
    """Set the current tense with thread-safe locking"""
    global current_tense
    with current_tense_lock:
        current_tense = tense

    tense_label.configure(text=f"Tense:\n{current_tense}")
    
    # Save settings
    settings = load_settings()
    settings["tense"] = tense
    save_settings(settings)


def set_theme(theme):
    """Set the theme"""
    ctk.set_appearance_mode(theme.lower())
    settings = load_settings()
    settings["theme"] = theme.lower()
    save_settings(settings)


def set_sound(value):
    """Set sound preference"""
    settings = load_settings()
    settings["sound"] = value
    save_settings(settings)


def set_volume(value):
    """Set volume level"""
    settings = load_settings()
    settings["volume"] = int(value)
    save_settings(settings)


# Load settings
loaded_settings = load_settings()

# Window Setup 
ctk.set_appearance_mode(loaded_settings["theme"])
app = ctk.CTk()
app.title("French Phrase Game")
app.geometry("800x500")

# Create main container
main_container = ctk.CTkFrame(app, fg_color="transparent")
main_container.pack(fill="both", expand=True, padx=0, pady=0)

# SIDEBAR
sidebar = ctk.CTkFrame(main_container, width=200, fg_color="#1a1a1a", corner_radius=0)
sidebar.pack(side="left", fill="y", padx=0, pady=0)
sidebar.pack_propagate(False)

sidebar_title = ctk.CTkLabel(sidebar, text="GAME MODES", font=("Georgia", 14, "bold"), text_color="#1f6aa5")
sidebar_title.pack(pady=20)

# Difficulty buttons
difficulty_buttons = {}

for difficulty in ["Easy", "Medium", "Hard"]:
    btn = ctk.CTkButton(
        sidebar,
        text=difficulty,
        font=("Georgia", 12),
        width=160,
        height=40,
        fg_color="gray",
        hover_color="#2a2a2a",
        command=lambda d=difficulty: set_difficulty(d)
    )
    btn.pack(pady=10)
    difficulty_buttons[difficulty] = btn

# Set Easy as default
difficulty_buttons[loaded_settings["difficulty"]].configure(fg_color="#1f6aa5")
current_difficulty = loaded_settings["difficulty"]

sidebar_divider = ctk.CTkLabel(sidebar, text="", fg_color="gray", height=1)
sidebar_divider.pack(fill="x", pady=20, padx=10)

sidebar_info = ctk.CTkLabel(
    sidebar,
    text=f"Current:\n{current_difficulty}",
    font=("Georgia", 15),
    text_color="gray"
)
sidebar_info.pack(pady=1)

sidebar_divider2 = ctk.CTkLabel(sidebar, text="", fg_color="gray", height=1)
sidebar_divider2.pack(fill="x", pady=20, padx=10)

setting_button = ctk.CTkButton(
    sidebar,
    text="Settings",
    font=("Georgia", 12),
    width=100,
    height=40,
    fg_color="gray",
    hover_color="#2a2a2a",
    command=open_settings
)
setting_button.pack(pady=10)

current_tense = loaded_settings["tense"]
tense_label = ctk.CTkLabel(
    sidebar,
    text=f"Tense:\n{current_tense}",
    font=("Georgia", 14)
)
tense_label.pack(pady=10)

# MAIN CONTENT
content = ctk.CTkFrame(main_container, fg_color="transparent")
content.pack(side="right", fill="both", expand=True, padx=20, pady=20)

score_label = ctk.CTkLabel(content, text="Score: 0", font=("Georgia", 16))
score_label.pack(pady=10)

words_frame = ctk.CTkFrame(content, fg_color="transparent")
words_frame.pack(pady=10)

# Set words based on loaded difficulty
words = all_words[current_difficulty]
current_words = pick_three()
word_cards = []
for w in current_words:
    card = ctk.CTkLabel(
        words_frame,
        text=f"{w['word']}\n({w['en']})",
        font=("Georgia", 18),
        width=150, height=80,
        fg_color="#35353f",
        corner_radius=10
    )
    card.pack(side="left", padx=10)
    word_cards.append(card)

entry = ctk.CTkEntry(content, placeholder_text="Write your French sentence...", width=450)
entry.pack(pady=20)

btn_frame = ctk.CTkFrame(content, fg_color="transparent")
btn_frame.pack()

ctk.CTkButton(btn_frame, text="Check my phrase", command=on_submit).pack(side="left", padx=10)
ctk.CTkButton(btn_frame, text="New words", command=refresh_words, fg_color="gray").pack(side="left", padx=10)

feedback_label = ctk.CTkLabel(content, text="", wraplength=500, font=("Georgia", 13))
feedback_label.pack(pady=20)

# SETTINGS OVERLAY

settings_overlay = ctk.CTkFrame(app, fg_color="transparent", corner_radius=0)
settings_overlay.place(x=0, y=0, relwidth=1, relheight=1)

settings_panel = ctk.CTkFrame(settings_overlay, fg_color="#2b2b2b", corner_radius=15, border_width=2, border_color="#1f6aa5", width=400, height=350)
settings_panel.place(relx=0.5, rely=0.5, anchor="center")

header_frame = ctk.CTkFrame(settings_panel, fg_color="transparent")
header_frame.pack(fill="x", padx=20, pady=15)

settings_title = ctk.CTkLabel(header_frame, text="SETTINGS", font=("Georgia", 18, "bold"), text_color="#1f6aa5")
settings_title.pack(side="left")

close_button = ctk.CTkButton(
    header_frame,
    text="✕",
    font=("Georgia", 16, "bold"),
    width=30,
    height=30,
    fg_color="#1f6aa5",
    hover_color="red",
    command=lambda: close_settings()
)
close_button.pack(side="right")

settings_content = ctk.CTkScrollableFrame(settings_panel, fg_color="transparent")
settings_content.pack(fill="both", expand=True, padx=20, pady=5)

theme_label = ctk.CTkLabel(settings_content, text="Theme:", font=("Georgia", 14))
theme_label.pack(anchor="w", pady=10)

theme_var = ctk.StringVar(value=loaded_settings["theme"].capitalize())
theme_combo = ctk.CTkComboBox(
    settings_content,
    values=["Dark", "Light"],
    variable=theme_var,
    state="readonly",
    command=lambda v: set_theme(v)
)
theme_combo.pack(fill="x", pady=5)

sound_label = ctk.CTkLabel(settings_content, text="Sound:", font=("Georgia", 14))
sound_label.pack(anchor="w", pady=(20, 10))

sound_var = ctk.BooleanVar(value=loaded_settings["sound"])
sound_check = ctk.CTkCheckBox(
    settings_content,
    text="Enable sound effects",
    variable=sound_var,
    command=lambda: set_sound(sound_var.get())
)
sound_check.pack(anchor="w")

volume_label = ctk.CTkLabel(settings_content, text="Volume:", font=("Georgia", 14))
volume_label.pack(anchor="w", pady=(20, 10))

volume_slider = ctk.CTkSlider(
    settings_content,
    from_=0,
    to=100,
    number_of_steps=10,
    command=set_volume
)
volume_slider.pack(fill="x", pady=5)
volume_slider.set(loaded_settings["volume"])

game_settings_label = ctk.CTkLabel(settings_content, text="Game Settings:", font=("Georgia", 14))
game_settings_label.pack(anchor="w", pady=(20, 10))

tension_label = ctk.CTkLabel(
    settings_content,
    text="Verb Tense:",
    font=("Georgia", 14)
)
tension_label.pack(anchor="w", pady=(20, 5))

tension_var = ctk.StringVar(value=loaded_settings["tense"])

tension_combo = ctk.CTkComboBox(
    settings_content,
    values=tenses,
    variable=tension_var,
    state="readonly",
    command=set_tense
)
tension_combo.pack(fill="x")

btn2 = ctk.CTkButton(
    settings_content,
    text="Add Words",
    font=("Georgia", 12),
    width=160,
    height=40,
    fg_color="gray",
    hover_color="#2a2a2a",
    command=open_change_words
)
btn2.pack(pady=10)

close_settings()

# CHANGE WORDS OVERLAY

change_words_overlay = ctk.CTkFrame(app, fg_color="transparent")
change_words_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

change_words_panel = ctk.CTkFrame(
    change_words_overlay,
    width=950,
    height=600,
    fg_color="#2b2b2b",
    border_width=2,
    border_color="#1f6aa5",
    corner_radius=15
)
change_words_panel.place(relx=0.5, rely=0.5, anchor="center")

header = ctk.CTkFrame(change_words_panel, fg_color="transparent")
header.pack(fill="x", padx=20, pady=15)

ctk.CTkLabel(
    header,
    text="CHANGE WORDS",
    font=("Georgia", 22, "bold"),
    text_color="#1f6aa5"
).pack(side="left")

ctk.CTkButton(
    header,
    text="✕",
    width=35,
    command=close_change_words,
    fg_color="#1f6aa5",
    hover_color="red"
).pack(side="right")

# -------------------------

columns = ctk.CTkFrame(change_words_panel, fg_color="transparent")
columns.pack(fill="both", expand=True, padx=20, pady=20)

for i in range(3):
    columns.grid_columnconfigure(i, weight=1)

word_boxes = {}
word_entries = {}
word_feedback_labels = {}

for col, difficulty in enumerate(["Easy", "Medium", "Hard"]):

    frame = ctk.CTkFrame(columns, corner_radius=12)
    frame.grid(row=0, column=col, padx=10, sticky="nsew")

    title = ctk.CTkLabel(
        frame,
        text=difficulty,
        font=("Georgia", 18, "bold"),
        text_color="#1f6aa5"
    )
    title.pack(pady=10)

    textbox = ctk.CTkTextbox(
        frame,
        width=250,
        height=250
    )
    textbox.pack(padx=10)

    # Fill textbox
    for item in all_words[difficulty]:
        textbox.insert("end", f"{item['word']} ({item['en']})\n")

    textbox.configure(state="disabled")

    word_boxes[difficulty] = textbox

    entry2 = ctk.CTkEntry(
        frame,
        placeholder_text="New French word..."
    )
    entry2.pack(fill="x", padx=10, pady=10)

    word_entries[difficulty] = entry2

    button = ctk.CTkButton(
        frame,
        text="Add Word",
        command=lambda d=difficulty: submit_custom_word(d)
    )
    button.pack(pady=5)

    feedback = ctk.CTkLabel(
        frame,
        text="",
        wraplength=220
    )
    feedback.pack(pady=(5, 15))

    word_feedback_labels[difficulty] = feedback

close_change_words()

app.mainloop()
