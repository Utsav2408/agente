import os, re
import glob
import json
import logging
from typing import List

from pydantic import BaseModel
from litellm import completion
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from test_set_generator.prompt import prompt_template

# set up logging
global_logger = logging.getLogger("CodeLogs")
logging.basicConfig(level=logging.INFO)

class Record(BaseModel):
    question: str
    answer: str

class Response(BaseModel):
    generated: List[Record]

def llm_call(data: str, num_records: int = 1) -> dict:
    """Stream LLM response and return parsed JSON."""

    stream = completion(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": prompt_template(data, num_records)}],
        max_tokens=2000,
        response_format=Response,
        stream=True
    )
    
    collected = ""
    for chunk in stream:
        delta = chunk['choices'][0]["delta"]["content"]
        if delta is not None:
            collected += delta
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", collected.strip(), flags=re.DOTALL)
    return json.loads(cleaned)

if __name__ == "__main__":
    try:
        input_dir = "test_data/raw"
        output_dir = "test_data/jsons"
        os.makedirs(output_dir, exist_ok=True)

        # initialize once
        converter = DocumentConverter()
        chunker = HybridChunker()

        # find all PDFs in data/raw
        pdf_paths = glob.glob(os.path.join(input_dir, "*.pdf"))

        for pdf_path in pdf_paths:
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            global_logger.info(f"Processing {base_name}.pdf")

            # convert & chunk
            doc = converter.convert(pdf_path).document
            chunks = chunker.chunk(dl_doc=doc)

            # build dataset
            dataset = {}
            for i, chunk in enumerate(chunks):
                enriched = chunker.contextualize(chunk=chunk)
                # call LLM
                gen = llm_call(enriched)
                dataset[i] = {
                    "context": enriched,
                    "generated": gen["generated"],
                }

            # write out JSON
            out_path = os.path.join(output_dir, f"{base_name}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(dataset, f, ensure_ascii=False, indent=2)

            global_logger.info(f"Wrote {out_path}")
    except Exception as e:
        print(e)
