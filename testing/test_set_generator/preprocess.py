import os
import glob
import json
from colorama import Fore

if __name__ == "__main__":
    input_dir = "test_data/jsons"
    # find all .json files under data/jsons
    json_paths = glob.glob(os.path.join(input_dir, "*.json"))

    for path in json_paths:
        base = os.path.basename(path)
        print(Fore.CYAN + f"\n→ Processing {base}" + Fore.RESET)

        # load the existing nested structure
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        instructions = []
        # data is a dict of chunks; each chunk has a 'generated' list
        for chunk in data.values():
            for rec in chunk.get("generated", []):
                instructions.append({
                    "question": rec["question"],
                    "answer": rec["answer"],
                })

        # overwrite the same file with the flat list
        with open(path, "w", encoding="utf-8") as f:
            json.dump(instructions, f, ensure_ascii=False, indent=2)

        print(Fore.GREEN + f"  ✔ Updated {base} with {len(instructions)} Q&A pairs" + Fore.RESET)
