# JEV: how jarring an 8-K excerpt reads, from 0 (planned, routine, recap) to 1 (abrupt, unplanned, new).
#
# Text only. Tune it with `python harness.py jev` (control categories + jev_labels.csv), never against P&L.
#
# Two scorers, one interface:
#   - TypeSafe Jev, read from the cache in jev_scores.csv: P(abrupt) for the fixed QUESTION below.
#   - The regex lexicon, for any excerpt not in the cache.
# score() never calls the API, so results change only when jev_scores.csv changes (the harness hashes it).
# Fill the cache once with `python jev.py --fill` (needs TYPESAFE_API_KEY in .env and typesafe-sdk).
import csv, hashlib, os, re, sys
from pathlib import Path

HIGH = 0.5    # score >= HIGH is a high-JEV filing
ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "jev_scores.csv"
TEXTS = ROOT / "runs" / "jev_texts.csv"

# Frozen with the experiment: rewording this is a new JEV version, and filling with it needs a fresh cache.
QUESTION = {
    "instructions": "Judging only from this 8-K excerpt, is the disclosed event abrupt or planned?",
    "criteria": {
        "abrupt": "Unplanned, sudden, adverse or genuinely new: an immediate or unexplained resignation, a "
                  "termination, a death or health exit, an investigation, a breach, a surprise exit.",
        "planned": "Planned, routine or a recap: a scheduled retirement or succession, an orderly appointment, "
                   "a vote result, compensation terms, or a restatement of something already announced.",
    },
}

ABRUPT = [r"\binterim (?:ceo|cfo|executive officer)\b", r"was terminated", r"terminat\w* (?:of )?(?:his|her|their) employment",
          r"for cause", r"without cause(?!.*(?:plan|agreement|severance))", r"investigation", r"misconduct", r"(?<!any )(?<!no )disagreement",
          r"passed away", r"\bdeath\b", r"medical leave", r"health reasons", r"unauthori[sz]ed", r"ransomware",
          r"cybersecurity incident", r"cyber security incident", r"nation.state.*threat actor",
          r"detected.*threat actor", r"exfiltrat", r"material(?:ly)? (?:adverse|impact)", r"impairment", r"wind(?:ing)? down",
          r"workforce reduction", r"layoffs?\b", r"reduction in force", r"\bresign(?:ed|ing)\b.*effective (?:immediately|now)",
          r"resign(?:ed|ing)\b.*effective (?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{1,2},? \d{4}"]
ROUTINE = [r"retire", r"succession", r"\bplanned\b", r"previously (?:announced|disclosed|reported)",
           r"not the result of any disagreement", r"will continue to serve", r"orderly transition",
           r"annual meeting", r"(?:stockholders|shareholders) (?:approved|elected|voted)", r"ordinary course",
           r"expects? to", r"intends? to", r"announced.*plan", r"previously announced plan",
           r"criteria", r"\bappointed\b(?!.*immediately)", r"\belected\b(?!.*immediately)",
           r"one.time grant", r"standard.*practices", r"approved an award", r"termination.*(?:death|disability)",
           r"effective immediately.*board", r"board.*effective immediately", r"severance.*plan",
           r"income continuation plan", r"resulting from"]
_ABRUPT, _ROUTINE = re.compile("|".join(ABRUPT), re.I), re.compile("|".join(ROUTINE), re.I)


def key(text: str) -> str:
    return hashlib.sha1((text or "").strip().encode()).hexdigest()


def _load_cache() -> dict[str, float]:
    if not CACHE.exists():
        return {}
    with CACHE.open(encoding="utf-8", newline="") as f:
        return {r["text_sha1"]: float(r["p_abrupt"]) for r in csv.DictReader(f)}


_CACHED = _load_cache()


def regex_score(text: str) -> float:
    h, r = len(_ABRUPT.findall(text or "")), len(_ROUTINE.findall(text or ""))
    return h / (h + r + 1)


def score(text: str) -> float:
    return _CACHED.get(key(text), regex_score(text))


def fill(limit: int | None = None):
    """Score every uncached excerpt in runs/jev_texts.csv with Jev and append it to jev_scores.csv. Resumable."""
    for line in (ROOT / ".env").read_text().splitlines() if (ROOT / ".env").exists() else []:
        if line.strip().startswith("TYPESAFE_API_KEY=") and not os.environ.get("TYPESAFE_API_KEY"):
            os.environ["TYPESAFE_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not os.environ.get("TYPESAFE_API_KEY"):
        sys.exit("No TYPESAFE_API_KEY in the environment or .env. Add it to .env and rerun.")
    if not TEXTS.exists():
        sys.exit("runs/jev_texts.csv is missing. Run `python harness.py jev` first; it writes every excerpt there.")
    from typesafe_sdk import Choice, TypeSafeClient, TypeSafeError, TypeSafeAuthenticationError, TypeSafePermissionDeniedError

    with TEXTS.open(encoding="utf-8", newline="") as f:
        todo = {key(r["supporting_text"]): r["supporting_text"] for r in csv.DictReader(f) if r.get("supporting_text")}
    todo = [(k, t) for k, t in todo.items() if k not in _CACHED][:limit]
    print(f"{len(todo)} excerpts to score ({len(_CACHED)} already cached)")
    new = not CACHE.exists()
    client, question, failures = TypeSafeClient(), {"jev": Choice(**QUESTION)}, 0
    with CACHE.open("a", encoding="utf-8", newline="") as out:
        w = csv.writer(out)
        if new:
            w.writerow(["text_sha1", "p_abrupt", "model"])
        for i, (k, text) in enumerate(todo, 1):
            try:
                resp = client.system_one(text, question)
            except (TypeSafeAuthenticationError, TypeSafePermissionDeniedError) as e:
                sys.exit(f"TypeSafe rejected the key ({type(e).__name__}): check it, or whether your account is off the waitlist. {e}")
            except TypeSafeError as e:    # rate limit, timeout, server error: skip this one, it stays uncached
                failures += 1
                print(f"  {i}: {type(e).__name__}: {e}")
                if failures >= 5:
                    sys.exit("5 failures in a row; stopping. Rerun later; finished rows are kept.")
                continue
            failures = 0
            w.writerow([k, f"{resp.answers['jev'].probabilities['abrupt']:.6f}", resp.model])
            out.flush()
            if i % 50 == 0:
                print(f"  {i}/{len(todo)}")
    client.close()
    print(f"done; {len(_load_cache())} excerpts cached in {CACHE.name}")


if __name__ == "__main__" and "--fill" in sys.argv:
    fill(int(sys.argv[sys.argv.index("--fill") + 1]) if len(sys.argv) > sys.argv.index("--fill") + 1 else None)
elif __name__ == "__main__":
    assert regex_score("Mr. Smith will retire as CEO on March 1 as part of the Board's planned succession process.") < HIGH
    assert regex_score("The Board terminated Ms. Doe's employment as CEO, effective immediately, and named an interim CEO.") >= HIGH
    assert regex_score("At the annual meeting, shareholders approved the advisory vote on executive compensation.") < HIGH
    assert regex_score("His resignation was not the result of any disagreement with the Company.") < HIGH
    assert regex_score("") == 0
    assert score("never-scored zq") == regex_score("never-scored zq")    # uncached -> regex fallback
    print(f"jev ok ({len(_CACHED)} Jev scores cached)")
