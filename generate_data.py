"""
Synthetic data generator for a nursing-education star schema.
All names, IDs, and outcomes are randomly generated. No real student data.
Run: python generate_data.py   ->  writes six CSVs to ./data/
"""
import csv, random, datetime, os

random.seed(42)
OUT = "data"
os.makedirs(OUT, exist_ok=True)

def write(name, header, rows):
    with open(f"{OUT}/{name}.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"{name}.csv: {len(rows)} rows")

# ---------- DIM_PROGRAM ----------
programs = [
    (1, "BSN", "Bachelor of Science in Nursing", "Pre-Licensure", 36),
    (2, "ADN", "Associate Degree in Nursing", "Pre-Licensure", 24),
    (3, "MSN-FNP", "MSN Family Nurse Practitioner", "Graduate", 30),
    (4, "MSN-PMHNP", "MSN Psychiatric Mental Health NP", "Graduate", 30),
    (5, "RN-BSN", "RN to BSN Bridge", "Post-Licensure", 18),
    (6, "DNP", "Doctor of Nursing Practice", "Graduate", 36),
]
write("dim_program", ["program_key","program_code","program_name","program_type","program_length_months"], programs)

# ---------- DIM_TERM ----------
terms, tk = [], 0
for year in range(2023, 2027):
    for i, (label, m, d) in enumerate([("1", 1, 8), ("2", 5, 6), ("3", 9, 5)], start=1):
        if year == 2026 and i > 2:
            continue
        tk += 1
        start = datetime.date(year, m, d)
        end = start + datetime.timedelta(weeks=15)
        season = {1: "Spring", 2: "Summer", 3: "Fall"}[i]
        terms.append((tk, f"{year}-{label}", f"{season} {year}", year, season,
                      start.isoformat(), end.isoformat()))
n = len(terms)
terms = [t + (n - idx,) for idx, t in enumerate(terms)]   # term_rank: 1 = most recent
write("dim_term", ["term_key","term_code","term_name","academic_year","season",
                   "term_start_date","term_end_date","term_rank"], terms)

# ---------- DIM_COURSE ----------
course_defs = [
    ("NURS101","Foundations of Nursing Practice",3,"Core",1),
    ("NURS150","Health Assessment",3,"Core",1),
    ("NURS210","Pharmacology I",4,"Core",2),
    ("NURS215","Pathophysiology",4,"Core",2),
    ("NURS240","Medical-Surgical Nursing I",5,"Clinical",2),
    ("NURS310","Maternal Newborn Nursing",4,"Clinical",3),
    ("NURS320","Pediatric Nursing",4,"Clinical",3),
    ("NURS330","Mental Health Nursing",4,"Clinical",3),
    ("NURS410","Community Health Nursing",3,"Clinical",4),
    ("NURS450","Leadership and Management",3,"Core",4),
    ("NURS460","NCLEX Readiness Capstone",2,"Capstone",4),
    ("STAT200","Statistics for Health Sciences",3,"General Ed",1),
    ("BIOL220","Microbiology",4,"General Ed",1),
    ("NURS510","Advanced Pharmacology",3,"Graduate Core",1),
    ("NURS520","Advanced Health Assessment",3,"Graduate Core",1),
    ("NURS610","Evidence-Based Practice",3,"Graduate Core",2),
]
courses = [(i+1,) + c for i, c in enumerate(course_defs)]
write("dim_course", ["course_key","course_code","course_name","credit_hours","course_category","course_level"], courses)

# ---------- DIM_LEARNER ----------
first = ["Alex","Jordan","Taylor","Morgan","Casey","Riley","Avery","Quinn","Rowan","Sage",
         "Maria","James","Linda","Robert","Patricia","Michael","Jennifer","David","Elizabeth","William",
         "Aisha","Diego","Priya","Kenji","Fatima","Luis","Nadia","Omar","Yuki","Sofia"]
last = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
        "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Nguyen","Patel","Kim","Chen",
        "Okafor","Silva","Rossi","Novak","Haddad","Ivanov","Berg","Choi","Diallo","Ferrara"]
campuses = ["Salt Lake City","Provo","Ogden","Online","St. George"]
statuses_pool = ["Active","Graduated","Withdrawn","Leave of Absence"]

learners = []
for sid in range(10001, 10001 + 1400):
    prog = random.choices([1,2,3,4,5,6], weights=[35,20,15,8,15,7])[0]
    start_term = random.randint(1, max(1, n - 2))
    status = random.choices(statuses_pool, weights=[55,28,13,4])[0]
    learners.append((
        sid, random.choice(first), random.choice(last), prog, start_term,
        random.choice(campuses), random.choice(["Full-Time","Part-Time"]), status,
        random.choice(["Yes","No"]) if random.random() < 0.12 else "No",
    ))
write("dim_learner", ["learner_key","first_name","last_name","program_key","start_term_key",
                      "campus","enrollment_intensity","learner_status","is_veteran"], learners)

# ---------- FACT_COURSE_ENROLLMENT ----------
prog_courses = {
    1: [1,2,3,4,5,6,7,8,9,10,11,12,13],
    2: [1,2,3,4,5,6,7,8,11,12],
    3: [14,15,16],
    4: [14,15,16,8],
    5: [9,10,11,12],
    6: [14,15,16,10],
}
difficulty = {1:.06,2:.08,3:.22,4:.20,5:.15,6:.10,7:.10,8:.09,9:.07,10:.05,
              11:.12,12:.18,13:.19,14:.11,15:.09,16:.07}

rows, eid = [], 500000
for sid, _, _, prog, start_term, campus, intensity, status, _ in learners:
    pool = prog_courses[prog][:]
    random.shuffle(pool)
    n_terms = random.randint(1, 6)
    per_term = 2 if intensity == "Part-Time" else 3
    ci = 0
    for t_off in range(n_terms):
        tkey = start_term + t_off
        if tkey > n:
            break
        for _ in range(per_term):
            if ci >= len(pool):
                break
            ckey = pool[ci]; ci += 1
            eid += 1
            base = difficulty[ckey]
            if intensity == "Part-Time": base -= 0.02
            if campus == "Online": base += 0.04
            if tkey >= n - 1: base += 0.03
            fail_p = min(max(base, 0.01), 0.45)
            r = random.random()
            if tkey >= n and random.random() < 0.6:
                passed, grade, final = "", "", ""          # in progress -> blank
            elif r < fail_p:
                passed, final = "FALSE", round(random.uniform(48, 74.4), 1)
                grade = random.choice(["F","D"])
            else:
                passed, final = "TRUE", round(random.uniform(75, 99), 1)
                grade = random.choice(["A","A","B","B","B","C"])
            withdrew = "TRUE" if (passed == "" and random.random() < 0.05) else "FALSE"
            rows.append((eid, sid, ckey, tkey, prog, passed, grade, final, withdrew,
                         round(random.uniform(0.55, 1.0), 2)))
write("fact_course_enrollment",
      ["enrollment_key","learner_key","course_key","term_key","program_key",
       "is_course_passed","letter_grade","final_score","is_withdrawn","attendance_rate"], rows)

# ---------- DIM_DATE ----------
d, end = datetime.date(2023, 1, 1), datetime.date(2026, 12, 31)
dates = []
while d <= end:
    q = (d.month - 1)//3 + 1
    dates.append((d.isoformat(), d.year, q, f"Q{q}", d.month, d.strftime("%B"),
                  d.day, d.strftime("%A"), 1 if d.weekday() >= 5 else 0))
    d += datetime.timedelta(days=1)
write("dim_date", ["date","year","quarter_number","quarter_name","month_number",
                   "month_name","day_of_month","day_name","is_weekend"], dates)
