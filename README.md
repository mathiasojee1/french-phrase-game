# 🇫🇷 French Phrase Game

A French language learning game built with Streamlit. Practice French verb conjugations across different tenses and difficulty levels!

## Features

✨ **7 French Tenses:**
- Présent (Present)
- Imparfait (Imperfect)
- Passé composé (Present Perfect)
- Futur simple (Future Simple)
- Conditionnel (Conditional)
- Subjonctif (Subjunctive)
- Impératif (Imperative)

🎯 **3 Difficulty Levels:**
- Easy
- Medium
- Hard

💡 **Smart Validation:**
- Tense detection using spaCy NLP
- Grammar checking with LanguageTool
- Verb conjugation matching
- Word requirement verification

🎮 **Game Features:**
- Score tracking
- Custom word addition
- Immediate feedback
- Automatic word refreshing

---

## Installation

### Prerequisites
- Python 3.8+
- pip

### Local Setup

1. **Clone the repository:**
```bash
git clone https://github.com/mathiasojee1/french-phrase-game.git
cd french-phrase-game
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Download the French spaCy model:**
```bash
python -m spacy download fr_core_news_sm
```

4. **Run the app:**
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## Deployment to Streamlit Cloud (FREE)

### Option 1: Automatic Deployment via GitHub

1. **Push your code to GitHub:**
   ```bash
   git add .
   git commit -m "Deploy to Streamlit Cloud"
   git push origin main
   ```

2. **Go to Streamlit Cloud:**
   - Visit https://streamlit.io/cloud
   - Sign in with GitHub

3. **Deploy your app:**
   - Click "New app"
   - Select your repository: `mathiasojee1/french-phrase-game`
   - Select main branch
   - Set main file path: `app.py`
   - Click "Deploy"

Your app will be live at: `https://your-username-french-phrase-game.streamlit.app`

### Option 2: Connect Custom Domain

After deploying to Streamlit Cloud:

1. **Buy a domain** (e.g., Namecheap ~$0.99 first year)
   - Go to https://www.namecheap.com
   - Search for your desired domain name
   - Complete purchase

2. **Point domain to Streamlit:**
   - In your domain provider, go to DNS settings
   - Add CNAME record:
     ```
     Name: @
     Type: CNAME
     Value: your-app-name.streamlit.app
     ```
   - Wait 10-30 minutes for DNS propagation

3. **Configure in Streamlit Cloud:**
   - Go to your app settings in Streamlit Cloud
   - Add your custom domain in the "Custom domain" section

---

## How to Play

1. **Select Difficulty:** Choose Easy, Medium, or Hard from the sidebar
2. **Choose Tense:** Pick a French verb tense to practice
3. **View Words:** Three required words are displayed at the top
4. **Write Sentence:** Write a French sentence using all three words in the chosen tense
5. **Submit:** Click "Check Sentence" for validation
6. **Get Feedback:** Receive instant feedback on:
   - Tense correctness
   - Grammar
   - Word usage
   - Sentence structure

---

## Adding Custom Words

1. Open the "Add Custom Words" section in the sidebar
2. Select difficulty level
3. Enter a French word
4. Click "Add"
5. Your custom words will be included in future rounds

---

## Technical Stack

- **Frontend:** Streamlit
- **NLP:** spaCy (French model)
- **Grammar Checking:** LanguageTool
- **Hosting:** Streamlit Cloud (Free)

---

## File Structure

```
french-phrase-game/
├── app.py                 # Main Streamlit application
├── game.py               # Original desktop version (customtkinter)
├── test_game.py          # Unit tests
├── requirements.txt      # Python dependencies
├── debug_grammar.py      # Debug script for grammar checking
├── game_settings.json    # Game settings (auto-generated)
└── README.md            # This file
```

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'spacy'`
**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: French spaCy model not found
**Solution:**
```bash
python -m spacy download fr_core_news_sm
```

### Issue: LanguageTool not working
**Solution:**
```bash
pip install --upgrade language-tool-python
```

### Issue: Streamlit app takes long to start
**Solution:** This is normal on first load. Subsequent loads are faster. The French spaCy model is large (~40MB).

---

## Testing

Run the unit tests to verify everything works:

```bash
python -m unittest test_game.py -v
```

All 12 tests should pass ✅

---

## Performance Notes

- **First load:** ~10-15 seconds (loads spaCy model)
- **Subsequent loads:** ~2-3 seconds
- **Streamlit Cloud:** Free tier has generous limits (~1 GB RAM)

---

## Future Improvements

- [ ] Audio pronunciation guide
- [ ] Leaderboard system
- [ ] More tenses and moods
- [ ] Phrase suggestions/hints
- [ ] User accounts and progress tracking
- [ ] Mobile app version

---

## License

MIT License - feel free to use and modify!

---

## Support

Found a bug? Have a suggestion? Open an issue on GitHub!

GitHub: https://github.com/mathiasojee1/french-phrase-game

---

Made with ❤️ for French learners
