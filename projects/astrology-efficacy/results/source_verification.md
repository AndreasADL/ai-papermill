# Source verification — pre-GATE-1 structural checks

Run: 2026-09-18T15:07:11.873957+00:00

Structure only. No astrological-variable x outcome association is computed here.

## A. Wikidata (Study 1) — via QLever

WDQS (query.wikidata.org) times out on the birth-date precision join even at
one-month scale. QLever indexes the same Wikidata dump and answers in ~1s.

### A1. Sample size
  [day-precision births] 1 rows in 0.8s
  Humans with DAY-precision date of birth: **5,046,592**
  [day-precision + occupation (statement pairs)] 1 rows in 0.5s
  Person-occupation statement pairs: **7,140,200**

### A2. Coverage by birth century
  [births by century] 10 rows in 1.5s
  1500s:     16,746
  1600s:     63,034
  1700s:    186,492
  1800s:  1,102,469
  1900s:  3,492,384
  2000s:    179,330
  2100s:          1
  2400s:          6
  8000s:          1
  9100s:          1

### A3. Date heaping — THE critical check for RDD bandwidth
Sign ingress falls on day-of-month 19-23. Heaping on the 1st/15th would
contaminate a wide bandwidth. Measuring the real distribution (births 1900+):

  [day-of-month distribution] 31 rows in 0.9s
  Total day-precision births 1900+: 3,671,723

  | day | n | ratio to median |
  |---|---|---|
  | 1.0 | 146,633.0 | 1.230 |  <-- HEAP
  | 2.0 | 122,307.0 | 1.026 |
  | 3.0 | 120,633.0 | 1.012 |
  | 4.0 | 119,485.0 | 1.002 |
  | 5.0 | 124,161.0 | 1.041 |
  | 6.0 | 120,797.0 | 1.013 |
  | 7.0 | 119,879.0 | 1.006 |
  | 8.0 | 120,633.0 | 1.012 |
  | 9.0 | 116,963.0 | 0.981 |
  | 10.0 | 128,266.0 | 1.076 |
  | 11.0 | 118,035.0 | 0.990 |
  | 12.0 | 124,799.0 | 1.047 |
  | 13.0 | 116,218.0 | 0.975 |
  | 14.0 | 120,110.0 | 1.007 |
  | 15.0 | 129,265.0 | 1.084 |
  | 16.0 | 118,875.0 | 0.997 |
  | 17.0 | 119,053.0 | 0.999 |
  | 18.0 | 119,408.0 | 1.002 |
  | 19.0 | 116,808.0 | 0.980 |  (ingress zone)
  | 20.0 | 124,257.0 | 1.042 |  (ingress zone)
  | 21.0 | 118,299.0 | 0.992 |  (ingress zone)
  | 22.0 | 118,177.0 | 0.991 |  (ingress zone)
  | 23.0 | 119,220.0 | 1.000 |  (ingress zone)
  | 24.0 | 117,395.0 | 0.985 |
  | 25.0 | 122,006.0 | 1.023 |
  | 26.0 | 116,358.0 | 0.976 |
  | 27.0 | 116,816.0 | 0.980 |
  | 28.0 | 118,627.0 | 0.995 |
  | 29.0 | 106,309.0 | 0.892 |
  | 30.0 | 105,949.0 | 0.889 |
  | 31.0 | 65,982.0 | 0.553 |

  Ingress-zone (19-23) ratio range: 0.980-1.042

### A4. Top occupations (marginal counts only — no sign crosstab)
  [top occupations] 30 rows in 1.8s
  politician                            590,195
  association football player           355,616
  writer                                245,897
  actor                                 237,734
  university teacher                    167,841
  basketball player                     147,542
  painter                               129,777
  journalist                            119,158
  singer                                 96,499
  composer                               84,720
  lawyer                                 77,246
  physician                              76,676
  musician                               74,101
  teacher                                72,163
  poet                                   71,479
  historian                              70,563
  military personnel                     70,187
  film actor                             68,199
  jurist                                 61,056
  businessperson                         60,760
  screenwriter                           54,041
  film director                          53,877
  Catholic priest                        52,413
  athletics competitor                   49,658
  architect                              49,409
  translator                             46,939
  military officer                       44,703
  television actor                       44,360
  association football coach             41,673
  ice hockey player                      41,574


## B. Laouenan et al. 2022 cross-verified notable people

  File: cross-verified-database.csv.gz (249.4 MB)
  Columns: 49
  Birth-related columns: ['birth', 'approx_birth', 'birth_min', 'birth_max', 'birth_estimation', 'bigperiod_birth_graph_b', 'bigperiod_birth']

  **VERDICT: birth date granularity**
  `birth` sample values: [1932.0, 1860.0, 1971.0, 1983.0, 1912.0, 1928.0, 1818.0, 1907.0]
  `birth` dtype: float64

  `birth` is a YEAR ONLY. There is no month or day field anywhere in the schema.
  => This dataset CANNOT support the cusp RDD (no running variable).
  => Demoted from Study 1 primary source to an occupation-taxonomy reference
     and a birth-YEAR-level descriptive cross-check only.

  Occupation taxonomy available: level1_main_occ = ['Culture', 'Discovery/Science', 'Leadership', 'Missing', 'Other', 'Sports/Games']
  level2_main_occ distinct values (first 50k rows): 15


## C. GSS (Study 3)

  Downloading https://gss.norc.org/content/dam/gss/get-the-data/documents/stata/GSS_stata.zip
  Downloaded 45.4 MB
  Archive contents: ['GSS_stata/', 'GSS_stata/GSS 2024 - Whats New R3a.pdf', 'GSS_stata/GSS 2024 Codebook R3a.pdf', 'GSS_stata/GSS 2024 Release Variables R3a.pdf', 'GSS_stata/gss7224_r3a.dta', 'GSS_stata/ReadMe.txt', 'GSS_stata/Release Notes 7224 R3a.pdf']
  Reading gss7224_r3a.dta (570.2 MB)
  Rows: 75,699
  zodiac: valid N = 64,451; years = [1976, 1977, 1978, 1980, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1993, 1994, 1996, 1998, 2000, 2002, 2004, 2006, 2008, 2010, 2012, 2014, 2016, 2018, 2021, 2022]
  astrolgy: valid N = 8,845; years = [2006, 2008, 2010, 2012, 2014, 2016, 2018]
  astrosci: valid N = 8,553; years = [2006, 2008, 2010, 2012, 2014, 2016, 2018]

  ### The number that decides Study 3's moderation test

  **ZODIAC x ASTROLGY: joint N = 8,531**
  Crosstab shape: (12, 2); min cell = 304; median cell = 357

  **ZODIAC x ASTROSCI: joint N = 8,263**
  Crosstab shape: (12, 3); min cell = 36; median cell = 201


## D. BTS On-Time Performance (Study 2)

  Downloading https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2023_1.zip
  File: ontime_2023_01.zip (25.8 MB)
  Inner CSV: On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2023_1.csv
  Columns: 110
    FlightDate             PRESENT
    ArrDelay               PRESENT
    ArrDelayMinutes        PRESENT
    DepDelay               PRESENT
    Cancelled              PRESENT
    CancellationCode       PRESENT
    Diverted               PRESENT
    Reporting_Airline      PRESENT
  Sample FlightDate values: ['2023-01-02', '2023-01-03', '2023-01-04']