"""ETL module for processing and cleaning quiz questions.
Handles extraction, transformation (including fuzzy correction), and loading into MongoDB.
"""

import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz

from src.models.question import QuestionModel
from src.services.mongo import ServiceMongo
from src.services.question import ServiceQuestion
from src.services.util import ServiceUtil

# ----- Folders -----
DATA_IN = Path("data/in")
DATA_TREATED = Path("data/treated")
DATA_LOG = Path("data/log")

# ----- Expected schema -----
EXPECTED_COLUMNS = {
    "question",
    "subject",
    "use",
    "correct",
    "responsea",
    "responseb",
    "responsec",
    "responsed",
    "remark",
}

MAPPING_CSV_TO_CIBLE = {
    "q": "question",
    "questions": "question",
    "sujet": "subject",
    "usage": "use",
    "correcte": "correct",
    "A": "responsea",
    "B": "responseb",
    "C": "responsec",
    "D": "responsed",
    "remarque": "remark",
}

THRESHOLD_FUZZY = 90  # for typo detection

# ----- Utilities -----


def clean_col(col):
    """Normalize column names: lowercase, trim spaces, replace spaces with underscore."""
    return "_".join(str(col).strip().lower().split())


def move_file(src, dest_dir):
    """Move a file into destination folder, create folder if necessary."""
    shutil.move(src, dest_dir / src.name)


def get_csv_files(folder):
    """Return sorted list of CSV files in a folder."""
    if not folder.exists():
        return []
    return sorted(folder.glob("*.csv"))


def rapport_etl(type_evenement, message, data_log=DATA_LOG, file="log", line=None):
    """Append ETL events to a daily log CSV in data/log."""
    now = datetime.now()
    ts = now.strftime("%Y-%m-%d %H:%M:%S")
    file_name = Path(file).stem
    log_file = data_log / f"rapport_{file_name}.csv"
    header = not log_file.exists()
    row = pd.DataFrame(
        [
            {
                "timestamp": ts,
                "file": file,
                "line": line,
                "type_evenement": type_evenement,
                "message": message,
            }
        ]
    )
    row.to_csv(
        log_file, mode="a", index=False, header=header, sep=";", encoding="utf-8-sig"
    )


def distinct_from_mongo(col, field: str) -> list[str]:
    """Retourne la liste des valeurs distinctes pour un champ donné en base Mongo."""
    return [v for v in col.distinct(field) if isinstance(v, str) and v.strip()]


# ------------------ Read + mapping + checks ------------------
def read_csv(data_in, data_treated, data_log):
    """Read and validate a CSV file for ETL processing."""
    all_rows = []

    for file_path in get_csv_files(data_in):
        file_name = file_path.name

        # 1. raw read
        try:
            df = pd.read_csv(file_path)
        except (
            FileNotFoundError,
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
        ) as e:
            rapport_etl("read_csv", str(e), data_log, file=file_name)
            move_file(file_path, data_treated)
            continue
        # 2. normalize column names
        df.columns = [clean_col(col) for col in df.columns]

        # 3. apply mapping to target schema
        df.rename(columns=MAPPING_CSV_TO_CIBLE, inplace=True)

        # 4. check expected columns
        missing = EXPECTED_COLUMNS - set(df.columns)
        if missing:
            rapport_etl(
                "structure",
                f"Missing columns: {sorted(missing)}",
                data_log,
                file=file_name,
            )
            move_file(file_path, data_treated)
            continue

        # 5. clean content (NaN -> "", strip strings)
        obj_cols = df.select_dtypes(include="object").columns
        df[obj_cols] = df[obj_cols].fillna("").apply(lambda s: s.str.strip())

        # 6. add tracking columns
        df["source_idx"] = df.index + 1
        df["source_file"] = file_name

        # 7. normalize question text
        df["question_key"] = df["question"].apply(ServiceUtil.normalize_question)

        # 8. log and move processed file
        all_rows.append(df)
        rapport_etl("READ_OK", f"{len(df)} rows to process", data_log, file=file_name)
        move_file(file_path, data_treated)

    return pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()


def fuzzy_value(
    val: str, ref: list[str], _field: str, threshold: int = THRESHOLD_FUZZY
) -> str:
    """Retourne la valeur corrigée si proche d’une valeur existante, sinon garde telle quelle."""
    if not ref:
        ref.append(val)
        return val
    best = max(ref, key=lambda c: fuzz.ratio(val, c))
    score = fuzz.ratio(val, best)
    if score > threshold and best != val:
        return best
    ref.append(val)  # new value becomes reference
    return val


# ------------------ Transform ------------------
def transform_fuzzy(df: pd.DataFrame, log_fn):
    """Apply fuzzy string matching to clean subject and use fields."""
    # collection retrieval in Mongo
    col = ServiceMongo.get_collection("questions")

    subjects_ref = distinct_from_mongo(col, "subject")
    uses_ref = distinct_from_mongo(col, "use")

    df["subject_input"] = df["subject"].fillna("").astype(str).str.strip()
    df["use_input"] = df["use"].fillna("").astype(str).str.strip()
    # loop for logging with line
    for i, row in df.iterrows():
        s_in, u_in = row["subject_input"], row["use_input"]

        s_out = fuzzy_value(s_in, subjects_ref, "subject")
        if s_out != s_in:
            sc = fuzz.ratio(s_in, s_out)
            if sc > THRESHOLD_FUZZY:
                log_fn(
                    "AUTO_CORRECT_SUBJECT",
                    f"from='{s_in}' to='{s_out}'",
                    file=row["source_file"],
                    line=int(row["source_idx"]),
                )
        df.at[i, "subject"] = s_out

        u_out = fuzzy_value(u_in, uses_ref, "use")
        if u_out != u_in:
            sc = fuzz.ratio(u_in, u_out)
            if sc > THRESHOLD_FUZZY:
                log_fn(
                    "AUTO_CORRECT_USE",
                    f"line={int(row['source_idx'])} field=use from='{u_in}' to='{u_out}' "
                    f"score={sc:.1f}, file='{row['source_file']}'",
                    file=row["source_file"],
                    line=int(row["source_idx"]),
                )
        df.at[i, "use"] = u_out

    return df


def extract_correct_indices(correct_answers):
    """
    Indices of correct choices (A..D -> {0..3}).
    Accepted: 'A', 'B,C', '1,3'.
    """
    raw = str(correct_answers).replace(";", ",").replace(".", ",")
    answers_raw = [
        answer.strip().upper() for answer in raw.split(",") if answer.strip()
    ]
    indices: set[int] = set()
    for answer in answers_raw:
        if answer in {"A", "B", "C", "D"}:
            indices.add("ABCD".index(answer))  # A=0, B=1, C=2, D=3
        elif answer.isdigit():
            n = int(answer)
            if 1 <= n <= 4:
                indices.add(n - 1)  # 1->0 ... 4->3
    return indices


def expand_responses_with_flags(df):
    """
    Expand columns A..D into long format with 'response' and 'isCorrect'.
    Skip empty responses, log if an empty response is marked correct.
    """
    records = []
    for _, row in df.iterrows():
        correct_indices = extract_correct_indices(row["correct"])
        for i, choice_col in enumerate(
            ["responsea", "responseb", "responsec", "responsed"]
        ):
            answers = row[choice_col]
            if not answers:
                if i in correct_indices:
                    rapport_etl(
                        "CORRECT_MISSING_CHOICE",
                        f"line={int(row['source_idx'])} col={choice_col}, file='{row['source_file']}'",
                        file=row["source_file"],
                        line=int(row["source_idx"]),
                    )
                continue
            records.append(
                {
                    "question": row["question"],
                    "question_key": row["question_key"],  # (for groupby)
                    "subject": row["subject"],
                    "use": row.get("use", ""),
                    "remark": row.get("remark", ""),
                    "response": answers,
                    "isCorrect": i in correct_indices,
                    "source_idx": int(row["source_idx"]),
                }
            )
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
                rapport_etl(
                    "ANSWER_MERGED", f"answer='{response_text}'", file=file_, line=line_
                )
            else:
                rapport_etl(
                    "ANSWER_IGNORED",
                    f"answer='{response_text}'",
                    file=file_,
                    line=line_,
                )
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


def build_question_object(question, subj, question_df, src_name, author, use):
    """
    Build one question dict (compatible QuestionModel) from a (question_key, subject, use) group.
    - Deduplicate responses
    - Validate business rules (>=2 responses, >=1 correct)
    - Keep 'remark' from the first non-empty row
    - Omit isCorrect when False
    """
    # 1) deduplicate + validate
    responses = deduplicate_responses(question_df, src_name)
    errors = validate_responses_rules(responses)
    if errors:
        line_hint = (
            int(question_df["source_idx"].min())
            if "source_idx" in question_df.columns
            else None
        )
        rapport_etl(
            "QUESTION_REJECTED",
            f"{question} -> {','.join(errors)}",
            file=src_name,
            line=line_hint,
        )
        return None

    # 2) pick remark
    grp_sorted = (
        question_df.sort_values("source_idx")
        if "source_idx" in question_df.columns
        else question_df
    )

    def first_non_empty(series_name):
        if series_name not in grp_sorted.columns:
            return None
        for v in grp_sorted[series_name]:
            if isinstance(v, str) and v.strip():
                return v
        return None

    remark_val = first_non_empty("remark")

    # 3) shape responses (omit isCorrect when False)
    shaped_responses = [
        (
            {"answer": r["answer"], "isCorrect": True}
            if r["isCorrect"]
            else {"answer": r["answer"]}
        )
        for r in responses
    ]

    # 4) dates + metadata
    now = datetime.now(timezone.utc)
    return {
        "question": question,
        "subject": subj,
        "use": use,
        "responses": shaped_responses,
        "remark": remark_val or None,
        "metadata": {"source_file": src_name, "author": author or ""},
        "date_creation": now,
        "date_modification": None,
        "active": True,
    }


def export_questions_to_mongo(src_name, responses_df, author=None):
    """
    GroupBy (question_key, subject, use) → build → exists() → create().
    """
    accepted = rejected = 0

    for (_, subj, use), question_df in responses_df.groupby(
        ["question_key", "subject", "use"], sort=False
    ):
        # choose the longest statement
        question = question_df.loc[
            question_df["question"].str.len().idxmax(), "question"
        ]

        obj = build_question_object(
            question, subj, question_df, src_name, author, use=use
        )
        if obj is None:
            rejected += 1
            continue

        qm = QuestionModel(**obj)

        # Application-level check: no index, we compare the normalized question on the service side.
        if ServiceQuestion.exists(qm.question, qm.subject, qm.use):
            rejected += 1
            rapport_etl(
                "DUP_SKIPPED",
                f"q='{qm.question}'",
                file=src_name,
                line=int(question_df["source_idx"].min()),
            )
            continue

        # Insert in Mongo
        ServiceQuestion.create(qm)
        accepted += 1
        rapport_etl(
            "QUESTION_INSERTED",
            f"count={len(qm.responses)} correct={sum((getattr(r, 'isCorrect', None) is True) or (isinstance(r, dict) and r.get('isCorrect') is True) for r in qm.responses)} q='{qm.question}'",
            file=src_name,
            line=int(question_df["source_idx"].min()),
        )

    total = accepted + rejected
    msg = f"Questions accepted: {accepted} | rejected: {rejected} | total: {total}"
    rapport_etl("SUMMARY", file=src_name, message=msg)
    return {"accepted": accepted, "rejected": rejected, "total": total}


def process_and_export_csv(csv_path, author=None):
    """
    Process a CSV from data/in, insert into Mongo, and return statistics.
    """
    # Ensure folders exist
    for d in [DATA_IN, DATA_TREATED, DATA_LOG]:
        d.mkdir(parents=True, exist_ok=True)

    # Connect to Mongo
    ServiceMongo.connect()
    try:
        # Step 1: Read CSVs
        df_all = read_csv(DATA_IN, DATA_TREATED, DATA_LOG)
        if df_all.empty:
            raise ValueError("No valid data from uploaded CSV")
        # Step 2: Fuzzy transform
        df = transform_fuzzy(df_all, rapport_etl)

        # Step 3: Expand responses to long format
        responses_df = expand_responses_with_flags(df)

        # Step 4: Export to Mongo
        src_name = csv_path.name
        stats = export_questions_to_mongo(src_name, responses_df, author)
        log_file_path = Path("data/log") / f"rapport_{Path(src_name).stem}.csv"
        return stats, log_file_path
    finally:
        ServiceMongo.disconnect()


# -------------- main ------------------
if __name__ == "__main__":
    files = list(Path("data/in").glob("*.csv"))
    if not files:
        print("No CSV file found in data/in")
    else:
        first_csv_path = files[0]
        stats, log_file_path = process_and_export_csv(first_csv_path, author=None)
        print(
            f"Questions accepted: {stats['accepted']} | rejected: {stats['rejected']} | total: {stats['total']}"
        )