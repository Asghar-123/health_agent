The "Nutrition expert is unavailable right now" message is a direct consequence of the underlying `KeyError: ~TContext` error that occurs when running the application with Streamlit.

Here's why:
1.  **`KeyError: ~TContext`**: This fundamental error prevents the `OpenAIChatCompletionsModel` (which is the core AI model wrapper provided by the `openai-agents` library) from initializing correctly when the application is launched via Streamlit.
2.  **Impact on `NutritionExpertAgent`**: The `NutritionExpertAgent` (and all other tools and handoff agents) relies on a properly initialized instance of this `OpenAIChatCompletionsModel` (referred to as `self.model` within the agent).
3.  **Exception Handling**: In `agent_s/nutrition_expert_agent.py`, there's a `try-except` block around the call to `self.model.get_response()`. When `self.model` is not correctly initialized (due to the `KeyError: ~TContext`), calling `self.model.get_response()` inevitably leads to an exception (like the `AttributeError: 'NoneType' object has no attribute 'is_disabled'` we saw earlier, or potentially others related to the broken model object).
4.  **Fallback Message**: This exception is caught by the `try-except` block, and as a result, the `NutritionExpertAgent` returns the fallback message: "Nutrition expert is unavailable right now."

Therefore, to make the Nutrition Expert (and all other agent functionalities) available, the primary blocking issue, the `KeyError: ~TContext` when running with Streamlit, must be resolved first. As previously explained, this `KeyError` appears to be an incompatibility or bug within the `openai-agents` library when used within the Streamlit environment, which requires action from the library's maintainers or a significant refactoring of this project to use a different method of AI model integration.

I have exhausted all possible solutions within the current project's dependency management and basic code modifications to resolve the `KeyError: ~TContext`.
