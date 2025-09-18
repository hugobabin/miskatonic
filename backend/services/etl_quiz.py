import pandas as pd
import shutil
import json
from pathlib import Path
from datetime import datetime

#----- Folders -----
DATA_IN = Path("data/in")
DATA_TREATED= Path("data/treated")
DATA_LOG    = Path("data/log")
DATA_JSON   = Path("data/json")

#----- Expected schema -----
EXPECTED_COLUMNS = {"question","subject","use","correct","responsea","responseb",
    "responsec","responsed","remark"}

MAPPING_CSV_TO_CIBLE = {
    "q": "question","questions": "question",
    "sujet": "subject",
    "usage": "use",
    "correcte": "correct",
    "A": "responsea",    
    "B": "responseb",     
    "C": "responsec",       
    "D": "responsed",    
    "remarque": "remark"
}

#----- Utilities -----

def clean_col(col):
    """Normalize column names: lowercase, trim spaces, replace spaces with underscore."""
    return "_".join(str(col).strip().lower().split())

def move_file(src, dest_dir):
    """Move a file into destination folder, create folder if necessary."""
    shutil.move(src, dest_dir/src.name)

def get_csv_files(folder):
    """Return sorted list of CSV files in a folder."""
    if not folder.exists():
        return []
    return sorted(folder.glob("*.csv"))

def log_etl(type_evenement, message, data_log=DATA_LOG,file=None,line=None):
    """Append ETL events to a daily log CSV in data/log."""
    now       = datetime.now()
    ts        = now.strftime("%Y-%m-%d %H:%M:%S")
    date_str  = now.strftime("%Y-%m-%d")
    log_file  = data_log / f"log_etl_{date_str}.csv"
    header = not log_file.exists()
    row = pd.DataFrame([{
        "timestamp": ts,
        "type_evenement": type_evenement,
        "message": message,
        "file": file,
        "line": line
    }])
    row.to_csv(log_file, mode="a", index=False, header=header,sep=';')

# ------------------ Read + mapping + checks ------------------
def read_csv(data_in, data_treated, data_log):
    all_rows = []

    for file_path in get_csv_files(data_in):
        file_name = file_path.name

        # 1. raw read
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            log_etl("read_csv", str(e), data_log,file_name)
            move_file(file_path, data_treated)
            continue
        
        # 2. normalize column names
        df.columns = [clean_col(col) for col in df.columns]

        # 3. apply mapping to target schema
        df.rename(columns=MAPPING_CSV_TO_CIBLE, inplace=True)

        # 4. check expected columns
        missing = EXPECTED_COLUMNS - set(df.columns)
        if missing:
            log_etl("structure", f"Missing columns: {sorted(missing)}", data_log,file=file_name)
            move_file(file_path, data_treated)
            continue
        # 5. clean content (NaN -> "", strip strings)
        obj_cols = df.select_dtypes(include="object").columns
        df[obj_cols] = df[obj_cols].fillna("").apply(lambda s: s.str.strip())

        # 6. add tracking columns
        df['source_idx']=df.index+1
        df["source_file"] = file_name

        # 7. log and move processed file
        all_rows.append(df)
        log_etl("read_ok", f"{len(df)} rows to process", data_log,file=file_name)
        move_file(file_path, data_treated)
   
    return pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    
# ------------------ Transform ------------------

def extract_correct_indices(correct_answers):
    """
    Indices of correct choices (A..D -> {0..3}).
    Accepted: 'A', 'B,C', '1,3'.
    """
    raw = str(correct_answers).replace(";", ",").replace(".", ",")
    answers_raw = [answer.strip().upper() for answer in raw.split(",") if answer.strip()]
    indices: set[int] = set()
    for answer in answers_raw :
        if answer in {"A","B","C","D"}:
            indices.add("ABCD".index(answer))      # A=0, B=1, C=2, D=3
        elif answer.isdigit():
            n = int(answer)
            if 1 <= n <= 4:
                indices.add(n - 1)            # 1->0 ... 4->3
    return indices

def expand_responses_with_flags(df):
    """
    Expand columns A..D into long format with 'response' and 'isCorrect'.
    Skip empty responses, log if an empty response is marked correct.
    """
    records = []
    for _, row in df.iterrows():
        correct_indices = extract_correct_indices(row["correct"])
        for i, choice_col in enumerate(["responsea", "responseb", "responsec", "responsed"]):
            answers = row[choice_col]
            if not answers:
                if i in correct_indices:
                    log_etl("CORRECT_MISSING_CHOICE", f"line={int(row['source_idx'])} col={choice_col}, file='{row['source_file']}',line={int(row['source_idx'])}")
                continue
            records.append({
                "question": row["question"],
                "subject": row["subject"],
                "use": row.get("use", ""),
                "remark":row.get("remark", ""),
                "response": answers,
                "isCorrect": i in correct_indices,
                "source_idx": int(row["source_idx"]),
            })
    return pd.DataFrame.from_records(records)

def deduplicate_responses(question_df, src_name):
    """
     Deduplicate by response text. Preserve first-seen order.
        - If a duplicate occurs:
            * if any is correct → merged
            * else → ignored
    """
    df = question_df.copy()

    # Order to preserve first appearance
    if "source_idx" in df.columns:
        df["order"] = df["source_idx"]
    else:
        df["order"] = range(len(df))

    # Ensure text type
    df["response"] = df["response"].astype(str)

    responses = []
    seen = {}

    for _, row in df.sort_values("order").iterrows():
        response_text = row["response"]
        is_correct = bool(row["isCorrect"])
        file_ = row.get("source_file", src_name)
        line_ = int(row.get("source_idx", 0))

        if response_text in seen:
            if is_correct and not seen[response_text]["isCorrect"]:
                seen[response_text]["isCorrect"] = True
                log_etl("DUPLICATE_OPTION_MERGED", f"answer='{response_text}'",file=file_,line=line_)
            else:
                log_etl("DUPLICATE_OPTION_IGNORED", f"answer='{response_text}'",file=file_,line=line_)
        else:
            seen[response_text] = {"answer": response_text, "isCorrect": is_correct}
            responses.append(seen[response_text])

    return responses

def validate_responses_rules(responses):
    """
    Business rules: ≥2 responses and ≥1 correct.
    """
    errors: list[str] = []
    if len(responses) < 2:
        errors.append("TOO_FEW_CHOICES")
    if not any(r["isCorrect"] for r in responses):
        errors.append("MISSING_CORRECT")
    return errors

def build_question_object(question, subj, question_df, src_name, author):
    """
    Build one question JSON object from a (question, subject) group.
    - Deduplicate responses
    - Validate business rules (>=2 responses, >=1 correct)
    - Keep 'use' and 'remark' from the first non-empty row
    - Omit isCorrect when False
    """
    # 1) deduplicate + validate
    responses = deduplicate_responses(question_df, src_name)
    errors = validate_responses_rules(responses)
    if errors:
        line_hint = int(question_df["source_idx"].min()) if "source_idx" in question_df.columns else None
        log_etl("validation", f"{question} -> {','.join(errors)}'",file=src_name,line=line_hint)
        return None

    # 2) pick use/remark from first non-empty values (ordered by source_idx if present)
    grp_sorted = question_df.sort_values("source_idx") if "source_idx" in question_df.columns else question_df
    def first_non_empty(series_name):
        if series_name not in grp_sorted.columns:
            return None
        for v in grp_sorted[series_name]:
            if isinstance(v, str) and v.strip():
                return v
        return None

    use_val = first_non_empty("use")
    remark_val = first_non_empty("remark")

    # 3) shape responses (omit isCorrect when False)
    shaped_responses = [
        ({"answer": r["answer"], "isCorrect": True} if r["isCorrect"] else {"answer": r["answer"]})
        for r in responses
    ]

    # 4) dates + metadata
    from datetime import date
    today = date.today().isoformat()
    return {
        "question": question,
        "subject": subj,
        "use": use_val,
        "responses": shaped_responses,
        "remark": remark_val,
        "metadata": {
            "source_file": src_name,
            "author": author
        },
        "date_creation": {"$date": today},
        "date_modification": {"$date": today}
    }

def export_questions_to_json(src_name,responses_df,author=None):
    """
    Process responses DataFrame grouped by (question, subject),
    build question objects, write them as a JSON file,
    returns: dict:{"accepted": int, "rejected": int, "total": int, "json_path": str}
    """
    out_path = DATA_JSON / (Path(src_name).stem + ".json")

    questions_out: list[dict] = []
    rejected = 0

    for (question, subj), question_df in responses_df.groupby(["question","subject"], sort=False):
        obj = build_question_object(question, subj, question_df, src_name, author)
        if obj is None:
            rejected += 1
            continue
        questions_out.append(obj)
        line_hint = int(question_df["source_idx"].min()) if "source_idx" in question_df.columns else None
        log_etl("GROUP_OK",
                f"count={len(obj['responses'])} correct="
                f"{sum(('isCorrect' in r) for r in obj['responses'])} q='{question}'",file=src_name,line=line_hint)

    # JSON output
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(questions_out, f, ensure_ascii=False, indent=2)

    stats = {
        "accepted": len(questions_out),
        "rejected": rejected,
        "total": len(questions_out) + rejected,
        "json_path": str(out_path),
    }
    return stats

def process_and_export_csv(csv_path, author = None):
    """
.   Process a CSV from data/in,
    generate a JSON, and return statistics.
    """
    # Ensure folders exist
    for d in [DATA_IN, DATA_TREATED, DATA_LOG, DATA_JSON]:
        d.mkdir(parents=True, exist_ok=True)

    # Step 1: Read CSVs
    df_all = read_csv(DATA_IN, DATA_TREATED, DATA_LOG)
    if df_all.empty:
        raise ValueError("No valid data from uploaded CSV")

    # Step 2: Expand responses to long format
    responses_df = expand_responses_with_flags(df_all)

    # Step 3: Export JSON per source file
    src_name = csv_path.name
    stats = export_questions_to_json(src_name, responses_df, author)
    stats["message"] = f"Questions accepted: {stats['accepted']} | rejected: {stats['rejected']} | total: {stats['total']}"

    return stats

if __name__ == "__main__":
    files = list(Path("data/in").glob("*.csv"))
    if not files:
        print("No CSV file found in data/in")
    else:
        csv_path = files[0]
        stats = process_and_export_csv(csv_path, author=None)
        print(stats["message"])