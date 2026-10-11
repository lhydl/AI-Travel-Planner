from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


def summarizer(state) -> str:
    """Turn the committee discussion into a concise, usable trip brief."""
    messages = state.get("messages", [])
    conversation = "\n".join(m.get("content", "") for m in messages)
    if not conversation.strip():
        return "No trip details were provided."
    system = """Create a clear trip-planning brief from the conversation. Include the destination and
traveler preferences, proposed itinerary, budget allocation and assumptions, practical logistics,
open questions, and next steps. Preserve uncertainty: don't invent dates, prices, availability, or
booking confirmations. If this is a follow-up, incorporate the latest requested changes and supersede
earlier recommendations where they conflict. If the group has not chosen a destination, present the
recommendations as options."""
    try:
        response = ChatOpenAI(model="gpt-5-nano", temperature=1).invoke([
            SystemMessage(content=system),
            HumanMessage(content=f"Committee conversation:\n{conversation}\n\nWrite the final trip brief."),
        ])
        result = response.content
        if not isinstance(result, str):
            result = " ".join(str(item) for item in result)
        return f"=== TRIP PLANNING BRIEF ===\n\n{result.strip()}"
    except Exception:
        return (
            "=== TRIP PLANNING BRIEF ===\n\n"
            f"Model summary unavailable. Here is the planning discussion:\n{conversation}"
        )
