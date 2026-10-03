"""Source-backed 3B audit tooling; no model, market or future-document calls.

Candidate passages aid analyst review. They are not automatically treated as
evidence: approved spans and officer binding must be recorded explicitly.
"""
import argparse
import json
import re

from departure_experiment import freeze
from jev_experiment import digest, ROOT
import full_source_experiment as recovery

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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['candidates','view'])
    parser.add_argument('--start',type=int,default=0)
    parser.add_argument('--end',type=int,default=10)
    args = parser.parse_args()
    if args.stage=='candidates':
        stage_candidates()
    else:
        review_view(args.start,args.end)
