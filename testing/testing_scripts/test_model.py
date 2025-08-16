import json
from pathlib import Path

from crew_flows_student.crews.support_crew_flow.administrative_query_crew.administrative_query_crew import AdministrativeQueryCrew


INPUT_PATH = Path("merged1.json")             # your existing merged file
OUTPUT_PATH = Path("merged1.json")            # unchanged (not used for final writes now)
FINAL_PATH = Path("final.json")               # NEW: incremental output file


def call_admin_crew(question: str) -> str:
    payload = {"user_input": question}
    result = AdministrativeQueryCrew().crew().kickoff(payload).pydantic
    return result.response


def _load_json_safe(path: Path):
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # If corrupted or empty, treat as empty to allow progress to continue
        return []


def main():
    # Load input items
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)

    # Load existing final results (if any) and build a fast lookup set of questions
    final_data = _load_json_safe(FINAL_PATH)
    seen_questions = {entry.get("question") for entry in final_data if isinstance(entry, dict)}

    print(seen_questions)

    processed_since_last_write = 0
    total_skipped = 0
    total_new = 0

    for item in items:
        question = item.get("question")
        if question in seen_questions:
            total_skipped += 1
            continue  # skip questions already present in final.json

        # Get model answer and append to final dataset
        model_answer = call_admin_crew(question)
        new_entry = dict(item)
        new_entry["model_answer"] = model_answer
        final_data.append(new_entry)
        seen_questions.add(question)

        processed_since_last_write += 1
        total_new += 1

        # Write to final.json every 5 new items
        if processed_since_last_write >= 5:
            with open(FINAL_PATH, "w", encoding="utf-8") as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
            print(f"Incremental write: {len(final_data)} total items in {FINAL_PATH}")
            processed_since_last_write = 0

    # Final flush (for any remainder < 5)
    if processed_since_last_write > 0:
        with open(FINAL_PATH, "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        print(f"Final write: {len(final_data)} total items in {FINAL_PATH}")

    print(f"Done. New items processed: {total_new}, skipped (already present): {total_skipped}")


if __name__ == "__main__":
    main()
