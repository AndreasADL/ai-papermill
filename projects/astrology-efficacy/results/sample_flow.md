# Sample construction — Study 1

Wikidata people, day-precision DOB, 1852-2020: 4,423,732
After restricting to ephemeris coverage (DE440s, 1849-2150): 4,407,456
Person-occupation pairs: 6,231,195; labelled occupations: 19,384
Occupation mapping audit written to occupation_mapping_audit.csv (inspect by hand)
  mercury    888 occupation types  e.g. ['Albanian teacher', 'American author', 'Ancient Egyptian Scribe', 'Arabic teacher', 'Art Teacher', 'Assistant Language Teacher']
  venus      161 occupation types  e.g. ['Apulian vase-painter', 'Attic vase-painter', 'Buddhist painter', 'Corinthian vase-painter', 'Cup Painter', 'Dōga painter']
  mars       107 occupation types  e.g. ['Armourer (plate)', 'Carpenter', 'Chinese chef', 'Decorative metalworker', 'Gold Miner', 'Ironworker']
  athlete    114 occupation types (positive control)
People with >=1 occupation: 3,714,005
  is_mercury_occ: 690,954 people (15.68%)
  is_venus_occ: 115,064 people (2.61%)
  is_mars_occ: 26,227 people (0.60%)
  is_athlete:    847,135 people (19.22%)

Computing sign ingresses (this is the expensive step)
  mercury  2,566 ingresses (14.8/yr)
  venus    2,195 ingresses (12.7/yr)
  mars     1,192 ingresses (6.9/yr)
  sun      2,076 ingresses (12.0/yr)

Attaching pre-registered direction per cusp (from hypotheses.py)
  mercury  cusp directions: +1:8  -1:8  0:8
  venus    cusp directions: +1:5  -1:6  0:11
  mars     cusp directions: +1:6  -1:6  0:12

Heaped-day records (dom 1/10/15): 484,222 (11.0%)

Final analysis frame: 4,407,456 rows x 35 cols
-> data/processed/study1.parquet