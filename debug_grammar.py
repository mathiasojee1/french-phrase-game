from language_tool_python import LanguageTool

tool = LanguageTool('fr')

sentence = "Je mangerais une pomme"
matches = tool.check(sentence)

print(f"Sentence: {sentence}")
print(f"Total matches: {len(matches)}\n")

for m in matches:
    print(f"Message: {m.message}")
    print(f"Category: {m.category}")
    print(f"Rule ID: {m.ruleId}")
    print(f"---")
