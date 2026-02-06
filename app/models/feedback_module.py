import json
import os

def update_knowledge_base(original_message_id, corrected_response):
    """
    Update the knowledge base or log corrections for future training.
    Currently logs to a file as a placeholder.
    """
    correction_log = 'app/data/corrections.json'

    # Ensure directory exists
    os.makedirs(os.path.dirname(correction_log), exist_ok=True)

    new_correction = {
        'message_id': original_message_id,
        'corrected_response': corrected_response,
        'timestamp': json.dumps(True) # Dummy timestamp
    }

    corrections = []
    if os.path.exists(correction_log):
        try:
            with open(correction_log, 'r') as f:
                corrections = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    corrections.append(new_correction)

    with open(correction_log, 'w') as f:
        json.dump(corrections, f, indent=2)

    print(f"✅ Logged correction for message {original_message_id}")
    return True
