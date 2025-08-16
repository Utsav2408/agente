import json

from crew_flows_teacher.crews.supervisor_crew_teacher.supervisor_teacher import SupervisorTeacherCrew

# from your_module import SupervisorCrew  # Uncomment and adjust to your import

INPUT_FILE = "merged4.json"
OUTPUT_FILE = "merged4_with_predictions.json"

def update_with_predictions():
    # Load JSON data
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    updated_data = []
    
    for item in questions:
        sup_payload = {
            "user_input": item["question"],
            "conversation_history": ""
        }
        response = SupervisorTeacherCrew().crew().kickoff(sup_payload).pydantic
        
        # Assuming the crew returns a dict with a "route" key
        predicted_route = response.route.strip().lower()
        
        updated_item = {
            "question": item["question"],
            "route": item["route"],
            "predicted_route": predicted_route
        }
        updated_data.append(updated_item)

    # Save updated data to a new JSON file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)

    print(f"Updated file saved as {OUTPUT_FILE} with predicted routes.")

if __name__ == "__main__":
    update_with_predictions()
