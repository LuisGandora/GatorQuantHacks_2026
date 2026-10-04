"""Full-context text safeguard, independent of quotes and benchmark choice."""
import re
import count_credit_prebaseline_v2 as previous


def review(row):
    reason = previous.review(row)
    if reason:
        return reason
    text = str(row.context_text).lower()
    paragraphs = [p for p in text.splitlines() if re.search(r'\brevolv', p)]
    # Do not demand all evidence in one Massive excerpt: related agreement
    # definitions and amendments are often split into separate excerpts.
    # Reject only the clear repayment-only case; ambiguous cases need review.
    term_change = re.search(r'extends?\s+(?:the\s+)?term\s+loan|term\s+(?:b\s+)?loan.{0,100}extends?', text)
    repayment_only = paragraphs and all(
        re.search(r'(?:partially\s+)?repay.{0,180}revolving\s+credit', p)
        and not re.search(r'(?:amend|restat|renew|extend|replac).{0,100}revolv|revolv.{0,100}(?:amend|restat|renew|extend|replac)', p)
        for p in paragraphs)
    if term_change and repayment_only:
        return 'term_loan_change_revolver_repayment_only'
    return ''
