import re

for f in ["working_rate_updated_snippet.tex", "working_rate_old_vs_new_snippet.tex",
          "working_rate_updated_table_snippet.tex", "working_rate_updated.tex",
          "working_rate_old_vs_new.tex", "working_rate_updated_table.tex"]:
    s = open(f, encoding="utf-8").read()
    b = re.findall(r"\\begin\{([^}]+)\}", s)
    e = re.findall(r"\\end\{([^}]+)\}", s)
    print(f, "begin", len(b), "end", len(e),
          "balanced", sorted(b) == sorted(e),
          "braces", s.count("{") - s.count("}"),
          "dollars", s.count("$") % 2)
    if sorted(b) != sorted(e):
        print("  begin:", b)
        print("  end:", e)
