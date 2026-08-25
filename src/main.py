import os

from pprint import pprint
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict
from datetime import datetime
from models import TrendResult, WorkoutEntry
from db import fetch_by_exercise, insert_entry, print_table

load_dotenv()


# State passed between LangGraph nodes
class GraphState(TypedDict):
    message: str
    response: str
    workout: WorkoutEntry | None
    history: list
    trend: str


# Parse free-form workout text into a validated WorkoutEntry
def parse_node(state: GraphState):
    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        temperature=0,
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )

    structured_model = model.with_structured_output(WorkoutEntry)

    current_timestamp = datetime.now().astimezone()

    prompt = f"""
                Extract the workout information from this journal entry.

                Journal:
                {state["message"]}

                Rules:
                - Extract every individual set with its weight and reps.
                - Preserve the order of the sets exactly as described in the journal.
                - Do not combine sets with different weights or reps.
                - If the same weight and reps are repeated for multiple sets, create a separate set entry for each set.
                - Infer RPE only from effort language.
                - Struggling, grinding, barely finishing → RPE 9-10.
                - Tough but controlled → RPE 7-8.
                - Normal/moderate → RPE 5-6.
                - Easy/light → RPE 3-4.
                - If no effort language is present, set rpe to null.
                - Do not invent an RPE when there is no evidence.
                - Return only information supported by the journal.
                - If the journal does not explicitly provide a workout date/time, leave timestamp as null.
                """

    workout = structured_model.invoke(prompt)

    workout.timestamp = current_timestamp
    return {"workout": workout}


# Fetch the last 8 workouts for the same exercise
def fetch_history_node(state: GraphState):
    workout = state["workout"]

    if workout is None:
        return {"history": []}

    rows = fetch_by_exercise(workout.exercise, limit=8)

    history = []

    for row in rows:
        history.append(
            {
                "id": row[0],
                "exercise": row[1],
                "sets": row[2],
                "rpe": row[3],
                "notes": row[4],
                "timestamp": row[5],
            }
        )

    return {"history": history}


def analyze_trend_node(state: GraphState):

    workout = state["workout"]
    history = state["history"]

    if workout is None or not history:
        return {
            "trend": "insufficient_history",
        }

    # Give the LLM the recent workout history and today's workout
    trend_prompt = f"""
    Analyze the training trend for this exercise.

    Exercise: {workout.exercise}

    Recent workout history:
    {history}

    Today's workout:
    Sets: {workout.sets}
    RPE: {workout.rpe}
    Notes: {workout.notes}

    Classify the trend as exactly one of:
    - progression
    - plateau
    - recurring_issue

    Use the exercise type, sets, weight, reps, RPE, notes,
    and the progression across sessions.

    Do not use rigid numerical rules. Use your judgment
    based on the actual exercise and training history.

    Return only the trend classification.
    """

    # Let Gemini interpret the history
    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        temperature=0,
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )

    structured_model = model.with_structured_output(TrendResult)

    result = structured_model.invoke(trend_prompt)

    return {
        "trend": result.trend.lower(),
    }


# Build the graph: START → parse_node → END
graph_builder = StateGraph(GraphState)
graph_builder.add_node("parse_node", parse_node)
graph_builder.add_node("fetch_history_node", fetch_history_node)
graph_builder.add_node("analyze_trend_node", analyze_trend_node)
graph_builder.add_edge(START, "parse_node")
graph_builder.add_edge("parse_node", "fetch_history_node")
graph_builder.add_edge("fetch_history_node", "analyze_trend_node")
graph_builder.add_edge("analyze_trend_node", END)
graph = graph_builder.compile()


if __name__ == "__main__":
    test_entries = [
        "Bench press: 77.5kg x 8, 72.5kg x 10, 67.5kg x 8. Felt strong and controlled.",
        "Bench press: 70kg x 10, 70kg x 8, 65kg x 8. Felt normal today.",
        "Bench press: 80kg x 5, 75kg x 7, 70kg x 7. Very heavy and difficult.",
        "Bench press: 67.5kg x 8, 62.5kg x 8, 57.5kg x 8. Shoulder pain returned again.",
        "Overhead press: 40kg x 8, 40kg x 7, 35kg x 6.",
    ]

    for i, journal in enumerate(test_entries, start=1):
        result = graph.invoke(
            {
                "message": journal,
                "response": "",
                "workout": None,
                "history": [],
                "trend": "",
            }
        )

        print(f"\n{'=' * 70}")
        print(f"TEST {i}")
        print(f"{'=' * 70}")

        print(f"Journal: {journal}")

        print("\nWorkout:")
        pprint(result["workout"].model_dump())

        print(f"\nHistory: {len(result['history'])} previous sessions")
        print(f"Trend: {result['trend']}")

        print(f"{'=' * 70}")

        insert_entry(result["workout"])

    # print_table()
