from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
import os
from pathlib import Path
import sys

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from nodes import committee_node, followup_node, followup_routing, human_node, summarizer_node
from state import State

load_dotenv(override=True)


class Tee:
    """Write console output to both the terminal and the run log."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for stream in self.streams:
            stream.write(text)
        return len(text)

    def flush(self):
        for stream in self.streams:
            stream.flush()

    def isatty(self):
        return any(getattr(stream, "isatty", lambda: False)() for stream in self.streams)


def build_graph():
    """Collect one trip request, run the committee, then present one combined plan."""
    builder = StateGraph(State)
    builder.add_node("traveler", human_node)
    builder.add_node("committee", committee_node)
    builder.add_node("summarizer", summarizer_node)
    builder.add_node("followup", followup_node)
    builder.add_edge(START, "traveler")
    builder.add_edge("traveler", "committee")
    builder.add_edge("committee", "summarizer")
    builder.add_edge("summarizer", "followup")
    builder.add_conditional_edges(
        "followup", followup_routing,
        {"committee": "committee", "end": END},
    )
    return builder.compile()


def main():
    log_path = Path(os.getenv("TRAVEL_PLANNER_LOG", "logs/travel_planner.log"))
    if not log_path.is_absolute():
        log_path = Path(__file__).resolve().parent / log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)
    os.environ["TRAVEL_PLANNER_LOG"] = str(log_path)

    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"\n\n=== Run started {datetime.now().astimezone().isoformat(timespec='seconds')} ===\n")
        log_file.flush()
        output = Tee(sys.stdout, log_file)
        errors = Tee(sys.stderr, log_file)
        with redirect_stdout(output), redirect_stderr(errors):
            print("=== TRAVEL PLANNING COMMITTEE ===")
            print("Describe your trip in one request. Include destination (or ask for ideas), dates or trip length,")
            print("group size, budget and currency, interests, and constraints if you know them.")
            print("The three specialists will work in the background and ask one role-specific question each.\n")
            graph = build_graph()
            initial_state = State(messages=[])
            try:
                graph.invoke(initial_state, config={"recursion_limit": 10000})
            except KeyboardInterrupt:
                print("\nPlanning interrupted. Goodbye!")
            except Exception as exc:
                print(f"\nAn error occurred: {exc}")
                print("Check that OPENAI_API_KEY is set in your .env file and try again.")


if __name__ == "__main__":
    main()
