"""Source-backed 3B audit tooling; no model, market or future-document calls.

Candidate passages aid analyst review. They are not automatically treated as
evidence: approved spans and officer binding must be recorded explicitly.
"""
import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from departure_experiment import freeze
from jev_experiment import digest, ROOT
import full_source_experiment as recovery
import full_source_annotations as review

OUTPUT = recovery.OUTPUT
# Exact target identities transcribed from frozen short departure excerpts,
# before assessing full-source sufficiency. Preserve multiple departures.
TARGETS = '''Rivera
Kremer
Roualet
Alford
Flessner
Liu|Mulligan
Tanner
Garnick
Browdy
McMahon
Karczmer
Macklon
White
Garnick
Regelman
Roualet
Carter
Hoovel
Young
Holston|Cox|Timko
Berlinski
Baglino
McElroy
Funck
Bondy
Sharritts
Clark|Martinetto
Silliman
Gorman
Carey
ten Hoedt
Daugherty|Shook
Weidemanis
Welsh
Dolsten
Timm
Parsey
Garfield
Sharritts
Peng
Desai
Hoovel
Hearne
Kotwal
Fasolo
Okpara
Conway
Colbert
Goel
Panikar
Smith
Panikar
Gruber
Kumar
Thompson
Buckbee
Keating
Schock
Screven
Wiedman
Kim
Young
Delk
Williams
Weiss
Belsky
Hearne
Galanti
Hayes
Millham
Steele
Walsh|Scally
Leung
Gibbons
Pope
Bless
Planishek
Goel
McDonald
Patterson
Johnston Holthaus|Zinsner
May
Kirk
Akram
McKee
Bazzano
Smith
Cianfrocco
Schell
Allen
O'Neill
Janson
Whited|Rynaski
D'Ambrosia
Hennington|Tu
Salmon
Parameswaran
Gore-Coty
Lerman
Hines
Narain|Beatty|Azagury
Krishnasamy
Williams
Hirawat
Brown
Ellis
Miller
Strauss
Keith
Wilfong
Wade
Boldea
Carter
Martin
Ewaldsson|Field
Reed
Puech
D'Emic
Buckminster
Templeton
Knowles
Smith
Meyer
Neal
Telman
Hans|Knox|Koder|Schimpf
Williams
Kalathur
Adams
Moss
Lee
Davis'''.splitlines()


def name_pattern(name):
    if name == 'May':
        return re.compile(r'\b(?:James\s+M\.?\s+May|Mr\.?\s+May)\b', re.I)
    if name == 'Field':
        return re.compile(r'\b(?:Callie\s+Field|Ms\.?\s+Field)\b', re.I)
    return re.compile(r'\b'+re.escape(name).replace(r'\ ', r'[\s-]+').replace("'", "['’]")+r'\b', re.I)


def sections(text):
    heads = list(re.finditer(r'(?im)^\s*Item\.?\s*(\d\.\d{2})(?:\.|\b)', text))
    result = []
    for i, heading in enumerate(heads):
        end = heads[i+1].start() if i+1 < len(heads) else len(text)
        signature = re.search(r'(?im)^SIGNATURES?\s*$', text[heading.start():end])
        if signature:
            end = heading.start()+signature.start()
        result.append({'item':heading.group(1), 'start':heading.start(), 'end':end})
    return result


def span(document, source, start, end):
    text = document['text']
    quote = text[start:end]
    if not quote.strip() or start < 0 or end > len(text):
        raise ValueError('Invalid source span.')
    return {'document':document['filename'], 'document_type':document['type'],
        'source':source, 'start':start, 'end':end, 'quote':quote,
        'normalized_document_sha256':digest(text)}


def stage_candidates():
    cohort = recovery.verify()
    if len(TARGETS) != len(cohort):
        raise ValueError('Target transcription must cover132 original excerpts.')
    packets = []
    for i, event in enumerate(cohort):
        targets = TARGETS[i].split('|')
        if not all(name_pattern(name).search(event['supporting_text']) for name in targets):
            raise ValueError('Target identity not present in frozen excerpt: '+event['accession_number'])
        parsed = json.loads((OUTPUT/'parsed'/f'{event["accession_number"]}.json').read_text())
        packet = {'index':i, 'accession':event['accession_number'], 'ticker':event['ticker'],
            'cik':event['cik'], 'filing_date':event['filing_date'], 'company':parsed.get('company'),
            'filing_timestamp':parsed.get('filing_timestamp'), 'original_url':event['original_url'],
            'short_excerpt':event['supporting_text'], 'experiment3_qualified':event['experiment3_qualified'],
            'targets':targets,'retrieved':parsed['retrieved'],'sources':[], 'incorporation_references':[]}
        if not parsed['retrieved']:
            packet['retrieval_error'] = parsed['error']
            packets.append(packet)
            continue
        main = next(d for d in parsed['documents'] if d['type']=='8-K' and d['sequence']=='1')
        blocks = sections(main['text'])
        core = [b for b in blocks if b['item']=='5.02']
        if not core:
            raise ValueError('Ambiguous/missing Item5.02 boundaries: '+event['accession_number'])
        item = '\n'.join(main['text'][b['start']:b['end']] for b in core)
        packet['item_length'] = sum(b['end']-b['start'] for b in core)
        for b in core:
            packet['sources'].append(span(main,'FULL_ITEM_5_02',b['start'],b['end']))
        # Same-filing incorporation is a candidate only when expressly stated;
        # analyst must verify the reference actually incorporates that section.
        if re.search(r'incorporat\w*\s+(?:herein\s+)?by reference', item, re.I):
            for other in blocks:
                if other['item'] != '5.02' and re.search(r'Item\s*'+re.escape(other['item']),item,re.I):
                    packet['sources'].append(span(main,'OTHER_8K_SECTION',other['start'],other['end']))
                    packet['incorporation_references'].append(other['item'])
        # Exhibit relevance is reviewed explicitly, not inferred from numbering.
        for document in parsed['documents']:
            if not document['type'].startswith('EX-') or document['type'].startswith(('EX-101','EX-104')):
                continue
            if document['type'].startswith('EX-99') or any(name_pattern(n).search(document['text']) for n in targets):
                source = 'EXHIBIT_99_1' if document['type']=='EX-99.1' else 'OTHER_EXHIBIT'
                packet['sources'].append(span(document,source,0,len(document['text'])))
        packets.append(packet)
    freeze(OUTPUT/'candidate_packets.json', packets)
    print('Candidate source packets:',len(packets), flush=True)


def review_view(start, end):
    packets = json.loads((OUTPUT/'candidate_packets.json').read_text())
    for packet in packets[start:end]:
        print(f'\nEVENT {packet["index"]} {packet["ticker"]} TARGETS {"|".join(packet["targets"])} {packet["filing_date"]}')
        print('SHORT:',packet['short_excerpt'])
        for number, source in enumerate(packet['sources']):
            print(f'SOURCE S{number} {source["source"]} {source["document"]}')
            lines = source['quote'].splitlines()
            anchors = {j for j,line in enumerate(lines) if any(name_pattern(n).search(line) for n in packet['targets']) or re.search(r'succeed|successor|interim|search|transition|responsibilit|appoint',line,re.I)}
            show = {k for j in anchors for k in range(max(0,j-1),min(len(lines),j+3))}
            for j,line in enumerate(lines):
                # Primary section is shown in full. Relevant exhibit windows
                # are review aids only; complete exhibit text is retained.
                if j in show:
                    if len(line)>2800:
                        print(f'L{j} [long {len(line)}chars; inspect packet directly] '+line[:2800])
                    else:
                        print(f'L{j} '+line)


FIELDS = ['officer_identified','officer_role_explicit','departure_explicit',
    'departure_effective_date','announcement_date','notice_date','effective_immediately',
    'future_effective_date','successor_named','successor_role_explicit',
    'successor_effective_date','interim_successor_named','permanent_successor_named',
    'search_process','transition_period','departure_reason','succession_arrangement']
TIERS = ['FULL_ITEM_5_02','OTHER_8K_SECTION','EXHIBIT_99_1','OTHER_EXHIBIT']
TIMING_FIELDS = ['departure_effective_date','announcement_date','notice_date',
    'effective_immediately','future_effective_date','transition_period']
SUCCESSION_FIELDS = ['successor_named','successor_role_explicit','successor_effective_date',
    'interim_successor_named','permanent_successor_named','search_process','succession_arrangement']


def source_reference(packet, ref):
    """Convert reviewed line selection to exact original normalized offsets."""
    number, first, last = ref
    source = packet['sources'][number]
    lines = source['quote'].splitlines(keepends=True)
    if not 0 <= first <= last < len(lines):
        raise ValueError(f'Invalid reviewed lines: {packet["index"]} {ref}')
    start = source['start'] + sum(map(len,lines[:first]))
    end = source['start'] + sum(map(len,lines[:last+1]))
    quote = ''.join(lines[first:last+1])
    if source['quote'][start-source['start']:end-source['start']] != quote:
        raise ValueError('Line-to-character provenance mismatch.')
    return dict(source, start=start, end=end, quote=quote,
        url=packet['original_url'], candidate_source_index=number,
        document_url=f'https://www.sec.gov/Archives/edgar/data/{int(packet["cik"])}/{packet["accession"].replace("-", "")}/{source["document"]}',
        selected_lines=[first,last])


def target_reference(packet, officer):
    override = review.PRIMARY_OVERRIDES.get((packet['index'],officer))
    if override:
        return source_reference(packet, override)
    for n, source in enumerate(packet['sources']):
        if source['source'] != 'FULL_ITEM_5_02':
            continue
        lines = source['quote'].splitlines()
        hits = [j for j,line in enumerate(lines) if name_pattern(officer).search(line)]
        if hits:
            j = hits[0]
            # Preserve wrapped prose and the preceding date-introduction line.
            return source_reference(packet,(n,max(0,j-2),min(len(lines)-1,j+4)))
    return None


def supported(value, citation):
    if citation is None:
        raise ValueError('Positive/negative fact needs an explicit citation.')
    return {'status':'supported','value':value,'citations':[citation]}


def unknown(reason='Not explicitly supported for this officer in the allowed input.'):
    return {'status':'unsupported','value':None,'citations':[], 'reason':reason}


def arrangement(index, officer, short=False):
    candidate = (review.SHORT_SUCCESSION if short else review.SUCCESSION).get(index)
    return candidate.get(officer) if isinstance(candidate,dict) else candidate


def officer_fields(packet, officer, short=False):
    i = packet['index']
    facts = {name:unknown() for name in FIELDS}
    if short:
        text = packet['short_excerpt']
        citation = {'document':'original_Massive_supporting_text','document_type':'MASSIVE_EXCERPT',
            'source':'MASSIVE_EXCERPT','start':0,'end':len(text),'quote':text,
            'normalized_document_sha256':digest(text),'url':packet['original_url']}
    else:
        citation = target_reference(packet,officer)
    if citation is None or not name_pattern(officer).search(citation['quote']):
        return {'officer':officer,'fields':facts,'scope':False,'timing':False,
            'succession':False,'joint':False,'note':review.NOTES.get(i)}
    text = citation['quote']
    facts['officer_identified'] = supported(officer,citation)
    scope = (i not in review.SHORT_SCOPE_UNKNOWN if short
             else officer not in review.FULL_SCOPE_UNKNOWN.get(i,set()))
    if scope:
        facts['officer_role_explicit'] = supported(True,citation)
    if i == 123:
        facts['departure_explicit'] = supported('future appointment cancelled; not an employee departure',citation)
    elif i == 125:
        facts['departure_explicit'] = supported('executive-officer designation ends; employee exit not disclosed',citation)
    else:
        facts['departure_explicit'] = supported(True,citation)
    timing = i not in (review.SHORT_TIMING_UNKNOWN if short else review.FULL_TIMING_UNKNOWN)
    if short and i == 71 and officer == 'Scally':
        timing = False  # Undated replacement is not an explicit timing fact.
    if short and i == 114 and officer == 'Field':
        timing = True
    if not short and i == 114 and officer == 'Field':
        timing = True
    # Fine-grained fields below are descriptive; source sufficiency uses the
    # separately reviewed timing/scope/arrangement annotations, not regex hits.
    # Restrict departure-side extraction to sentences containing the target or
    # its personal pronoun, excluding unrelated biographies and appointments.
    target_lines = [line for line in text.splitlines()
                    if name_pattern(officer).search(line) or re.search(r'\b(?:Mr|Ms|Dr)\.?\s+'+re.escape(officer.split()[-1]),line,re.I)]
    bound = ' '.join(target_lines)
    if not short:
        dated = review.DEPARTURE_TIMING[i]
        dated = review.DEPARTURE_TIMING_BY_OFFICER.get((i,officer),dated)
        if dated:
            facts['departure_effective_date'] = supported(dated,citation)
    # Aliases and wrapped dates require the approved joined source context.
    actual = review.VARIATION_DATES.get(i)
    if isinstance(actual,dict):
        actual = actual.get(officer)
    if actual and not short:
        if actual > packet['filing_date']:
            facts['future_effective_date'] = supported(actual,citation)
    if re.search(r'(?:retir\w*|step\w* down|resign\w*|cease serv\w*|depart\w*)[^.;]{0,100}effective immediately',bound,re.I):
        facts['effective_immediately'] = supported(True,citation)
    calendar = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+20\d{2}'
    announcement = re.search(r'On ('+calendar+r')[^.;]{0,170}?announced',bound,re.I)
    if announcement:
        facts['announcement_date'] = supported(announcement.group(1),citation)
    notice = re.search(r'On ('+calendar+r')[^.;]{0,170}?(?:informed|notified|provided notice)',bound,re.I)
    if notice:
        facts['notice_date'] = supported(notice.group(1),citation)
    transition = re.search(r'(?:remain|continu\w*|assist|transition|advis\w*)[^.;]{0,160}(?:until|through|period|months|transition)[^.;]*',bound,re.I)
    if transition:
        facts['transition_period'] = supported(transition.group(0),citation)
    if i in review.REASON_PRESENT:
        rv = review.REASON_VALUES[i]
        if not short or all(part.lower() in bound.lower() for part in rv.split('; ')):
            facts['departure_reason'] = supported(rv,citation)
    if not short and i in review.REASON_EXHIBITS:
        rc = source_reference(packet,review.REASON_EXHIBITS[i])
        facts['departure_reason'] = supported(rc['quote'].strip(),rc)
    specified = arrangement(i,officer,short)
    succession = specified is not None
    if succession:
        if short:
            kind, sc = specified, citation
        else:
            *ref, kind = specified
            sc = source_reference(packet,ref)
        facts['succession_arrangement'] = supported(kind,sc)
        named = kind in ['permanent','interim','mixed'] or (kind=='reassignment' and not (i==18 or (i==26 and officer=='Martinetto')))
        if named:
            facts['successor_named'] = supported(True,sc)
            if not short or i not in [5,75,80,104,109,114]:
                facts['successor_role_explicit'] = supported(True,sc)
        if kind in ['permanent','mixed']:
            facts['permanent_successor_named'] = supported(True,sc)
        if kind in ['interim','mixed']:
            facts['interim_successor_named'] = supported(True,sc)
        if kind == 'search' or (kind=='interim' and re.search(r'\bsearch\b',sc['quote'],re.I)):
            facts['search_process'] = supported(True,sc)
        if kind == 'unfilled':
            facts['successor_named'] = supported(False,sc)
        if not short:
            dated = review.SUCCESSOR_DATES.get(i)
            if isinstance(dated,dict):dated = dated.get(officer)
            if dated:
                facts['successor_effective_date'] = supported(dated,sc)
                if i == 119:
                    facts['successor_effective_date']['citations'].append(source_reference(packet,(1,7,9)))
    return {'officer':officer,'fields':facts,'scope':scope,'timing':timing,
        'succession':succession,'joint':scope and timing and succession,
        'timing_evidence':supported('explicit dated exit, immediate handover, or advance/conditional transition',citation) if timing else unknown(),
        'note':review.NOTES.get(i)}


def coverage(officers, allowed=None):
    def available(officer, key):
        if not officer[key]:
            return False
        if allowed is None:
            return True
        field = {'scope':'officer_role_explicit','timing':'timing_evidence','succession':'succession_arrangement'}[key]
        fact = officer['timing_evidence'] if key=='timing' else officer['fields'][field]
        return any(c['source'] in allowed for c in fact['citations'])
    result = {key:all(available(o,key) for o in officers) for key in ['scope','timing','succession']}
    result['joint'] = all(result.values())
    return result


def population(rows):
    counts = Counter(r['cik'] for r in rows)
    n = len(rows)
    return {'filings':n,'companies':len(counts),'percent_of_cohort':n/132*100,
        'effective_company_n':n*n/sum(v*v for v in counts.values()) if n else 0,
        'max_company_share':max(counts.values())/n if n else 0}


def source_gate(rows):
    spec = recovery.PROTOCOL['source_gate']
    eligible = [r for r in rows if r['coverage']['full']['joint']]
    pop = population(eligible)
    groups = {name:[] for name in ['on_or_before','future_14_days','settled','unresolved']}
    for r in eligible:
        dates = review.VARIATION_DATES.get(r['index'])
        dates = list(dates.values()) if isinstance(dates,dict) else [dates] if dates else []
        delta = [(date.fromisoformat(d)-date.fromisoformat(r['filing_date'])).days for d in dates]
        if any(d<=0 for d in delta):groups['on_or_before'].append(r)
        if any(d>=14 for d in delta):groups['future_14_days'].append(r)
        kinds = [o['fields']['succession_arrangement']['value'] for o in r['full_officers']]
        if any(k in ['permanent','reassignment','mixed'] for k in kinds):groups['settled'].append(r)
        if any(k in ['interim','search','unresolved','unfilled','mixed'] for k in kinds):groups['unresolved'].append(r)
    stats = {name:population(items) for name,items in groups.items()}
    failed = [r for r in rows if not r['item_5_02_recovered']]
    checks = {'joint_filings':pop['filings']>=spec['min_joint_scope_filings'],
        'companies':pop['companies']>=spec['min_companies'],
        'company_effective_n':pop['effective_company_n']>=spec['min_company_effective_n'],
        'company_concentration':pop['max_company_share']<=spec['max_company_share'],
        'retrieval_failure_fraction':len(failed)/len(rows)<=spec['max_retrieval_or_package_failure_fraction']}
    for name,group in stats.items():
        kind = 'timing' if name in ['on_or_before','future_14_days'] else 'succession'
        checks[name+'_filings'] = group['filings']>=spec['min_each_'+kind+'_fact_group']
        checks[name+'_companies'] = group['companies']>=spec['min_each_'+kind+'_group_companies']
    return {'decision':'source_feasibility_passed' if all(checks.values()) else 'source_feasibility_failed',
        'checks':checks,'eligible':pop,'variation_groups':stats,
        'variation_accessions':{k:[r['accession'] for r in v] for k,v in groups.items()},
        'retrieval_failure_fraction':len(failed)/len(rows),'frozen_thresholds':spec}


def stage_audit():
    recovery.verify()
    packets = json.loads((OUTPUT/'candidate_packets.json').read_text())
    rows = []
    for packet in packets:
        officers = [officer_fields(packet,o) for o in packet['targets']]
        short = [officer_fields(packet,o,short=True) for o in packet['targets']]
        tiers = {name:coverage(officers,TIERS[:j+1]) for j,name in enumerate(TIERS)}
        full = coverage(officers)
        used_exhibits = {c['document']:c for o in officers for f in [*o['fields'].values(),o.get('timing_evidence',unknown())]
                         for c in f['citations'] if c['document_type'].startswith('EX-')}
        row = {k:packet[k] for k in ['index','accession','ticker','cik','company','filing_date','filing_timestamp','original_url','targets','experiment3_qualified']}
        row.update(item_5_02_recovered=packet['retrieved'],item_5_02_length=packet.get('item_length',0),
            incorporated_sections=packet['incorporation_references'],
            relevant_exhibits=[{'document':c['document'],'type':c['document_type'],'source':c['source']} for c in used_exhibits.values()],
            short_officers=short,full_officers=officers,
            coverage={'short':coverage(short),**tiers,'full':full},note=review.NOTES.get(packet['index']))
        row['reason_for_insufficiency'] = [o['officer']+': '+', '.join(k for k in ['scope','timing','succession'] if not o[k]) for o in officers if not o['joint']]
        rows.append(row)
    (OUTPUT/'source_audits_draft.json').write_text(json.dumps(rows,indent=2)+'\n')
    gate = source_gate(rows)
    # This is a draft until the deterministic stratified validation is complete.
    (OUTPUT/'source_gate_draft.json').write_text(json.dumps(gate,indent=2)+'\n')
    print(json.dumps(gate,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['candidates','view','audit'])
    parser.add_argument('--start',type=int,default=0)
    parser.add_argument('--end',type=int,default=10)
    args = parser.parse_args()
    if args.stage=='candidates':
        stage_candidates()
    elif args.stage=='view':
        review_view(args.start,args.end)
    else:
        stage_audit()
