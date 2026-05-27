CLARIFY_SYSTEM = "You are xiaoSU, a new AI intern. Politely confirm missing details with the teacher."

CLARIFY_USER_TEMPLATE = "Teacher: {message}. Missing: {missing_slots}. Slots: {slot_details}. Generate polite clarify. Start with receive teacher~. 1-3 options. End with reply confirm for defaults."

def build_clarify_prompt(message, missing_slots, slots):
    slot_details = []
    for name in missing_slots:
        for s in slots:
            if s["name"] == name:
                hint = s.get("hint", "")
                slot_details.append(f"- {s["label"]}: {hint}")
    return CLARIFY_USER_TEMPLATE.format(message=message, missing_slots=", ".join(missing_slots), slot_details=chr(10).join(slot_details))
