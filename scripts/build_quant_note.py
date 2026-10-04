"""Build the submission note from committed aggregates; never load market data.

Install requirements-report.txt, then: python scripts/build_quant_note.py
The Markdown source and PDF are generated together from the same content.
"""
from pathlib import Path
import json
from xml.sax.saxutils import escape
import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parents[1]
M = json.loads((ROOT / 'submission_final_metrics.json').read_text())
R = M['fixed_horizon_detail']
OUT = ROOT / 'submission'
OUT.mkdir(exist_ok=True)
font_dir = Path(reportlab.__file__).parent / 'fonts'
pdfmetrics.registerFont(TTFont('NoteSans', str(font_dir / 'Vera.ttf')))
pdfmetrics.registerFont(TTFont('NoteSansBold', str(font_dir / 'VeraBd.ttf')))
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyNote', fontName='NoteSans', fontSize=9.3, leading=12.2, spaceAfter=6))
styles.add(ParagraphStyle(name='SmallNote', fontName='NoteSans', fontSize=7.6, leading=9.5, spaceAfter=5))
styles.add(ParagraphStyle(name='SectionNote', fontName='NoteSansBold', fontSize=10.5, leading=13, spaceBefore=8, spaceAfter=5, textColor=colors.HexColor('#18394a')))
styles.add(ParagraphStyle(name='TitleNote', fontName='NoteSansBold', fontSize=19, leading=22, spaceAfter=7, textColor=colors.HexColor('#18394a')))
story=[]; md=[]
def text(s,style='BodyNote'):
 story.append(Paragraph(escape(s),styles[style])); md.extend([s,''])
def heading(s):
 story.append(Paragraph(escape(s),styles['SectionNote']));md.extend(['## '+s,''])
def table(headers,rows,widths):
 data=[[Paragraph(escape(str(x)),styles['SmallNote']) for x in row] for row in [headers]+rows]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9f1f3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#54747e')),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#dce4e7')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),2)]))
 story.append(t);story.append(Spacer(1,5))
 md.extend(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |'])
 md.extend('| '+' | '.join(str(x) for x in row)+' |' for row in rows);md.append('')
text('Do fresh leadership 8-Ks reward put sellers?','TitleNote')
text('Gator Quant Hacks 2026 / Massive Trade the 8-K / Final quant note / October 4, 2026','SmallNote')
text('Decision: do not deploy the proposed signal. We did not find evidence that fresh leadership-change filings generated a robust after-cost advantage for cash-secured put sellers over ordinary days. The negative result is a test of the declared payoff, not proof that buying protection would work.')
heading('Question, economic rationale and frozen trade')
text('A newly disclosed management disruption could increase demand for downside insurance beyond its economic risk. We tested whether this overpayment favors selling a 5% out-of-the-money cash-secured put after the filing session, using 90-180 calendar-day expiries targeting 120 days. The Massive category family comprises CEO appointment/departure, CFO appointment/departure and executive-officer appointment. The pre-outcome primary contrast is fresh minus stale; fresh versus ordinary days is a separate comparator. The headline equally averages differences at 21 sessions, 42 sessions and expiry; it is neither an absolute trade return nor an annualized return.')
heading('Data, event timing and inference')
text('The study uses a static top-100 universe, Massive categorized disclosures, as-of option references and historical daily option bars. Spot is inferred by put-call parity. Filing acceptance timestamps shift after-close events to the next session; entry is its close. Fresh means at most one trading session from the SEC EDGAR CONFORMED PERIOD OF REPORT date to this adjusted filing date. One event per ticker/session and undated exclusions follow the original implementation. The metadata proxy cannot verify the first public disclosure. F1 uses no JEV treatment arm. Earlier work used committed TypeSafe/System One JEV probabilities and rules for uncached text. Optional API score generation is implemented; no System One call was made during submission QA.')
text('In-sample event dates are 2024-2025; the already-reported historical OOS window is January-August 2026. Ordinary-day controls use the same tickers, at least 30 days from an event, with 120 draws per window before pricing exclusions. The original difference calculation independently resamples each group 2,000 times (seed 1) for percentile 95% intervals. It is not issuer-clustered. The hypothesis precedes the first recorded outcomes, but protocol date ranges were corrected after OOS; exact-window preregistration and independent tag custody are not established. Historical hashes document this limitation.')
heading('Table 1. Three-horizon gross differences and denominators')
labels=['Fresh - ordinary','Stale - ordinary','Fresh - stale (primary)']
rows=[]
for i,r in enumerate(M['f1_reported_comparisons']):
 val=f"{r['gross_edge_fraction_exact']*100:+.2f}%"
 rows.append(['IS' if i<3 else 'Reported OOS',labels[i%3],val,str(r['n_reported_max_per_horizon']),str([1,0,0,0,2,2][i])+'/3'])
table(['Window','Contrast','Gross diff.','Max N(a)','CI excludes 0'],rows,[76,163,80,64,133])
text('N(a) is the maximum valid group-A event count among the three headline horizons, not issuer N or a common matched set. Discovery fresh/stale counts are 62/108 IS and 27/42 reported OOS; valid headline maxima are 55/95 and 25/40. Capacity N=56/25 precedes horizon eligibility; year counts 27/32/27 cover all evaluated settings. These populations differ. Control-valid N, issuer N, common matched N and numeric F1 interval endpoints are unavailable. Source: original ledger aggregate rows 87-89, 95-97; authoritative facts.','SmallNote')
story.append(PageBreak());md.extend(['<!-- Page 2 -->',''])
heading('Table 2. All fixed-horizon gross differences (% of spot notional)')
rows=[]
for h in [1,2,3,5,10,21,42,63,'exp']:
 vals=[]
 for w,c in [(w,c) for w in ('in_sample','reported_oos') for c in ('fresh_vs_ordinary','stale_vs_ordinary','fresh_minus_stale')]:
  r=next(x for x in R if x['window']==w and x['comparison']==c and x['horizon']==h)
  vals.append(r['display_value'])
 rows.append(['Expiry' if h=='exp' else str(h)]+vals)
table(['Sessions','F-O IS','S-O IS','F-S IS','F-O OOS','S-O OOS','F-S OOS'],rows,[60,76,76,76,76,76,76])
text('F-O = fresh minus ordinary; S-O = stale minus ordinary; F-S = fresh minus stale (primary). All 54 cells are direct recovery of saved original displays at commit 5871597e3e, cells 44/45, rounded to 0.01 percentage point; no chart or average reconstruction. * records an original interval excluding zero, not its endpoints. Absolute signal/control gross means, historical net differences and horizon-specific N remain unavailable.','SmallNote')
heading('Sensitivity, costs and trade realism')
text('All 18 reported neighbors per window have negative gross fresh-versus-ordinary differences: three expiry buckets x three moneyness levels x pre/post entry. Pre-entry settings are descriptive diagnostics, not an executable filing-triggered strategy. No neighbor was selected. Dropping the best three IS fresh events leaves a -0.45% gross difference versus ordinary days. The primary IS contrast fails the ordered gate; later significance at two primary OOS horizons does not rescue it. The secondary OOS comparison has zero significant headline horizons, so only its negative sign repeats.')
heading('Table 3. Costs, portfolio and volume-based capacity')
c=M['costs_and_capacity']
table(['Quantity','In-sample','Reported OOS'],[
 ['Median assumed cost / side',str(c['median_cost_bps_per_side']['in_sample'])+' bps',str(c['median_cost_bps_per_side']['reported_oos'])+' bps'],
 ['Absolute annualized net portfolio return, 1x / 2x costs','-1.2% / -2.0%','-3.0% / -4.6%'],
 ['Median pre-entry option volume / session','29 contracts','18 contracts'],
 ['Rough ten-position capacity at 10% volume participation','~$500,000','~$390,000'],
 ],[267,124,125])
text('Costs assume 5% of entry premium per side; they are not observed bid-ask spreads. Portfolio holds for 21 sessions with 10% spot-notional sizing per event; annualization is mean daily return x252, not CAGR. The implementation has no enforced ten-position cap (observed maxima 7/8). Capacity uses volume in the ten calendar days through the pre-event session and spot notional, not strike collateral or guaranteed fills. Historical net portfolio performance is distinct from the unavailable net event-control contrast. Source: runs/FINDINGS.md, runs/EXTRAS.md and ledger aggregate rows 123/124.','SmallNote')
heading('Interpretation, limitations and sealed-window expectation')
text('The proposed premium-selling payoff is unsupported. An exploratory directional-loss explanation does not establish causal mispricing: the static September-2026 universe introduces selection/look-ahead risk, public-news timing is imperfect, observations can overlap, bootstrap inference ignores issuer clustering and daily-bar marks do not prove executable fills. Portfolio forward-filling can extend stale marks. Short OOS and unavailable endpoints constrain precision. The separate 18-category variance-premium screen had zero BH q=.10 selections; it is context, not a replacement strategy.')
text('Judges\' sealed dates and outcomes remain unknown and untouched. Our expectation is fragility of any precise magnitude and no demonstrated robust after-cost advantage; this is a submission-time expectation, not a pre-OOS forecast. Default notebook Run All reproduces the published aggregates without a key. Authorized custom dates invoke the unchanged measurement functions with source-integrity checks; no new research outcome was generated during submission QA. Live entitlement verification is pending because no key is configured.')
text('Reproducibility: GQH_MASSIVE_FINAL.ipynb; submission_authoritative_facts.json; docs/RESEARCH_PROVENANCE.md; SUBMISSION_QA_CHECKLIST.md. Final sources are committed aggregates only. Licensed API payloads and caches are excluded.','SmallNote')
text('Supporting remote research: priced earnings, governance-resolution CSP and covered-call tests also failed their original gates. Actual event/control net means, costs and full sensitivity are in submission/evidence/remote_experiments/README.md. Experiments 11-13 remain unpriced supporting history; numbered artifacts are unavailable at the fetched tip.','SmallNote')
def footer(canvas,doc):
 canvas.setFont('NoteSans',8);canvas.setFillColor(colors.HexColor('#54747e'));canvas.drawString(48,29,'Gator Quant Hacks 2026 | Failed premium-selling hypothesis | Historical aggregate evidence');canvas.drawRightString(564,29,str(doc.page))
SimpleDocTemplate(str(OUT/'QUANT_NOTE.pdf'),pagesize=letter,leftMargin=48,rightMargin=48,topMargin=39,bottomMargin=43,title='Do fresh leadership 8-Ks reward put sellers?',author='Gator Quant Hacks team').build(story,onFirstPage=footer,onLaterPages=footer)
(OUT/'QUANT_NOTE.md').write_text('\n'.join(md)+'\n')
print('Built submission/QUANT_NOTE.pdf and matching Markdown source')
