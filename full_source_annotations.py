"""Outcome-blind analyst adjudications for the original 132 filing packets.

Indices refer to the immutable original cohort, not a newly selected sample.
Source/line references select reviewed passages in candidate_packets.json.
The audit builder validates exact offsets and target identity. Silence is never
encoded as a negative fact. A dated handover can support timing without proving
the employee's ultimate exit date; those two fields remain separate.
"""

# Named successor/coverage, explicitly unsettled arrangements, or reassignment.
# Values: source index, first line, last line (inclusive), disclosed arrangement.
SUCCESSION = {
    1:(0,2,2,'permanent'), 2:(1,11,12,'permanent'),
    5:{'Liu':(0,4,4,'unresolved'),'Mulligan':(0,1,3,'permanent')},
    7:(2,3,5,'permanent'),16:(0,1,2,'permanent'),18:(0,19,22,'reassignment'),
    19:{'Timko':(0,1,2,'permanent')},24:(0,1,1,'permanent'),
    25:(0,1,3,'reassignment'),
    26:{'Clark':(1,22,25,'permanent'),'Martinetto':(1,18,21,'reassignment')},
    31:{'Daugherty':(1,8,8,'reassignment'),'Shook':(1,7,7,'permanent')},
    33:(1,10,13,'reassignment'),34:(0,1,1,'search'),35:(0,2,2,'permanent'),
    36:(0,3,7,'search'),39:(1,12,14,'reassignment'),41:(0,1,1,'permanent'),
    42:(0,2,2,'reassignment'),43:(1,9,10,'search'),44:(1,7,8,'permanent'),
    45:(0,1,5,'interim'),48:(0,1,1,'unfilled'),49:(0,2,3,'permanent'),
    50:(0,2,4,'permanent'),52:(1,11,13,'permanent'),53:(0,2,2,'permanent'),
    54:(0,1,1,'permanent'),55:(0,2,4,'permanent'),62:(0,2,7,'permanent'),
    63:(1,8,8,'unresolved'),64:(0,1,1,'permanent'),68:(0,2,5,'permanent'),
    69:(0,2,5,'permanent'),71:{'Walsh':(0,1,4,'permanent')},
    72:(0,2,4,'unresolved'),75:(0,1,2,'permanent'),76:(0,1,2,'mixed'),
    78:(0,1,1,'permanent'),79:(0,4,9,'interim'),
    80:(0,2,19,'permanent'),81:(0,4,8,'permanent'),82:(0,1,2,'permanent'),
    85:(0,1,2,'permanent'),86:(0,1,1,'permanent'),87:(0,1,1,'permanent'),
    90:(1,9,14,'reassignment'),91:(1,25,27,'permanent'),
    92:{'Rynaski':(0,7,8,'permanent')},93:(0,2,3,'permanent'),
    95:(0,1,1,'permanent'),97:(0,3,19,'permanent'),98:(0,5,5,'unresolved'),
    99:(0,1,2,'permanent'),
    100:{'Narain':(1,5,17,'permanent'),'Beatty':(1,5,17,'permanent'),
         'Azagury':(1,5,17,'permanent')},
    102:(0,2,3,'permanent'),103:(1,1,6,'permanent'),104:(0,1,5,'permanent'),
    106:(0,1,2,'permanent'),107:(0,2,3,'permanent'),109:(0,1,3,'permanent'),
    111:(0,1,2,'permanent'),112:(0,2,3,'interim'),113:(0,1,2,'permanent'),
    114:{'Ewaldsson':(0,3,4,'permanent')},115:(1,14,18,'permanent'),
    117:(0,2,2,'unresolved'),119:(0,2,5,'permanent'),120:(0,2,3,'permanent'),
    122:(0,1,1,'search'),126:(1,9,11,'reassignment'),128:(0,2,4,'permanent'),
    129:(0,2,2,'permanent'),130:(0,3,9,'permanent'),
}

# Full input timing failures: no disclosed exit/handover date or advance period.
# For 71 the original package does not contain the second target, Scally.
# 114 states Ewaldsson's retirement but not when he hands over to Saw.
FULL_TIMING_UNKNOWN = {66,114}
SHORT_TIMING_UNKNOWN = {66,69,79,80,97,100,102,109,114,115}
FULL_SCOPE_UNKNOWN = {19:{'Holston','Cox'},71:{'Scally'}}
SHORT_SCOPE_UNKNOWN = {66,100}

# Short inputs explicitly describe these succession/coverage arrangements.
# The identity of Fiddelke/Okpara alone is not a sufficient role description,
# but the departing officer's clause explicitly binds the appointment/transition.
SHORT_SUCCESSION = {
    5:{'Liu':'unresolved','Mulligan':'permanent'},18:'reassignment',34:'search',
    36:'search',41:'permanent',48:'unfilled',53:'permanent',
    71:{'Walsh':'permanent','Scally':'permanent'},72:'unresolved',75:'permanent',
    76:'interim',80:'permanent',98:'unresolved',102:'permanent',104:'permanent',
    109:'permanent',114:{'Ewaldsson':'permanent'},117:'unresolved',122:'search',
}

# Departure dates used ONLY for the frozen factual variation screen. Dates are
# deliberately omitted where only ultimate retirement or a successor date is
# known, or where a month/quarter/conditional period is stated. Coverage does
# not require an exact calendar day; variation groups do.
VARIATION_DATES = {
    1:'2024-01-07',2:'2024-04-30',5:{'Mulligan':'2024-02-04'},7:'2024-04-01',
    16:'2024-06-30',18:'2024-06-30',24:'2024-06-04',25:'2024-05-15',
    26:'2024-06-28',31:'2024-08-31',33:'2024-07-31',39:'2024-08-30',
    41:'2024-10-01',42:'2024-10-01',44:'2024-10-01',45:'2024-09-10',
    48:'2025-03-31',49:'2024-11-01',50:'2024-11-18',52:'2025-04-01',
    54:'2025-02-03',55:'2025-03-01',62:'2025-03-01',63:'2025-02-03',
    64:'2025-01-30',68:'2025-04-30',69:'2025-03-21',75:'2025-03-01',
    78:'2025-05-01',80:'2025-03-18',81:'2025-05-22',82:'2025-05-02',
    85:'2025-04-30',86:'2025-04-23',87:'2025-05-06',90:'2025-05-02',
    91:'2025-06-30',93:'2025-07-31',95:'2025-05-21',99:'2025-06-30',
    102:'2025-07-25',103:'2025-08-01',104:'2025-09-02',107:'2025-09-01',
    109:'2025-09-22',111:'2025-08-31',112:'2025-09-05',113:'2025-08-25',
    115:'2025-11-03',119:'2025-12-31',120:'2026-02-28',126:'2025-12-05',
    128:'2026-03-01',129:'2026-03-31',130:'2026-03-01',
}

# Explicit context joins needed when the short passage uses an undefined date
# alias, the officer is only in an exhibit, or a contemporaneous handover is the
# timing evidence. These are not substituted employee termination dates.
PRIMARY_OVERRIDES = {
    (26,'Clark'):(1,22,25),
    (31,'Daugherty'):(1,8,8),(31,'Shook'):(1,7,7),
    (69,'Millham'):(0,2,5),(79,'Patterson'):(0,4,9),
    (80,'Johnston Holthaus'):(0,2,19),(80,'Zinsner'):(0,2,19),
    (97,'Gore-Coty'):(0,3,19),
    (100,'Narain'):(1,5,17),(100,'Beatty'):(1,5,17),(100,'Azagury'):(1,5,17),
    (102,'Williams'):(0,2,3),(104,'Brown'):(0,1,5),
    (109,'Wilfong'):(0,1,3),(115,'Reed'):(0,1,1),
    (128,'Adams'):(0,2,4),
}

# Officer-bound successor starts, reviewed separately from departure/retirement
# dates. Text values retain relative/partial dates when that is all disclosed.
SUCCESSOR_DATES = {
    1:'January 7, 2024',2:'April 15',5:{'Mulligan':'February 4, 2024'},
    7:'April 1, 2024',16:'July 1, 2024',18:'April 1, 2024',24:'June 4, 2024',
    25:'May 15, 2024',26:'June 28, 2024',31:'September 1, 2024',
    41:'October 1, 2024',42:'October 1, 2024',44:'October 1',45:'September 10, 2024',
    49:'November 1, 2024',50:'November 18, 2024',52:'April 1, 2025',
    53:'first half of 2025',54:'February 3, 2025',55:'March 1, 2025',
    62:'March 1, 2025',64:'immediately',68:'April 30, 2025',69:'March 21, 2025',
    71:{'Walsh':'February 21, 2025'},75:'March 1, 2025',
    76:'interim February 25, 2025; permanent March 24, 2025',
    78:'on or about May 1, 2025',79:'immediately',80:'March 18, 2025',
    81:'May 22, 2025',82:'March 17, 2025',85:'May 1, 2025',86:'April 23, 2025',
    87:'May 6, 2025',90:'effective immediately',91:'July 1',
    93:'upon retirement (July 31, 2025)',95:'May 21, 2025',97:'immediately',
    99:'July 1, 2025',100:'September 1, 2025',102:'July 25, 2025',103:'August 1, 2025',
    104:'September 2, 2025',106:'February 2026',107:'September 1, 2025',
    109:'September 22, 2025',111:'October 15, 2025',112:'September 5, 2025',
    113:'immediately',115:'November 3',119:'on retirement (December 31, 2025); exhibit says January 2026',
    120:'March 1, 2026',128:'March 1, 2026',129:'April 1, 2026',130:'March 1, 2026',
}

NOTES = {
    0:'Sandra Rivera has a new role; Sandra L. is not disclosed as a replacement for the departing DCAI role.',
    12:'Position elimination and business reorganization do not explicitly identify coverage of White’s responsibilities.',
    15:'Do not import the successor from the earlier separate General Dynamics filing.',
    19:'Giglietti replaces Timko only; the package does not provide succession for Holston or Cox.',
    32:'Generic separation-contract assistance to any successor/backfill is not an actual succession arrangement.',
    38:'The target is the later Executive Advisor departure, not the earlier sales-role departure.',
    40:'Bedi is appointed interim Chief Product Officer; no explicit link to Desai’s COO responsibilities supports counting him as the COO successor.',
    48:'Explicitly no successor because of a business sale; this is a disclosed fact, not proof of economic uncertainty.',
    51:'Do not import the successor disclosed in the earlier Linde package.',
    62:'Welsh explicitly covers the Controller role; coverage of Delk’s additional tax-counsel responsibilities remains unknown.',
    63:'Future reassignment is explicitly promised but not yet specified; the separate bank-CEO appointment is not treated as replacement of Group President.',
    66:'Retirement is mentioned, but compensation effective dates cannot supply the departure date.',
    71:'The short excerpt names Patrick Scally, but Scally is absent from the original package; retain the original target and mark its full-source facts unsupported.',
    76:'An interim accounting handover and a later permanent appointment are disclosed; the actual Planishek exit date is not specified.',
    79:'Immediate interim handover supports timing; the target’s employee exit date remains unspecified.',
    82:'Kirk’s disclosed resignation date is May 2; Blomquist’s accounting-role start is March 17. Keep those dates separate.',
    90:'Role elimination alone is insufficient; the exhibit explicitly describes the split of Consumer, Product and Brand responsibilities.',
    91:'Core retirement date is June 30, whereas the exhibit says July 1. Preserve the discrepancy; both imply a future transition, not a precise reconciled date.',
    92:'Powers covers Rynaski’s accounting role; no President successor is disclosed for Whited.',
    96:'New Growth Officer/COO appointments do not expressly state they cover Parameswaran’s Growth and Strategy responsibilities.',
    97:'Macdonald’s new remit explicitly includes Delivery. Immediate handover is supported, but a separate Gore-Coty employee exit date is not stated.',
    100:'The press release explicitly dates the leadership changes September 1. That is a handover date, not a separately stated employee exit date.',
    111:'Permanent successor is named, but his October 15 start follows Boldea’s August 31 exit; preserve the disclosed coverage gap.',
    114:'Saw replaces Ewaldsson but the handover date is unstated; Field’s Business Group replacement is not explicitly identified.',
    117:'An anticipated 2026 hire and eventual 2027 retirement are disclosed in the 2025 package; no later information was retrieved.',
    119:'Core states new chairman effective on December 31 retirement; the attached announcement says January 2026. Do not silently reconcile.',
    123:'Cancelled future appointment, not an actual employee departure. Keep the original cohort member; do not invent a successor or replace the filing.',
    125:'Change of executive-officer designation, not a disclosed departure from employment. General co-president oversight is not explicit replacement of each target’s role.',
    126:'The exhibit expressly reassigns commercial reporting lines; role elimination alone would not suffice.',
}

# Departure dates/periods are adjudicated, not extracted by taking the first
# date in a paragraph. Explicit handover dates are labelled as such when an
# employee termination date is unstated. This prevents compensation, new-hire
# start and ultimate retirement dates from becoming interchangeable.
DEPARTURE_TIMING = '''December 31, 2023
January 7, 2024
April 30, 2024
January 31, 2024
April 1, 2024
2024 (Liu); February 4, 2024 (Mulligan)
February 2, 2024
April 1, 2024
end of 2024
April 1, 2024
April 30, 2024
May 1, 2024
April 26, 2024
April 1, 2024
April 15, 2024
April 30, 2024
June 30, 2024 role exit; December 31, 2024 retirement
October 1, 2024
June 30, 2024 retirement; April 1, 2024 responsibilities transition
April 7, 2024
May 1, 2024 Treasurer role exit; June 1, 2024 bank-CEO retirement
April 14, 2024
May 1, 2024
July 1, 2024
June 4, 2024
May 15, 2024
June 28, 2024
July 1, 2024
December 31, 2024
June 3, 2024 role exit; December 31, 2024 retirement
June 28, 2024
August 31, 2024
July 1, 2024
July 31, 2024 role exit; October 4, 2024 advisor exit

end of first quarter 2025 retirement; president-role handover day unstated

August 9, 2024
July 15, 2024
August 30, 2024
July 24, 2024, immediately
October 1, 2024
October 1, 2024 role exit; February 14, 2025 retirement
first half of 2025
October 1, 2024 role exit; end of 2024 retirement
September 10, 2024
November 30, 2024
September 20, 2024
March 31, 2025
November 1, 2024 role exit; March 31, 2025 retirement
November 18, 2024 CAO exit; January 17, 2025 employee exit
November 1, 2024 role exit; March 31, 2025 retirement
April 1, 2025
first half of 2025
February 3, 2025
March 1, 2025
April 30, 2025
on or about March 14, 2025
end of February 2025
today (January 15, 2025)
March 31, 2025
immediately (January 22, 2025)
March 1, 2025
February 3, 2025 role exit; November 2025 advisor exit
immediately (January 30, 2025)
March 15, 2025

January 30, 2025 EVP retirement; prior CFO retirement March 15, 2024
April 30, 2025 role exit; January 2, 2026 advisor exit
March 21, 2025 role exit; May 1, 2025 employee exit
April 25, 2025
February 21, 2025 (Walsh only)
2025 retirement; handover conditional on successor appointment
April 2, 2025
February 19, 2025 COO role exit; Commercial Airplanes role continues
March 1, 2025

March 31, 2025
on or about May 1, 2025

March 18, 2025 interim co-CEO handover
May 22, 2025
May 2, 2025 employee resignation; March 17, 2025 accounting handover

May 1, 2025
April 30, 2025
April 23, 2025 role exit; advisory role through September 30, 2025
May 6, 2025
June 30, 2025

May 2, 2025 role exit; September 5, 2025 employee exit
June 30, 2025 core retirement; July 1 in exhibit
July 1, 2025 (Whited); immediately May 8, 2025 (Rynaski)
July 31, 2025
May 25, 2025 (Hennington); June 1, 2025 employee exit following brief transition (Tu)
May 21, 2025 role exit; September 2, 2025 employee exit
October 1, 2025


June 30, 2025 accounting-role exit; January 2026 retirement
September 1, 2025 leadership handover; individual employee exit days unstated
July 17, 2025 role exit; October 31, 2025 employee exit
July 25, 2025 COO handover; employee exit day unstated
August 1, 2025 role exit; November 1, 2025 employee exit
September 2, 2025 accounting handover
August 25, 2025 General Counsel exit; February 28, 2026 retirement
February 2026
September 1, 2025 role exit; March 31, 2026 retirement
February 20, 2026
September 22, 2025 interim-role handover
December 31, 2025 role exit
August 31, 2025
September 5, 2025
immediately (August 25, 2025)
September 30, 2025 (Field only)
November 3, 2025
January 2, 2026
end of March 2027 retirement; accounting handover anticipated 2026
March 2026 retirement
December 31, 2025
February 28, 2026 role exit; April 2026 retirement
December 2, 2025
before end of 2026 retirement; accounting handover conditional on appointment

December 5, 2025 role exit; later December employee exit
December 31, 2025 executive-officer designation ends
December 5, 2025 role exit; April 6, 2026 employee exit
January 31, 2026
March 1, 2026 General Counsel handover; late 2026 retirement
March 31, 2026
March 1, 2026 role exit; December 31, 2026 retirement
June 30, 2026'''.splitlines()

REASON_PRESENT = {11,37,45,57,59,65,82,83,88,100,110,112,121,123}
REASON_EXHIBITS = {33:(1,5,6),103:(1,13,14)}

DEPARTURE_TIMING_BY_OFFICER = {
    (5,'Liu'):'2024', (5,'Mulligan'):'February 4, 2024',
    (71,'Walsh'):'February 21, 2025', (71,'Scally'):'',
    (92,'Whited'):'July 1, 2025', (92,'Rynaski'):'immediately May 8, 2025',
    (94,'Hennington'):'May 25, 2025',
    (94,'Tu'):'June 1, 2025 employee exit following brief transition',
    (114,'Ewaldsson'):'', (114,'Field'):'September 30, 2025',
}
REASON_VALUES = {
    11:'family medical reasons',37:'pursue another opportunity',
    45:'pursue another opportunity',57:'personal reasons; pursue another opportunity',
    59:'pursue other opportunities',65:'pursue another career opportunity',
    82:'become CEO of Exubrion Therapeutics',83:'pursue another opportunity',
    88:'pursue another career opportunity',100:'pursue other opportunities',
    110:'ongoing health issues',112:'accepted CFO position at another company',
    121:'join a private equity-held organization',123:'personal circumstances',
}
