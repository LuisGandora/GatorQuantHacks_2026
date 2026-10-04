import re
import financing_hypothesis as f
def eligible(t):
 return bool(re.search(f.DEBT,t,re.I) and re.search(f.COMPLETE,t,re.I) and not re.search(f.EXCLUDE,t,re.I))
assert eligible('The Company completed the sale of $500 million senior notes due 2030.')
assert eligible('The Company issued $500 million of fixed rate notes due 2030.')
assert not eligible('The Company issued a press release announcing pricing of its notes offering.')
assert not eligible('The Company entered an underwriting agreement for an offering of senior notes.')
assert not eligible('The Company completed the sale of exchangeable senior notes.')
assert not eligible('The Company completed the sale of notes to fund an acquisition.')
assert not eligible('The Company completed the sale of equity units including notes.')
print('Financing classification boundary checks passed.')
