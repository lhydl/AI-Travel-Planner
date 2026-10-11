# Travel Planning Committee

A small multi-agent travel planner built with LangGraph. The traveler makes one request, then three specialist agents work behind the scenes. If a specialist needs an essential detail, it can ask the traveler once and resume planning. The final summarizer combines the committee's work into one trip brief.

## Committee roles

- **Budget Advisor** allocates the stated budget across transport, accommodation, food, activities, and contingency.
- **Itinerary Designer** drafts a day-by-day pacing outline around the traveler's interests.
- **Logistics Planner** considers transport, accommodation location, group size, and sequence.
The committee processes the request in sequence; its internal reports are not shown as conversational turns. Each specialist asks exactly one role-specific question, then proceeds using the answer and reasonable assumptions for any remaining gaps. After presenting the plan, the program asks whether the traveler wants to add or change anything. It continues planning until the traveler types `done`, `exit`, `quit`, or `no`.

## Setup

Requires Python 3.12+ and an OpenAI API key.

```sh
uv sync
cp .env.example .env
```

Put your key in `.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
DEBUG=false
```

Run:

```sh
uv run python main.py
```

Console output is shown in the terminal and appended to `logs/travel_planner.log`, including traveler responses to prompts. Set `TRAVEL_PLANNER_LOG` in `.env` to choose another path.

Example opening request:

> Plan a 5-day trip to Penang for two people in March. Our total budget is SGD 2,000. We like hawker food, heritage, and relaxed walks. Avoid very packed days.

## Agent and tool flow

`main.py` defines a LangGraph workflow: traveler input → committee → final summarizer → follow-up prompt. The committee runs each specialist in sequence. Each specialist asks one clarification; the answer is added to the shared context and that same specialist resumes before the next agent runs. If the model fails to produce a question in the expected format, the app uses a role-specific fallback question. A follow-up request starts another planning pass using the existing trip plan as context.

Agents share the request, clarifications, and internal reports through `state.py`. The budget advisor has access to `budget_split`; the itinerary designer has access to `day_outline`; the logistics planner has both. Tools are dispatched in `tools/trip_tools.py` and return deterministic planning aids. Budget categories are allocations of the traveler's own stated total, not market prices. The itinerary outline does not verify specific venues or opening hours.

The LLM agents do not search the live web, check booking availability, or make reservations. Verify actual prices, schedules, entry requirements, and opening hours before booking. If the model call fails, the program reports a fallback response; a valid `OPENAI_API_KEY` is required for normal use.
