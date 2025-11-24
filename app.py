import time
import json
import streamlit as st
import streamlit.components.v1 as components
from streamlit_mic_recorder import speech_to_text

from agent import get_next_question, generate_feedback

st.set_page_config(page_title="Interview Practice Partner", page_icon="🎤", layout="wide")

# ---------- Global minimal styling ----------
st.markdown(
    """
    <style>
    .main > div {
        padding-top: 1.5rem;
    }

    /* Header / context card */
    .result-card {
        border-radius: 12px;
        padding: 1rem 1.25rem;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
        color: #0f172a;
    }
    .result-card * {
        color: #0f172a !important;  /* dark text on light background */
    }

    /* Small chips for role / type / questions */
    .chip {
        display: inline-block;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        background-color: #e2e8f0;
        font-size: 0.75rem;
        margin-right: 0.25rem;
        margin-bottom: 0.25rem;
        color: #0f172a;
    }

    /* Score rows */
    .score-pill {
        border-radius: 10px;
        padding: 0.75rem 0.9rem;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        margin-bottom: 0.75rem;
        color: #0f172a;
    }
    .score-pill * {
        color: #0f172a !important;  /* force dark text inside score card */
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# REPLACE your existing tts_button function with this:
def tts_button(text, label="🔊 Read question aloud"):
    if not text:
        return

    # 1. Clean up text (replace newlines with spaces to avoid JS errors)
    # 2. json.dumps ensures quotes are escaped properly
    safe_text = json.dumps(text.replace("\n", " ").strip())

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <body>
        <button id="speakBtn" style="
            padding: 0.4rem 0.9rem;
            border-radius: 0.75rem;
            border: 1px solid #cbd5f5;
            background: #eef2ff;
            cursor: pointer;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            font-family: sans-serif;
            color: #333;
        ">
            {label}
        </button>

        <script>
            const btn = document.getElementById("speakBtn");
            
            btn.onclick = function() {{
                // 1. Stop any currently playing audio (CRITICAL FIX)
                window.speechSynthesis.cancel();

                // 2. Create the utterance
                const msg = new SpeechSynthesisUtterance({safe_text});
                
                // Optional: Set language to US English explicitly
                msg.lang = 'en-US';
                msg.rate = 1.0; // Speed: 0.1 to 10
                msg.pitch = 1.0; // Pitch: 0 to 2

                // 3. Error handling
                msg.onerror = function(event) {{
                    console.error("TTS Error:", event);
                }};

                // 4. Speak
                window.speechSynthesis.speak(msg);
                console.log("Speaking:", {safe_text});
            }};
        </script>
    </body>
    </html>
    """

    # Increase height slightly to ensure button isn't cut off
    components.html(html_code, height=70)

# ---------- Voice input widget using browser SpeechRecognition ----------
def voice_input_widget():
    """
    Adds a button that uses the browser's SpeechRecognition API to
    transcribe the user's speech and fill the latest Streamlit textarea.

    Works best in Chrome / Edge.
    """
    components.html(
        """
        <div>
          <button id="voice-btn" style="
              padding: 0.4rem 0.9rem;
              border-radius: 0.75rem;
              border: 1px solid #a7f3d0;
              background: #dcfce7;
              cursor: pointer;
              margin-top: 0.25rem;
              font-size: 0.9rem;
          ">
            🎙 Speak your answer
          </button>
          <span id="voice-status" style="margin-left: 0.5rem; font-size: 0.85rem; color: #444;"></span>
        </div>

        <script>
            (function() {
                const btn = document.getElementById('voice-btn');
                const statusSpan = document.getElementById('voice-status');

                if (!btn) return;

                btn.onclick = async function() {
                    statusSpan.textContent = '';

                    // Request permission explicitly (sometimes hidden in iframes)
                    try {
                        await navigator.mediaDevices.getUserMedia({ audio: true });
                    } catch (e) {
                        statusSpan.textContent = " Microphone blocked. Allow mic and retry.";
                        return;
                    }

                    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                    if (!SpeechRecognition) {
                        statusSpan.textContent = ' Speech recognition not supported in this browser.';
                        return;
                    }

                    const recognition = new SpeechRecognition();
                    recognition.lang = 'en-US';
                    recognition.continuous = false;
                    recognition.interimResults = false;
                    recognition.maxAlternatives = 1;

                    recognition.onstart = function() {
                        statusSpan.textContent = ' 🎤 Listening...';
                    };

                    recognition.onerror = function(event) {
                        statusSpan.textContent = '❌ Error: ' + event.error;
                    };

                    recognition.onend = function() {
                        if (!statusSpan.textContent.startsWith('❌')) {
                            statusSpan.textContent = ' ⏹️ Stopped';
                        }
                    };

                    recognition.onresult = function(event) {
                        const transcript = event.results[0][0].transcript;
                        try {
                            const textareas = window.parent.document.querySelectorAll('textarea[data-baseweb="textarea"]');
                            const textarea = textareas[textareas.length - 1];
                            if (textarea) {
                                textarea.value = transcript;
                                textarea.dispatchEvent(new Event('input', { bubbles: true }));
                                statusSpan.textContent = ' ✔️ Transcribed';
                            }
                        } catch (e) {
                            statusSpan.textContent = ' Could not access parent document.';
                        }
                    };

                    recognition.start();
                };
            })();
        </script>
        """,
        height=80,
    )


# ---------- Initialize session state ----------
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.role = "Software Engineer"
    st.session_state.interview_type = "Mixed"
    st.session_state.history = []            # list of dicts with Q/A and stats
    st.session_state.current_question = ""
    st.session_state.question_number = 0
    st.session_state.max_questions = 5
    st.session_state.status = "not_started"  # "not_started" | "in_progress" | "finished"
    st.session_state.feedback = None
    st.session_state.question_start_time = None


# ---------- Sidebar (settings) ----------
with st.sidebar:
    st.title("⚙️ Session Setup")

    st.session_state.role = st.selectbox(
        "Role",
        ["Software Engineer", "Data Analyst", "Sales Associate", "Product Manager"],
        index=0,
    )

    st.session_state.interview_type = st.selectbox(
        "Interview Type",
        ["Technical", "Behavioral", "Mixed"],
        index=2,
    )

    st.session_state.max_questions = st.slider(
        "Number of Questions",
        min_value=3,
        max_value=10,
        value=5,
    )

    st.markdown("---")
    if st.button("🔄 Restart Interview", use_container_width=True):
        st.session_state.history = []
        st.session_state.current_question = ""
        st.session_state.question_number = 0
        st.session_state.status = "not_started"
        st.session_state.feedback = None
        st.session_state.question_start_time = None
        st.success("Interview reset.")


# ---------- Main Page ----------
st.title("🎤 AI Interview Practice Partner (Voice-Enabled)")

st.write(
    "This agent conducts **role-based mock interviews**, speaks the questions aloud, "
    "and lets you **answer using your voice** (transcribed into the answer box). "
    "At the end, you receive a structured evaluation of your performance."
)

# Compact header chips (context)
st.markdown(
    f"""
    <div class="result-card">
        <span class="chip">Role: {st.session_state.role}</span>
        <span class="chip">Type: {st.session_state.interview_type}</span>
        <span class="chip">Questions: {st.session_state.max_questions}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----- Not started -----
if st.session_state.status == "not_started":
    st.info("Click **Start Interview** to begin.")
    if st.button("🚀 Start Interview", type="primary"):
        st.session_state.status = "in_progress"
        st.session_state.current_question = get_next_question(
            st.session_state.role,
            st.session_state.interview_type,
            st.session_state.history,
            st.session_state.question_number,
            st.session_state.max_questions,
        )
        st.session_state.question_number += 1
        st.session_state.question_start_time = time.time()

# ----- In progress -----
if st.session_state.status == "in_progress":
    left, right = st.columns([2, 1])

    with left:
        st.subheader(f"Question {st.session_state.question_number}")
        st.write(st.session_state.current_question)
        tts_button(st.session_state.current_question)   # voice output

        # --- NEW VOICE LOGIC START ---
        
        # 1. Define a unique key for the text area based on the question number
        answer_key = f"answer_{st.session_state.question_number}"

        # 2. Initialize the session state for this answer if not present
        if answer_key not in st.session_state:
            st.session_state[answer_key] = ""

        # 3. Voice Input Button (streamlit-mic-recorder)
        st.write("🎙️ Record your answer:")
        voice_text = speech_to_text(
            language='en',
            start_prompt="Click to Speak",
            stop_prompt="Stop Recording",
            just_once=True,
            key=f"voice_btn_{st.session_state.question_number}"
        )

        # 4. If voice text was received, update the text area's session state and rerun
        if voice_text:
            st.session_state[answer_key] = voice_text
            st.rerun()

        # 5. The Text Area (Linked to the same key)
        answer = st.text_area(
            "Your answer (you can speak above or type here):",
            key=answer_key,
            height=160,
        )
        # --- NEW VOICE LOGIC END ---

        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Submit Answer", use_container_width=True):
                # Using the variable 'answer' which comes from the text_area above
                if not answer.strip():
                    st.warning("Please enter or speak an answer before submitting.")
                else:
                    # Compute timing + word count
                    response_time = None
                    if st.session_state.question_start_time is not None:
                        response_time = time.time() - st.session_state.question_start_time

                    clean_answer = answer.strip()
                    st.session_state.history.append(
                        {
                            "question": st.session_state.current_question,
                            "answer": clean_answer,
                            "answer_word_count": len(clean_answer.split()),
                            "response_time_sec": response_time,
                        }
                    )

                    # Check if interview finished
                    if st.session_state.question_number >= st.session_state.max_questions:
                        st.session_state.status = "finished"
                        st.session_state.current_question = ""
                        st.session_state.question_start_time = None
                        st.rerun()
                    else:
                        # Get next question
                        st.session_state.current_question = get_next_question(
                            st.session_state.role,
                            st.session_state.interview_type,
                            st.session_state.history,
                            st.session_state.question_number,
                            st.session_state.max_questions,
                        )
                        st.session_state.question_number += 1
                        st.session_state.question_start_time = time.time()
                        st.rerun()

        with c2:
            if st.button("⏭️ Skip Question", use_container_width=True):
                if st.session_state.question_number >= st.session_state.max_questions:
                    st.session_state.status = "finished"
                    st.session_state.current_question = ""
                    st.session_state.question_start_time = None
                    st.rerun()
                else:
                    st.session_state.current_question = get_next_question(
                        st.session_state.role,
                        st.session_state.interview_type,
                        st.session_state.history,
                        st.session_state.question_number,
                        st.session_state.max_questions,
                    )
                    st.session_state.question_number += 1
                    st.session_state.question_start_time = time.time()
                    st.rerun()

    with right:
        st.markdown("#### Live Interview Log")
        if st.session_state.history:
            for idx, item in enumerate(st.session_state.history, start=1):
                with st.expander(f"Q{idx}: {item['question'][:60]}..."):
                    st.markdown(f"**Your answer:** {item['answer']}")
                    st.caption(
                        f"Words: {item.get('answer_word_count')}, "
                        f"Time: {round(item.get('response_time_sec') or 0, 1)} sec"
                    )
        else:
            st.caption("Your answers will appear here as you progress.")

# ----- Finished -----
if st.session_state.status == "finished":
    st.subheader("✅ Interview Complete")

    if not st.session_state.feedback:
        if st.button("🧠 Generate Feedback", type="primary"):
            with st.spinner("Analyzing your responses..."):
                st.session_state.feedback = generate_feedback(
                    st.session_state.role,
                    st.session_state.interview_type,
                    st.session_state.history,
                )
            st.success("Feedback generated!")

    fb = st.session_state.feedback

    if fb:
        # Try to recover structured JSON even if it came back as raw_text
        if "raw_text" in fb:
            raw = fb["raw_text"]
            parsed = None
            try:
                # try direct parse
                parsed = json.loads(raw)
            except Exception:
                try:
                    # try to extract the JSON object from surrounding text
                    start = raw.find("{")
                    end = raw.rfind("}")
                    if start != -1 and end != -1:
                        parsed = json.loads(raw[start : end + 1])
                except Exception:
                    parsed = None

            if parsed:
                fb = parsed   # from now on treat as normal structured response
            else:
                # last-resort fallback: show as plain text
                st.markdown("### 📋 Feedback")
                st.write(raw)
                st.stop()  # don't run the pretty UI below

        # --------- from here on, fb is expected to be structured JSON ----------
        overall_summary = fb.get("overall_summary", "")
        scores = fb.get("scores", {})
        strengths = fb.get("strengths", [])
        gaps = fb.get("areas_to_improve", [])
        tasks = fb.get("next_practice_tasks", [])

        # Header card
        st.markdown(
            f"""
            <div class="result-card">
                <h4 style="margin-bottom: 0.3rem;">Session Summary</h4>
                <p style="margin-top: 0.2rem; margin-bottom: 0.4rem; font-size: 0.9rem; color: #475569;">
                    Role: <b>{st.session_state.role}</b> · 
                    Type: <b>{st.session_state.interview_type}</b> ·
                    Questions: <b>{len(st.session_state.history)}</b>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_overview, tab_scores, tab_strengths, tab_practice = st.tabs(
            ["Overview", "Scores", "Strengths & Gaps", "Practice Plan"]
        )

        # ---- Overview tab ----
        with tab_overview:
            st.markdown("#### Overall Summary")
            st.write(overall_summary or "Summary not available.")

            if scores:
                st.markdown("#### Snapshot")
                c1, c2, c3, c4 = st.columns(4)
                for col, key in zip(
                    [c1, c2, c3, c4],
                    ["communication", "technical_depth", "structure", "confidence"],
                ):
                    if key in scores:
                        with col:
                            try:
                                v = float(scores[key])
                            except Exception:
                                v = 0
                            st.metric(key.replace("_", " ").title(), f"{v}/10")

        # ---- Scores tab ----
        with tab_scores:
            st.markdown("#### Detailed Scores")
            if not scores:
                st.info("Scores not available.")
            else:
                for key, label in [
                    ("communication", "Communication"),
                    ("technical_depth", "Technical Depth"),
                    ("structure", "Structure"),
                    ("confidence", "Confidence"),
                ]:
                    if key in scores:
                        try:
                            val = float(scores[key])
                        except Exception:
                            val = 0.0

                        st.markdown(
                            f"""
                            <div class="score-pill">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.25rem;">
                                    <span><b>{label}</b></span>
                                    <span>{val}/10</span>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        st.progress(min(max(val, 0.0), 10.0) / 10.0)

        # ---- Strengths & Gaps tab ----
        with tab_strengths:
            col_s, col_g = st.columns(2)
            with col_s:
                st.markdown("#### 💪 Strengths")
                if strengths:
                    for s in strengths:
                        st.write(f"- {s}")
                else:
                    st.caption("No strengths identified.")
            with col_g:
                st.markdown("#### 🛠 Areas to Improve")
                if gaps:
                    for g in gaps:
                        st.write(f"- {g}")
                else:
                    st.caption("No areas to improve identified.")

        # ---- Practice Plan tab ----
        with tab_practice:
            st.markdown("#### 🎯 Suggested Practice Tasks")
            if tasks:
                for t in tasks:
                    st.write(f"- {t}")
            else:
                st.caption("No specific practice tasks generated.")
