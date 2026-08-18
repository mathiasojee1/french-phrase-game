import customtkinter as ctk
import random
import threading
import spacy
import fr_core_news_sm
from language_tool_python import LanguageTool

# AI Setup
nlp = fr_core_news_sm.load()
tool = LanguageTool('fr')

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

score = 0
current_words = []
current_difficulty = "Easy"
words = easy_words

def pick_three():
    return random.sample(words, 3)

def check_french_sentence(sentence, word_list):
    result = {
        "is_correct": False,
        "feedback": [],
        "all_words_used": False,
        "no_grammar_errors": False,
    }
    doc = nlp(sentence)
    sentence_lemmas = [token.lemma_.lower() for token in doc]
    
    words_found = []
    for word_dict in word_list:
        word = word_dict["word"].lower()
        if word in [token.text.lower() for token in doc] or word in sentence_lemmas:
            words_found.append(word)
    
    if len(words_found) == len(word_list):
        result["all_words_used"] = True
        result["feedback"].append("✓ All required words used")
    else:
        missing = [w["word"] for w in word_list if w["word"].lower() not in words_found]
        result["feedback"].append(f"✗ Missing words: {', '.join(missing)}")
        return False, " | ".join(result["feedback"])
    
    matches = tool.check(sentence)
    grammar_errors = [m for m in matches if m.category != 'TYPOS']
    
    if not grammar_errors:
        result["no_grammar_errors"] = True
        result["feedback"].append("✓ Grammar is correct")
    else:
        error_messages = [m.message for m in grammar_errors[:2]]
        result["feedback"].append(f"✗ Grammar: {', '.join(error_messages)}")
        return False, " | ".join(result["feedback"])
    
    has_verb = any(token.pos_ == "VERB" for token in doc)
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

def _run_check_in_thread(sentence, words_snapshot):
    try:
        is_correct, feedback = check_french_sentence(sentence, words_snapshot)
    except Exception as e:
        msg = f"Error: {e}"
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
    global current_words
    current_words = pick_three()
    for i, card in enumerate(word_cards):
        card.configure(text=f"{current_words[i]['word']}\n({current_words[i]['en']})")
    entry.delete(0, "end")
    feedback_label.configure(text="")

def on_submit():
    sentence = entry.get()
    if not sentence.strip():
        feedback_label.configure(text="Please write a sentence first!", text_color="orange")
        return

    feedback_label.configure(text="Checking...", text_color="gray")
    app.update()

    words_snapshot = list(current_words)
    threading.Thread(target=_run_check_in_thread, args=(sentence, words_snapshot), daemon=True).start()

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

# submit custom word
def submit_custom_word(difficulty):

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

# Window Setup 
ctk.set_appearance_mode("dark")
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
difficulty_buttons["Easy"].configure(fg_color="#1f6aa5")

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

# MAIN CONTENT
content = ctk.CTkFrame(main_container, fg_color="transparent")
content.pack(side="right", fill="both", expand=True, padx=20, pady=20)

score_label = ctk.CTkLabel(content, text="Score: 0", font=("Georgia", 16))
score_label.pack(pady=10)

words_frame = ctk.CTkFrame(content, fg_color="transparent")
words_frame.pack(pady=10)

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

theme_var = ctk.StringVar(value="Dark")
theme_combo = ctk.CTkComboBox(settings_content, values=["Dark", "Light"], variable=theme_var, state="readonly")
theme_combo.pack(fill="x", pady=5)

sound_label = ctk.CTkLabel(settings_content, text="Sound:", font=("Georgia", 14))
sound_label.pack(anchor="w", pady=(20, 10))

sound_var = ctk.BooleanVar(value=True)
sound_check = ctk.CTkCheckBox(settings_content, text="Enable sound effects", variable=sound_var)
sound_check.pack(anchor="w")

volume_label = ctk.CTkLabel(settings_content, text="Volume:", font=("Georgia", 14))
volume_label.pack(anchor="w", pady=(20, 10))

volume_slider = ctk.CTkSlider(settings_content, from_=0, to=100, number_of_steps=10)
volume_slider.pack(fill="x", pady=5)
volume_slider.set(70)

game_settings_label = ctk.CTkLabel(settings_content, text="Game Settings:", font=("Georgia", 14))
game_settings_label.pack(anchor="w", pady=(20, 10))

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

# =========================
# CHANGE WORDS OVERLAY
# =========================

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

    entry = ctk.CTkEntry(
        frame,
        placeholder_text="New French word..."
    )
    entry.pack(fill="x", padx=10, pady=10)

    word_entries[difficulty] = entry

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
    feedback.pack(pady=(5,15))

    word_feedback_labels[difficulty] = feedback

close_change_words()

app.mainloop()