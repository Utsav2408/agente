from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini")

import json
from pathlib import Path
from typing import Any, Dict, List

MERGED_PATH = Path("rag_test.json")  # change if your file lives elsewhere

def load_dataset(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # handle common wrappers like {"data": [...]}
        for key in ("data", "items", "records", "rows", "examples"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # single object -> wrap it
        return [data]

    raise ValueError("merged.json must contain a JSON array or an object (optionally wrapping a list).")

dataset: List[Dict[str, Any]] = load_dataset(MERGED_PATH)
print(f"Loaded {len(dataset)} items from {MERGED_PATH}")



from ragas import EvaluationDataset
evaluation_dataset = EvaluationDataset.from_list(dataset)

from ragas import evaluate
from ragas.llms import LangchainLLMWrapper


evaluator_llm = LangchainLLMWrapper(llm)
from ragas.metrics import LLMContextRecall, Faithfulness, AnswerCorrectness, ResponseRelevancy, AnswerSimilarity

result = evaluate(dataset=evaluation_dataset,metrics=[LLMContextRecall(), Faithfulness(), AnswerCorrectness(), ResponseRelevancy(), AnswerSimilarity()],llm=evaluator_llm)
print(result)
