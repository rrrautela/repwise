import streamlit as st
import pandas as pd
import json
import altair as alt
from datetime import date, timedelta

from main import run_workout
from db import fetch_by_exercise, fetch_exercises, insert_entry

st.set_page_config(
    page_title="Repwise",
    page_icon="🏋️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================================
# STYLING
# ============================================================

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 12% 15%, rgba(34,211,238,0.07), transparent 40%),
                radial-gradient(circle at 88% 8%, rgba(167,139,250,0.08), transparent 42%),
                radial-gradient(circle at 50% 100%, rgba(74,222,128,0.05), transparent 45%),
                linear-gradient(180deg, #0a0c12 0%, #12141c 100%);
        }

        #MainMenu, footer, header { visibility: hidden; }

        /* ---------- Header ---------- */
        .rw-header {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 2px;
        }
        .rw-header-emoji {
            font-size: 2.3rem;
            filter: drop-shadow(0 0 12px rgba(34,211,238,0.35));
        }
        .rw-header-title {
            font-size: 2.1rem;
            font-weight: 800;
            margin: 0;
            letter-spacing: -0.5px;
            background: linear-gradient(90deg, #22d3ee, #a78bfa 60%, #f472b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .rw-caption {
            color: #8b93a7;
            font-size: 0.95rem;
            margin-top: -4px;
        }

        .rw-stat-strip {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin: 16px 0 6px 0;
        }
        .rw-chip {
            background: rgba(255,255,255,0.035);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 999px;
            padding: 7px 16px;
            font-size: 0.85rem;
            font-weight: 600;
            color: #d1d5db;
            backdrop-filter: blur(6px);
        }

        .rw-divider {
            height: 1px;
            border: none;
            margin: 22px 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.14), transparent);
        }

        /* ---------- Cards ---------- */
        .rw-card {
            background: rgba(255,255,255,0.035);
            border: 1px solid rgba(255,255,255,0.09);
            border-radius: 16px;
            padding: 18px 20px;
            margin-bottom: 14px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.25);
        }
        .rw-insight {
            background: linear-gradient(120deg, rgba(34,211,238,0.08), rgba(167,139,250,0.06));
            border: 1px solid rgba(167,139,250,0.25);
            border-radius: 16px;
            padding: 16px 20px;
            margin-bottom: 18px;
            font-size: 0.95rem;
            color: #e5e7eb;
        }

        /* ---------- Badges ---------- */
        .rw-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 16px;
            border-radius: 999px;
            font-weight: 700;
            font-size: 0.98rem;
            letter-spacing: 0.2px;
        }
        .rw-label {
            color: #8b93a7;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 1.3px;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        .rw-set-pill {
            display: inline-block;
            background: rgba(34,211,238,0.08);
            border: 1px solid rgba(34,211,238,0.28);
            color: #cffafe;
            border-radius: 10px;
            padding: 6px 12px;
            margin: 3px 6px 3px 0;
            font-size: 0.9rem;
            font-family: 'SFMono-Regular', Consolas, monospace;
            transition: all 0.15s ease;
        }
        .rw-set-pill:hover {
            border-color: rgba(34,211,238,0.6);
            transform: translateY(-1px);
        }

        .rw-pr {
            background: rgba(250,204,21,0.1);
            border: 1px solid rgba(250,204,21,0.35);
            color: #fde68a;
            border-radius: 10px;
            padding: 3px 11px;
            font-size: 0.78rem;
            font-weight: 700;
            margin-left: 8px;
        }

        .rw-delta-up { color: #4ade80; font-weight: 700; font-size: 0.85rem; }
        .rw-delta-down { color: #f87171; font-weight: 700; font-size: 0.85rem; }
        .rw-delta-flat { color: #9ca3af; font-weight: 700; font-size: 0.85rem; }

        /* ---------- Metrics ---------- */
        div[data-testid="stMetricValue"] { font-size: 1.55rem; font-weight: 700; }
        div[data-testid="stMetric"] {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 14px;
            padding: 10px 14px 4px 14px;
        }

        /* ---------- Tabs ---------- */
        .stTabs [data-baseweb="tab-list"] { gap: 6px; }
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(255,255,255,0.03);
            border-radius: 10px 10px 0 0;
            padding: 10px 22px;
            color: #8b93a7;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(90deg, rgba(34,211,238,0.14), rgba(167,139,250,0.14));
            color: #f4f4f5 !important;
        }

        /* ---------- Buttons ---------- */
        .stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #22d3ee, #a78bfa);
            border: none;
            color: #0a0c12;
            font-weight: 700;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .stButton > button[kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 24px rgba(34,211,238,0.25);
        }

        textarea { border-radius: 12px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# HELPERS
# ============================================================

DECISION_STYLE = {
    "progress": ("🚀", "#22c55e", "rgba(34,197,94,0.12)", "rgba(34,197,94,0.35)"),
    "hold":     ("🧘", "#60a5fa", "rgba(96,165,250,0.12)", "rgba(96,165,250,0.35)"),
    "deload":   ("🛟", "#fb923c", "rgba(251,146,60,0.12)", "rgba(251,146,60,0.35)"),
    "flag":     ("🚩", "#f87171", "rgba(248,113,113,0.14)", "rgba(248,113,113,0.4)"),
}

TREND_STYLE = {
    "progression":          ("📈", "#22c55e", "rgba(34,197,94,0.12)", "rgba(34,197,94,0.35)"),
    "plateau":              ("➖", "#9ca3af", "rgba(156,163,175,0.12)", "rgba(156,163,175,0.35)"),
    "recurring_issue":      ("⚠️", "#f87171", "rgba(248,113,113,0.14)", "rgba(248,113,113,0.4)"),
    "insufficient_history": ("🌱", "#a78bfa", "rgba(167,139,250,0.12)", "rgba(167,139,250,0.35)"),
}


def badge_html(label: str, style_map: dict, key: str) -> str:
    icon, color, bg, border = style_map.get(
        key, ("•", "#9ca3af", "rgba(156,163,175,0.12)", "rgba(156,163,175,0.35)")
    )
    return (
        f'<span class="rw-badge" style="color:{color};background:{bg};'
        f'border:1px solid {border};">{icon} {label}</span>'
    )


def extract_text(recommendation) -> str:
    if isinstance(recommendation, list):
        return "".join(
            block.get("text", "")
            for block in recommendation
            if isinstance(block, dict)
        )
    return recommendation


def get_all_time_pr(exercise: str) -> float:
    """Highest single-set weight ever logged for this exercise."""
    rows = fetch_by_exercise(exercise, limit=1000)
    best = 0.0
    for row in rows:
        sets = json.loads(row[2])
        for s in sets:
            best = max(best, s["weight"])
    return best


def delta_arrow(current: float, previous: float) -> str:
    if previous == 0:
        return ""
    change = current - previous
    pct = (change / previous) * 100
    if abs(pct) < 1:
        return '<span class="rw-delta-flat">→ steady</span>'
    if change > 0:
        return f'<span class="rw-delta-up">▲ {pct:.0f}% vs last session</span>'
    return f'<span class="rw-delta-down">▼ {abs(pct):.0f}% vs last session</span>'


@st.cache_data(ttl=20)
def get_global_stats():
    exercises = fetch_exercises()
    total_sessions = 0
    timestamps = []

    for ex in exercises:
        rows = fetch_by_exercise(ex, limit=1000)
        total_sessions += len(rows)
        timestamps.extend(row[5] for row in rows)

    return {
        "exercises": exercises,
        "total_sessions": total_sessions,
        "timestamps": timestamps,
    }


def compute_streak(timestamps) -> int:
    if not timestamps:
        return 0

    days = sorted({pd.to_datetime(t).date() for t in timestamps}, reverse=True)
    today = date.today()

    if days[0] not in (today, today - timedelta(days=1)):
        return 0

    streak = 1
    for i in range(1, len(days)):
        if (days[i - 1] - days[i]).days == 1:
            streak += 1
        else:
            break
    return streak


def day_tick_values(df: pd.DataFrame) -> list:
    """One tick per calendar day, regardless of how many sessions fall on it."""
    return sorted(pd.to_datetime(df["Date"].dt.date).unique().tolist())


def trend_chart(df: pd.DataFrame, y_field: str, y_title: str, color: str, height: int = 280):
    """Line + soft area chart with clean, deduplicated day-level x-axis ticks."""

    ticks = day_tick_values(df)

    x_enc = alt.X(
        "Date:T",
        title="",
        axis=alt.Axis(
            values=ticks,
            format="%b %d",
            labelAngle=-40,
            labelColor="#9ca3af",
            grid=False,
            domainColor="rgba(255,255,255,0.15)",
            tickColor="rgba(255,255,255,0.15)",
        ),
    )

    base = alt.Chart(df).encode(x=x_enc)

    area = base.mark_area(
        line=False,
        opacity=0.12,
        color=color,
    ).encode(
        y=alt.Y(
            f"{y_field}:Q",
            title=y_title,
            axis=alt.Axis(labelColor="#9ca3af", titleColor="#9ca3af", gridColor="rgba(255,255,255,0.06)"),
        ),
    )

    line = base.mark_line(
        point=alt.OverlayMarkDef(color=color, size=55, filled=True),
        color=color,
        strokeWidth=3,
    ).encode(
        y=alt.Y(f"{y_field}:Q"),
        tooltip=[
            alt.Tooltip("Date:T", title="Date", format="%b %d, %Y"),
            alt.Tooltip(f"{y_field}:Q", title=y_title),
        ],
    )

    return (
        (area + line)
        .properties(height=height)
        .configure_view(strokeWidth=0)
    )


def volume_insight(df: pd.DataFrame):
    """Simple first-half vs second-half comparison to surface a headline trend."""
    if len(df) < 3:
        return None

    mid = len(df) // 2
    first_half_avg = df["Volume"].iloc[:mid].mean()
    second_half_avg = df["Volume"].iloc[mid:].mean()

    if first_half_avg == 0:
        return None

    pct = ((second_half_avg - first_half_avg) / first_half_avg) * 100

    if pct >= 5:
        return f"📈 Volume is trending up **{pct:.0f}%** across your recent sessions for this exercise. Keep it going."
    if pct <= -5:
        return f"📉 Volume has dropped **{abs(pct):.0f}%** across your recent sessions. Might be worth checking recovery or notes."
    return "➖ Volume has been fairly steady across your recent sessions for this exercise."


# ============================================================
# HEADER
# ============================================================

stats = get_global_stats()
streak = compute_streak(stats["timestamps"])

st.markdown(
    """
    <div class="rw-header">
        <div class="rw-header-emoji">🏋️</div>
        <div>
            <p class="rw-header-title">Repwise</p>
            <p class="rw-caption">Your AI training partner — logs, reads, and coaches you.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="rw-stat-strip">
        <span class="rw-chip">🔥 {streak}-day streak</span>
        <span class="rw-chip">📅 {stats['total_sessions']} sessions logged</span>
        <span class="rw-chip">🎯 {len(stats['exercises'])} exercises tracked</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<hr class="rw-divider">', unsafe_allow_html=True)

log_tab, history_tab = st.tabs(["📝 Log Workout", "📊 History"])

# ============================================================
# LOG WORKOUT
# ============================================================

with log_tab:

    st.markdown('<p class="rw-label">Workout journal</p>', unsafe_allow_html=True)

    with st.expander("Need an example?"):
        st.code(
            "Bench press:\n"
            "80kg x 8\n"
            "80kg x 8\n"
            "80kg x 7\n\n"
            "Felt strong today. Last set was difficult but controlled.",
            language=None,
        )

    journal = st.text_area(
        "Workout journal",
        placeholder=(
            "Bench press:\n80kg x 8\n80kg x 8\n80kg x 7\n\n"
            "Felt strong today. Last set was difficult but controlled."
        ),
        height=180,
        label_visibility="collapsed",
    )

    analyze_clicked = st.button(
        "Analyze Workout",
        type="primary",
        use_container_width=True,
    )

    if analyze_clicked:

        if not journal.strip():
            st.warning("Write down your workout first — even a few lines is enough.")
            st.stop()

        with st.spinner("Reading your journal, checking history, thinking it through..."):
            try:
                result = run_workout(journal)

                pr_before_insert = 0.0
                if result["workout"] is not None:
                    pr_before_insert = get_all_time_pr(result["workout"].exercise)
                    insert_entry(result["workout"])
                    get_global_stats.clear()

            except Exception as e:
                st.error("Something went wrong while analyzing your workout.")
                st.caption(f"Error: {e}")
                st.stop()

        if result["workout"] is not None:
            st.toast("Workout logged", icon="✅")

        st.markdown('<hr class="rw-divider">', unsafe_allow_html=True)

        workout = result["workout"]

        # ---------- Trend + Decision badges ----------

        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<p class="rw-label">Trend</p>', unsafe_allow_html=True)
            st.markdown(
                badge_html(
                    result["trend"].replace("_", " ").title(),
                    TREND_STYLE,
                    result["trend"],
                ),
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown('<p class="rw-label">Decision</p>', unsafe_allow_html=True)
            st.markdown(
                badge_html(
                    result["decision"].title(),
                    DECISION_STYLE,
                    result["decision"],
                ),
                unsafe_allow_html=True,
            )

        st.write("")

        # ---------- Recommendation ----------

        st.markdown('<p class="rw-label">Recommendation</p>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="rw-card">{extract_text(result["recommendation"])}</div>',
            unsafe_allow_html=True,
        )

        # ---------- Reasoning ----------

        with st.expander("Why this decision?"):
            st.write(result["reasoning"])

        # ---------- Workout details ----------

        with st.expander("Workout details", expanded=True):

            if workout is not None:

                st.markdown(f"**Exercise:** {workout.exercise}")

                today_max = max(s.weight for s in workout.sets)


                pills = "".join(
                    f'<span class="rw-set-pill">{s.weight}kg × {s.reps}</span>'
                    for s in workout.sets
                )
                pr_tag = (
                    '<span class="rw-pr">🏆 PR MATCHED/BEATEN</span>'
                    if today_max >= pr_before_insert
                    else ""
                )

                st.markdown(
                    f'<div style="margin: 8px 0;">{pills}{pr_tag}</div>',
                    unsafe_allow_html=True,
                )

                m1, m2 = st.columns(2)
                with m1:
                    st.metric("RPE", workout.rpe if workout.rpe is not None else "—")
                with m2:
                    st.metric("Sessions analyzed", len(result["history"]))

                if workout.notes:
                    st.markdown(f"**Notes:** {workout.notes}")
            else:
                st.info("No structured workout could be extracted from that entry.")


# ============================================================
# HISTORY
# ============================================================

with history_tab:

    st.markdown('<p class="rw-label">Training history</p>', unsafe_allow_html=True)
    st.caption("Track how your performance changes across sessions.")

    all_exercises = fetch_exercises()

    if not all_exercises:
        st.info("No workout history yet — log a session in the **Log Workout** tab to get started.")

    else:
        selected_exercise = st.selectbox("Exercise", all_exercises)

        history = fetch_by_exercise(selected_exercise, limit=50)

        if not history:
            st.info("No history found for this exercise.")

        else:
            # ---------- Convert DB rows ----------

            chart_rows = []

            for row in reversed(history):
                timestamp = pd.to_datetime(row[5])
                sets = json.loads(row[2])
                rpe = row[3]

                total_volume = sum(s["weight"] * s["reps"] for s in sets)
                max_weight = max(s["weight"] for s in sets)
                total_reps = sum(s["reps"] for s in sets)

                chart_rows.append(
                    {
                        "Date": timestamp,
                        "Volume": total_volume,
                        "Max Weight": max_weight,
                        "Reps": total_reps,
                        "RPE": rpe,
                    }
                )

            df = pd.DataFrame(chart_rows)

            # ---------- Insight ----------

            insight = volume_insight(df)
            if insight:
                st.markdown(f'<div class="rw-insight">{insight}</div>', unsafe_allow_html=True)

            # ---------- Summary ----------

            latest = df.iloc[-1]
            previous = df.iloc[-2] if len(df) > 1 else None
            all_time_pr = df["Max Weight"].max()

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Latest Volume", f"{latest['Volume']:.0f} kg")
                if previous is not None:
                    st.markdown(delta_arrow(latest["Volume"], previous["Volume"]), unsafe_allow_html=True)

            with col2:
                st.metric("Max Weight", f"{latest['Max Weight']:.1f} kg")
                if latest["Max Weight"] >= all_time_pr:
                    st.markdown('<span class="rw-pr">🏆 ALL-TIME PR</span>', unsafe_allow_html=True)

            with col3:
                st.metric("Total Reps", f"{latest['Reps']:.0f}")
                if previous is not None:
                    st.markdown(delta_arrow(latest["Reps"], previous["Reps"]), unsafe_allow_html=True)

            st.markdown('<hr class="rw-divider">', unsafe_allow_html=True)

            # ---------- Volume chart ----------

            st.markdown('<p class="rw-label">Volume Over Time</p>', unsafe_allow_html=True)
            st.altair_chart(trend_chart(df, "Volume", "Volume (kg)", "#22d3ee"), use_container_width=True)

            # ---------- Max weight chart ----------

            st.markdown('<p class="rw-label">Max Weight Over Time</p>', unsafe_allow_html=True)
            st.altair_chart(trend_chart(df, "Max Weight", "Weight (kg)", "#a78bfa"), use_container_width=True)

            # ---------- RPE chart (only if any data present) ----------

            if df["RPE"].notna().any():
                st.markdown('<p class="rw-label">Perceived Effort (RPE) Over Time</p>', unsafe_allow_html=True)
                rpe_df = df.dropna(subset=["RPE"])
                st.altair_chart(trend_chart(rpe_df, "RPE", "RPE", "#fb923c", height=220), use_container_width=True)

            # ---------- Session history ----------

            st.markdown('<p class="rw-label">Recent Sessions</p>', unsafe_allow_html=True)

            display_df = df[["Date", "Volume", "Max Weight", "Reps", "RPE"]].copy()
            display_df["Date"] = display_df["Date"].dt.strftime("%b %d, %Y — %I:%M %p")
            display_df["RPE"] = display_df["RPE"].apply(lambda x: "—" if pd.isna(x) else int(x))
            display_df.columns = ["Date", "Volume (kg)", "Max Weight (kg)", "Total Reps", "RPE"]
            display_df = display_df.iloc[::-1]  # most recent first

            st.dataframe(display_df, use_container_width=True, hide_index=True)