for name in ("llm_data.py","llm_technique.py","llm_stats.py"):
    text = open(name, encoding="utf-8").read()
    if "\u2014" in text:
        print(name, text.count("\u2014"))
        text = text.replace("\u2014", "-")
        with open(name, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
