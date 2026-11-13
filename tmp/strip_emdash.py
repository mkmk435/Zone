import io
for name in ("llm_data.py", "llm_technique.py"):
    with open(name, encoding="utf-8") as f:
        text = f.read()
    text = text.replace(" ? ", " - ")
    with open(name, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
print("done")
