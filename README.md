# Health Agent

The Health Agent is a personalized health and wellness assistant that helps you achieve your health goals. It can generate customized meal and workout plans based on your preferences and goals, and it can also track your progress over time.

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- `uv` package installer (`pip install uv`)

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/health-agent.git
   cd health-agent
   ```

2. **Create a virtual environment and install dependencies:**

   ```bash
   uv venv
   uv pip install -r requirements.txt
   ```

3. **Set up your environment variables:**

   Create a `.env` file in the root of the project and add your Gemini API key:

   ```
   GEMINI_API_KEY=your-gemini-api-key
   ```

### Running the Agent

To run the agent, use the following command:

```bash
chainlit run main.py -w
```

This will start the Chainlit server, and you can interact with the agent in your web browser.

## 🤖 Agent Architecture

The Health Agent is built using the `agents` library and Chainlit for the user interface. It follows a tool-based architecture, where different tools are responsible for specific tasks.

The main components of the agent are:

-   **`main.py`**: The entry point of the application. It initializes the Chainlit server and handles user interactions.
-   **`agent.py`**: The core of the agent. It initializes the tools and the Gemini model, and it orchestrates the conversation with the user.
-   **`tools/`**: This directory contains the tools that the agent uses to perform specific tasks, such as generating meal plans, recommending workouts, and tracking progress.
-   **`agent_s/`**: This directory contains specialized agents that can be used for more complex tasks, such as providing support for injuries or escalating issues to a human expert.
-   **`guardrails.py`**: This file contains the guardrails that are used to validate the user's input and ensure that the agent behaves as expected.
-   **`context.py`**: This file defines the `UserSessionContext` class, which is used to store information about the user's session.

## 🛠️ Tools

The Health Agent uses the following tools:

-   **`GoalAnalyzerTool`**: Parses the user's health goals from natural language.
-   **`MealPlannerTool`**: Generates a 7-day meal plan based on the user's diet preferences and goals.
-   **`WorkoutRecommenderTool`**: Recommends a workout plan based on the user's fitness level and goals.
-   **`CheckinSchedulerTool`**: Schedules check-ins with the user to track their progress.
-   **`ProgressTrackerTool`**: Tracks the user's progress over time.

## 👨‍⚕️ Specialized Agents

The Health Agent can also hand off to the following specialized agents:

-   **`NutritionExpertAgent`**: Provides expert advice on nutrition.
-   **`InjurySupportAgent`**: Provides support and guidance for injuries.
-   **`EscalationAgent`**: Escalates complex issues to a human expert.
