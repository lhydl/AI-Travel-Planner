"""Small deterministic tools used by the travel committee agents."""

def budget_split(budget: float, currency: str = "SGD") -> str:
    """Split a user-provided total budget into planning envelopes, not price quotes."""
    shares = {
        "Transport": 0.35,
        "Accommodation": 0.30,
        "Food": 0.20,
        "Activities": 0.10,
        "Contingency": 0.05,
    }
    lines = [f"Planning allocation for {currency.upper()} {budget:,.2f} (not live prices):"]
    lines.extend(f"- {name}: {currency.upper()} {budget * share:,.2f} ({share:.0%})" for name, share in shares.items())
    lines.append("Check actual transport and lodging prices for the dates before booking.")
    return "\n".join(lines)


def day_outline(days: int, interests: str = "mix of local highlights and downtime") -> str:
    """Create a lightweight pacing outline from trip length and interests."""
    days = max(1, min(int(days), 14))
    interests = interests.strip() or "local highlights and downtime"
    lines = [f"Draft {days}-day pacing outline, focused on {interests}:"]
    for day in range(1, days + 1):
        if day == 1:
            activity = "Arrival, check in, and an easy nearby meal"
        elif day == days:
            activity = "Flexible morning, check out, and departure"
        else:
            activity = f"One main {interests} activity, a nearby meal, and free time"
        lines.append(f"Day {day}: {activity}.")
    lines.append("These are planning prompts; choose specific venues after confirming location and opening hours.")
    return "\n".join(lines)


def run_tool(action: str) -> str:
    """Parse the constrained Action line emitted by an agent and dispatch its tool."""
    try:
        name, *parts = action.strip().split("|")
        args = {}
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                args[key.strip().lower()] = value.strip()
        if name.strip().lower() == "budget_split":
            budget = float(args["budget"])
            if budget <= 0:
                return "Budget must be a positive number."
            return budget_split(budget, args.get("currency", "SGD"))
        if name.strip().lower() == "day_outline":
            return day_outline(int(args["days"]), args.get("interests", ""))
        return f"Unknown or unavailable tool: {name.strip()}"
    except (KeyError, ValueError):
        return "Tool input was incomplete or invalid. Ask for the missing budget, days, or currency."
