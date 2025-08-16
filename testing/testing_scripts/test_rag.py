import json
from pathlib import Path

from crew_flows_student.crews.subjective_crew.subjective_crew import SubjectiveCrew
from faiss_ops.faiss_db import retrieve_relevant_context_testing


INPUT_PATH = Path("merged2.json")             # your existing merged file
OUTPUT_PATH = Path("merged2.json")            # overwrite in place; change if you want a new file


def call_subjective_crew(question: str) -> str:
    payload = {
        "user_input": question,
        "available_subjects": ', '.join(["Machine Learning", "Data Mining"]),
        "custom_memory": "",
        "last_subject": "",
        "supervisor_output": json.dumps({"route":"course", "reason":"new_query"}),
        "grade": "10",
    }

    # Kick off the crew and get the pydantic result
    result = SubjectiveCrew().crew().kickoff(payload).pydantic
    return result


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        items = json.load(f)

    updated = []
    for idx, item in enumerate(items, start=1):
        question = item.get("question")
        model_answer = call_subjective_crew(question)
        updated.append({
            "user_input":question,
            "response":model_answer.answer,
            "retrieved_contexts": retrieve_relevant_context_testing(model_answer.last_subject, "10", question),
            "reference": item.get("answer"),
        })

        # Optional: log progress every 10 items
        if idx % 10 == 0:
            print(f"Processed {idx} items")

    # Save updated JSON (overwrites merged.json by default)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(updated, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(updated)} items with model answers to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
