"""
Freeze the prompt texts as v1 (register A66): the arm-2 template (pilot wording W1, C37) and the
arm-3 instruction built from it (A49). Writes prompts/frozen_v1/*.txt (UTF-8, LF, no trailing
newline) and prints their SHA-256. Refuses to overwrite a frozen file with different content.

Usage:  python experiments/step5_freeze_prompts.py
"""
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import step4_prompt_tokens as rt  # noqa: E402

ROOT = os.path.join(HERE, "..")
DRAFT = os.path.join(ROOT, "prompts", "DRAFT_arm2_arm3.md")
FROZEN = os.path.join(ROOT, "prompts", "frozen_v1")
ARM2_FILE = os.path.join(FROZEN, "arm2_template_v1.txt")
ARM3_FILE = os.path.join(FROZEN, "arm3_instruction_v1.txt")
SLOT = "[the arm-2 template from section 1, verbatim, placeholders unfilled]"


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build():
    blocks = re.findall(r"```\n(.*?)\n```", open(DRAFT, encoding="utf-8").read(), re.S)
    arm2, arm3_draft = blocks[0], blocks[2]
    assert arm2 == rt.TEMPLATE, "draft template differs from the renderer's"
    assert arm3_draft.count(SLOT) == 1
    return arm2, arm3_draft.replace(SLOT, arm2)


def main():
    os.makedirs(FROZEN, exist_ok=True)
    arm2, arm3 = build()
    for path, text in ((ARM2_FILE, arm2), (ARM3_FILE, arm3)):
        if os.path.exists(path):
            old = open(path, encoding="utf-8", newline="").read()
            assert old == text, f"{path} is frozen and differs; not overwritten"
        else:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(text)
        print(f"{os.path.relpath(path, ROOT)}  sha256 {sha256(text)}  {len(text)} chars")


if __name__ == "__main__":
    main()
