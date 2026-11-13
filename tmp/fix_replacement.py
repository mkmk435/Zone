for name in ("llm_data.py","llm_technique.py","llm_stats.py","llm_payload.py","pobf.py","pobf86.py","README.md"):
    text = open(name, encoding="utf-8").read()
    count = text.count("\ufffd")
    if count:
        print(name, count)
        text = text.replace("\ufffd", "-")
        with open(name, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
