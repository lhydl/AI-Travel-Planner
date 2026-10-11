from state import State
from agents import participant, summarizer
from utils import record_user_input

COMMITTEE_ORDER = [
    "budget_advisor",
    "itinerary_designer",
    "logistics_planner",
]

FALLBACK_QUESTIONS = {
    "budget_advisor": "Which matters most if trade-offs are needed: the lowest total cost, more comfort, or more activities?",
    "itinerary_designer": "What one experience or interest should be the highlight of the itinerary?",
    "logistics_planner": "Would you prefer the most convenient base or a lower-cost area, assuming travel times are acceptable?",
}


def human_node(state: State) -> dict:
    """Collect the traveler's initial request."""
    user_input = input("\nWhat trip would you like the committee to plan?\nYou: ").strip()
    record_user_input(user_input)
    return {
        "messages": [{"role": "user", "content": f"Traveler: {user_input}"}],
    }


def followup_node(state: State) -> dict:
    """Ask whether the traveler wants to refine the plan or finish."""
    user_input = input("\nAnything else to add or change? (Type 'done' to finish)\nYou: ").strip()
    record_user_input(user_input)
    previous_plan = next(
        (message for message in reversed(state.get("messages", [])) if message.get("name") == "Trip Planner"),
        None,
    )
    messages = [previous_plan] if previous_plan else []
    messages.append({"role": "user", "content": f"Traveler follow-up: {user_input}"})
    return {"messages": messages}


def followup_routing(state: State) -> str:
    messages = state.get("messages", [])
    content = messages[-1].get("content", "") if messages else ""
    answer = content.split(":", 1)[-1].strip().lower()
    if answer in {"", "no", "no thanks", "nothing", "done", "exit", "quit"}:
        print("\nThanks for planning with the travel committee!")
        return "end"
    return "committee"


def committee_node(state: State) -> dict:
    """Run each specialist in the background and collect one answer from the traveler."""
    working_messages = list(state.get("messages", []))
    for speaker in COMMITTEE_ORDER:
        question_result = participant(
            speaker,
            {"messages": working_messages},
            require_question=True,
        )
        question_message = (question_result.get("messages") or [{}])[-1]
        persona_name = question_message.get("name", speaker)
        question_content = question_message.get("content", "")
        if question_content.startswith("Question:"):
            question = question_content.removeprefix("Question:").strip()
        else:
            # Ensure each specialist still asks exactly one question if the model
            # returns a report or fails to follow the required response format.
            question = FALLBACK_QUESTIONS[speaker]

        print(f"\n{persona_name}: {question}")
        answer = input("You: ").strip()
        record_user_input(answer)
        working_messages.append({
            "role": "user",
            "content": f"Traveler answer to {persona_name}: {answer}",
        })

        report_result = participant(
            speaker,
            {"messages": working_messages},
            allow_question=False,
        )
        report_messages = report_result.get("messages", [])
        if report_messages:
            report = report_messages[-1]
            if report.get("content", "").startswith("Question:"):
                report["content"] = (
                    f"Report from {persona_name}: Proceeding with an assumption after the clarification."
                )
            working_messages.extend(report_messages)

    return {"messages": working_messages}


def summarizer_node(state: State) -> dict:
    print("\nThe committee has finished planning.\n")
    print("=== YOUR TRIP PLAN ===\n")
    summary = summarizer(state)
    print(summary)
    return {
        "messages": state.get("messages", []) + [
            {"role": "assistant", "name": "Trip Planner", "content": summary}
        ]
    }
