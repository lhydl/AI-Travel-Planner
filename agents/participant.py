"""Specialist travel agents with distinct responsibilities and tool permissions."""

import re

from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from tools.trip_tools import run_tool
from utils import debug

PERSONAS = {
    "budget_advisor": {
        "name": "Budget Advisor",
        "role": "Keep the plan within the traveler's total budget. Identify trade-offs and protect a contingency.",
        "tools": ["budget_split"],
    },
    "itinerary_designer": {
        "name": "Itinerary Designer",
        "role": "Suggest a realistic day-by-day plan paced around the traveler's interests and energy.",
        "tools": ["day_outline"],
    },
    "logistics_planner": {
        "name": "Logistics Planner",
        "role": "Consider transport, accommodation location, travel time, group size, and practical sequencing.",
        "tools": ["budget_split", "day_outline"],
    },
}

TOOL_HELP = {
    "budget_split": "budget_split|budget=1200|currency=SGD. Allocates a user-supplied total across transport, lodging, food, activities, and contingency. Not a live quote.",
    "day_outline": "day_outline|days=5|interests=food and museums. Creates a flexible pacing outline, not verified venue recommendations.",
}


def participant(
    persona_id: str,
    state,
    allow_question: bool = True,
    require_question: bool = False,
) -> dict:
    if persona_id not in PERSONAS:
        return {"messages": [{"role": "assistant", "content": f"Unknown committee role: {persona_id}"}]}

    persona = PERSONAS[persona_id]
    history = "\n".join(message.get("content", "") for message in state.get("messages", []))
    available = "\n".join(f"- {TOOL_HELP[tool]}" for tool in persona["tools"])
    if not available:
        available = "No tools are available to this role."

    if require_question:
        question_policy = (
            "Before doing any planning or using tools, you MUST ask exactly one concise, role-specific question. "
            "Do not repeat details already provided; ask for a priority or preference that helps your role. "
            "Respond only as Question: [your one question]."
        )
    elif not allow_question:
        question_policy = (
            "You have already asked your one question. Do not ask another; use the answer and proceed with "
            "a reasonable, clearly stated assumption for anything still unknown."
        )
    else:
        question_policy = "Ask at most one concise question if a critical detail is missing."
    system = f"""You are the {persona['name']} in a travel planning committee.
Your job: {persona['role']}
Use the traveler's stated destination, dates/trip length, party size, budget/currency, interests,
and constraints. {question_policy} Do not ask for details that can be handled with an ordinary
planning assumption. Use reasonable, clearly labeled assumptions for nonessential gaps.
Never claim to have checked live flights, hotel prices, opening hours, visas, or safety conditions.
You may use only these tools:
{available}

If a question is required by the instructions above, ask it before any tool call. Otherwise, if a tool
would help, respond with exactly one line beginning Action: and use the format shown above.
The tool result will be supplied as an Observation on your next turn. Then output exactly one of:
Question: [one specific question for the traveler]
Report: [your concise, practical contribution, 2-5 sentences]
Do not address the traveler directly except through Question:. Reports are internal committee notes
for the final planner. Make estimates and assumptions clear. Do not expose private reasoning.
Do not create fake booking prices or claim a booking was made."""

    context = (
        "Complete the traveler's latest request. Earlier trip details and the current plan are context; "
        "apply requested changes and avoid repeating unrelated recommendations.\n\n"
        f"Traveler and committee conversation so far:\n{history}"
    )
    for _ in range(4):
        try:
            response = ChatOpenAI(model="gpt-5-mini", temperature=1).invoke([
                SystemMessage(content=system), HumanMessage(content=context),
            ])
            content = response.content if isinstance(response.content, str) else str(response.content)
            content = content.strip()
            action_match = re.search(r"^Action:\s*(.+)$", content, re.IGNORECASE | re.MULTILINE)
            if action_match:
                action = action_match.group(1).strip()
                requested_tool = action.split("|", 1)[0].strip().lower()
                if requested_tool not in persona["tools"]:
                    observation = f"Access denied: {persona['name']} does not have the {requested_tool} tool."
                else:
                    observation = run_tool(action)
                debug(f"{persona['name']} tool result: {observation}", "TOOL")
                context += f"\n\nAction: {action}\nObservation: {observation}"
                continue

            question_match = re.search(r"Question:\s*(.*)", content, re.IGNORECASE | re.DOTALL)
            report_match = re.search(r"Report:\s*(.*)", content, re.IGNORECASE | re.DOTALL)
            if question_match:
                final_message = f"Question: {question_match.group(1).strip()}"
            elif report_match:
                final_message = f"Report from {persona['name']}: {report_match.group(1).strip()}"
            else:
                final_message = f"Report from {persona['name']}: {content}"
            return {"messages": [{
                "role": "assistant",
                "name": persona["name"],
                "content": final_message,
            }]}
        except Exception as exc:
            debug(f"{persona['name']} LLM error: {exc}", "AGENT")
            return {"messages": [{
                "role": "assistant",
                "name": persona["name"],
                "content": f"Report from {persona['name']}: The planning model could not be reached, so this specialist could not complete their review.",
            }]}

    return {"messages": [{
        "role": "assistant", "name": persona["name"],
        "content": f"Report from {persona['name']}: I need a little more detail before I can make a useful recommendation.",
    }]}
