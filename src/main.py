import os

from pprint import pprint
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict
from datetime import datetime
from models import WorkoutEntry, DecisionResult, TrendResult
from db import fetch_by_exercise, insert_entry, print_table
from typing import Literal


load_dotenv()


model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        temperature=0,
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )

# State passed between LangGraph nodes
class GraphState(TypedDict):
    message: str
    response: str
    workout: WorkoutEntry | None
    history: list
    trend: str
    decision: str
    reasoning: str
    recommendation: str

# Parse free-form workout text into a validated WorkoutEntry
def parse_node(state: GraphState):

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

# Analyze the trend of the current workout compared to recent history
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

    structured_model = model.with_structured_output(TrendResult)

    result = structured_model.invoke(trend_prompt)


    return {
        # Return the trend classification in lowercase
        "trend": result.trend.lower(),
    }

# Make a training decision based on the current workout, history, and trend
def decide_node(state: GraphState):
    workout = state["workout"]
    history = state["history"]
    trend = state["trend"]

    if workout is None:
        return {
            "decision": "hold",
            "reasoning": "No valid workout data was available.",
            "recommendation": "Maintain the current training approach until more data is available.",
        }


    structured_model = model.with_structured_output(DecisionResult)

    decision_prompt = f"""
    Make a training decision based on the athlete's current workout,
    recent workout history, and detected training trend.

    Current workout:
    {workout}

    Recent history:
    {history}

    Detected trend:
    {trend}

    Choose exactly one decision:
    - progress
    - hold
    - deload
    - flag

    Decision guidelines:

    1. FLAG:
       Use this when the athlete reports pain, injury, or a concerning
       physical issue. Safety takes priority over performance.

    2. DELOAD:
       Use this when there are recurring fatigue, recovery, or performance
       issues suggesting that training stress should be reduced.

    3. PROGRESS:
       Use this when the athlete has plateaued but there are no significant
       safety or recovery concerns. Progress means making a deliberate
       progression adjustment, such as increasing weight, reps, or another
       training variable. Do not automatically increase weight.

    4. HOLD:
       Use this when the athlete is already progressing appropriately,
       when maintaining the current approach is preferable, or when there
       is insufficient evidence to justify a more aggressive decision.

    Consider the exercise, weight, reps, RPE, notes, recent history, and
    detected trend together. Do not use rigid numerical rules.

    Return:
    - decision: exactly one of progress, hold, deload, flag
    - reasoning: explain why this decision was selected
    - recommendation: give a concise actionable recommendation for the athlete
    """

    result = structured_model.invoke(decision_prompt)

    return {
        "decision": result.decision.lower(),
        "reasoning": result.reasoning,
        "recommendation": result.recommendation,
    }

# Generate a short plain-language recommendation based on the decision and trend
def advise_node(state: GraphState):

    decision = state["decision"]
    trend = state["trend"]

    advise_prompt = f"""
    Give the athlete a short, plain-language training recommendation.

    Decision:
    {decision}

    Training trend:
    {trend}

    Rules:
    - Keep the recommendation concise and actionable.
    - Explain what the athlete should do next.
    - Do not introduce a new training decision.
    - Do not contradict the provided decision.
    - Use simple language suitable for an athlete.

    Return only the recommendation.
    """

    response = model.invoke(advise_prompt)

    return {
        "recommendation": response.content,
    }

# Build the LangGraph state machine
graph_builder = StateGraph(GraphState)

# Add nodes to the graph
graph_builder.add_node("parse_node", parse_node)
graph_builder.add_node("fetch_history_node", fetch_history_node)
graph_builder.add_node("analyze_trend_node", analyze_trend_node)
graph_builder.add_node("decide_node", decide_node)
graph_builder.add_node("advise_node", advise_node)

# Connect the nodes in the desired order
graph_builder.add_edge(START, "parse_node")
graph_builder.add_edge("parse_node", "fetch_history_node")
graph_builder.add_edge("fetch_history_node", "analyze_trend_node")
graph_builder.add_edge("analyze_trend_node", "decide_node")

def route_decision(state: GraphState):
    return state["decision"]

graph_builder.add_conditional_edges(
    "decide_node",
    route_decision,
    {
        "progress": "advise_node",
        "hold": "advise_node",
        "deload": "advise_node",
        "flag": "advise_node",
    },
)
graph_builder.add_edge("advise_node", END)

graph = graph_builder.compile()



def run_workout(journal: str):
    return graph.invoke(
        {
            "message": journal,
            "response": "",
            "workout": None,
            "history": [],
            "trend": "",
            "decision": "",
            "reasoning": "",
            "recommendation": "",
        }
    )


if __name__ == "__main__":

    #manual test

    journal = """
    Bench press:
    80kg x 8
    80kg x 8
    80kg x 7

    Felt strong today. Last set was difficult but controlled.
    """

    result = run_workout(journal)

    print("\nWorkout:")
    pprint(result["workout"].model_dump())
    print(f"\nHistory: {len(result['history'])} previous sessions")
    print(f"Trend: {result['trend']}")
    print(f"Decision: {result['decision']}")
    print(f"Reasoning: {result['reasoning']}")
    print(f"Recommendation: {result['recommendation']}")