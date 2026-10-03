# JEV: how jarring an 8-K excerpt reads, from 0 (planned, routine, recap) to 1 (abrupt, unplanned, new).
#
# Text only. Tune it with `python harness.py jev` (control categories + jev_labels.csv), never against P&L.
# Baseline: count abrupt cues against routine cues. Any scorer with score(text) -> [0, 1] and HIGH can replace it.
import re

HIGH = 0.5    # score >= HIGH is a high-JEV filing

ABRUPT = [r"effective immediately", r"\binterim\b", r"was terminated", r"terminat\w* (?:of )?(?:his|her|their) employment",
          r"for cause", r"without cause", r"investigation", r"misconduct", r"(?<!any )(?<!no )disagreement",
          r"passed away", r"\bdeath\b", r"medical leave", r"health reasons", r"unauthori[sz]ed", r"ransomware",
          r"cybersecurity incident", r"material(?:ly)? (?:adverse|impact)", r"impairment", r"wind(?:ing)? down",
          r"workforce reduction", r"layoffs?\b", r"reduction in force"]
ROUTINE = [r"retire", r"succession", r"\bplanned\b", r"previously (?:announced|disclosed|reported)",
           r"not the result of any disagreement", r"will continue to serve", r"orderly transition",
           r"annual meeting", r"(?:stockholders|shareholders) (?:approved|elected|voted)", r"ordinary course"]
_ABRUPT, _ROUTINE = re.compile("|".join(ABRUPT), re.I), re.compile("|".join(ROUTINE), re.I)


def score(text: str) -> float:
    h, r = len(_ABRUPT.findall(text or "")), len(_ROUTINE.findall(text or ""))
    return h / (h + r + 1)


if __name__ == "__main__":
    assert score("Mr. Smith will retire as CEO on March 1 as part of the Board's planned succession process.") < HIGH
    assert score("The Board terminated Ms. Doe's employment as CEO, effective immediately, and named an interim CEO.") >= HIGH
    assert score("At the annual meeting, shareholders approved the advisory vote on executive compensation.") < HIGH
    assert score("His resignation was not the result of any disagreement with the Company.") < HIGH
    assert score("") == 0
    print("jev ok")
