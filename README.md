# AI Interview Practice Partner (Voice-Enabled)

A conversational agent built for the Eightfold.ai — AI Agent Building Assignment

📌 Project Overview

The AI Interview Practice Partner is a voice-enabled mock interview agent that conducts realistic job interviews tailored to specific roles. It asks adaptive questions, supports live speech interaction, and provides structured feedback with improvement insights at the end.

This project was developed as part of the Eightfold.ai – AI Agent Building Assignment, focusing on building a conversational agent that demonstrates:

✔ Natural, realistic dialogue

✔ Agentic decision-making (dynamic interviewing)

✔ Technical reasoning in design choices

✔ Voice-first interaction experience

🧠 Key Features

🎙 Voice-Enabled Interaction

  Questions can be spoken aloud using TTS (Text-to-Speech)

  Users can speak answers, automatically transcribed using speech-to-text

  Hybrid mode: type + speech both supported

👔 Role-Based Interviewing

  The interviewer adapts to roles such as:

    Software Engineer

    Data Analyst

    Sales Associate

    Product Manager

🧩 Adaptive Questioning

  The agent adjusts interview depth based on:

  Length of previous answers

  User confusion (short/unclear answers)

  Technical competence shown in responses

📊 Structured Post-Interview Feedback

  Includes:

    Overall performance summary

    Scored evaluation (Communication, Technical Depth, Structure, Confidence)

    Strengths and weaknesses

    Personalized practice recommendations

💬 Handles Multiple Persona Styles

  The interviewer adapts even if the user is:

    ❓ Confused (doesn’t know answers)

    🚀 Efficient (short, direct answers)

    🗣 Chatty (off-topic but talkative)

    🤖 Edge cases (invalid/unrelated responses)

🏗️ Architecture & Design Decisions

🔧 Core Components

Component	Responsibility
app.py	UI, voice control, display logic, state management
agent.py	Interactions with Gemini, conversation orchestration
prompts.py	Behavior and personality definition for interviewer and coach
.env	API key storage (not included in repo)

🎤 Speech & Audio Processing

Feature	Implementation

Text-to-Speech	Browser SpeechSynthesis API
Speech-to-Text	streamlit-mic-recorder + SpeechRecognition API
Hybrid Input	Typed + spoken answers

🤖 AI Model Strategy

Uses Google Gemini (generateContent)

Dynamic model picker ensures compatibility:

Prioritizes fastest real-time models for adaptive interviewing

Full interview history (Q/A, word count, response time) is sent for evaluation

📝 Design Principles

Natural Conversation First (not just question–answer scripts)

Agentic Behavior → interviewer decides difficulty and depth

Voice First → no-click interview possible

Feedback Intelligence → includes structure, STAR method hints, timing confidence signals

🚀 Getting Started

📌 Requirements

    pip install -r requirements.txt

🔒 Environment Setup (.env)

  Create a file named .env:

    GEMINI_API_KEY=your_api_key_here

▶️ Run the Application

    streamlit run app.py


Use Google Chrome / Edge for microphone compatibility.

🧪 Persona Testing Scenarios

Persona	How the agent responds

❓ Confused user	Asks simpler follow-ups, offers clarification
🚀 Efficient user	Asks deeper, more challenging questions
🗣 Chatty user	Gently redirects to job-relevant responses
🤯 Edge case user	Handles invalid inputs, keeps professional tone
📌 Demo Guidelines (for reviewers)

The agent demo should include:

Starting a new session by selecting a role

Speaking answers + showing live transcription

A sample of skipped questions

Final feedback screen showing:

Scores

Strengths & Weaknesses

Practice Plan

🛠️ Future Enhancements

🔮 Potential improvements include:

Resume upload → interviewer asks resume-specific questions

Long-term user skill analytics + progress dashboard

Multi-language support for global job seekers

More behavioral context (leadership, communication styles)

👨‍💻 Author

Your Name Here
📧 [Add email/contact if required]
🔗 GitHub Repo: Add your link here

🌟 Final Note

This project highlights natural conversation quality, adaptive agent behavior, thoughtful design, and a voice-first user experience — aligning directly with Eightfold.ai’s goals for the assignment.
