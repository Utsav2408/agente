import json

from crew_flows_teacher.crews.announcement_flow.announcement_creator_crew.announcement_creator_crew import AnnouncementCreatorCrew

# from your_module import SupervisorCrew  # Uncomment and adjust to your import

INPUT_FILE = "merged5.json"
OUTPUT_FILE = "merged5_with_predictions.json"

def update_with_predictions():
    # Load JSON data
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    updated_data = []
    
    for item in questions:
        payload = {
            "user_query": item["user_input"],
            "last_announcement_class": "",
            "last_announcement_summary": "",
            "last_announcement_event_date": ""
        }
        crew_response = AnnouncementCreatorCrew().crew().kickoff(payload).pydantic

        updated_item = {
            "user_input": item["user_input"],
            "reference": item["reference"],
            "response": f"Title: {crew_response.announcement_title}\nClass: {crew_response.announcement_class}\nBody: {crew_response.draft_announcement}\nEvent Date: {crew_response.announcement_event_date}"
        }
        updated_data.append(updated_item)

    # Save updated data to a new JSON file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)

    print(f"Updated file saved as {OUTPUT_FILE} with predicted routes.")

if __name__ == "__main__":
    update_with_predictions()
