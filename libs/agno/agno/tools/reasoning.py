from textwrap import dedent
from typing import Optional

from agno.agent import Agent
from agno.reasoning.step import NextAction, ReasoningStep, ReasoningSteps
from agno.run.response import RunEvent
from agno.tools import Toolkit
from agno.utils.log import log_debug, logger


class ReasoningTools(Toolkit):
    def __init__(
        self,
        reason: bool = True,
        analyze: bool = True,
        finalize: bool = True,
        instructions: Optional[str] = None,
        add_instructions: bool = True,
        **kwargs,
    ):
        super().__init__(
            name="reasoning_tools",
            instructions=instructions,
            add_instructions=add_instructions,
            **kwargs,
        )

        if instructions is None:
            self.instructions = dedent("""\
            ## Using Reasoning Tools
            Use these tools to work through problems step-by-step:
            
            1. `reason` - Work through complex problems step-by-step, tracking your thought process
            2. `analyze` - Analyze intermediate results and determine next steps
            3. `finalize` - Provide a final answer after thorough reasoning
            
            ## Guidelines
            - Break down complex problems into smaller steps
            - Explicitly state your assumptions and reasoning
            - Use the reason tool multiple times to build on previous steps
            - Analyze intermediate results before proceeding
            - End with a finalize step to summarize your conclusion\
            """)

        # Register tools based on parameters
        if reason:
            self.register(self.reason)
        if analyze:
            self.register(self.analyze)
        if finalize:
            self.register(self.finalize)

    def reason(
        self, agent: Agent, step_title: str, reasoning: str, action: Optional[str] = None, confidence: float = 0.8
    ) -> str:
        """Start a reasoning step to work through a problem methodically.
        This tool helps break down complex problems into logical steps and track the reasoning process.

        Args:
            step_title: A concise title for this reasoning step
            reasoning: Your detailed reasoning for this step
            action: What you'll do based on this reasoning
            confidence: How confident you are about this step (0.0 to 1.0)

        Returns:
            A summary of the reasoning step
        """
        try:
            log_debug(f"Reasoning step: {step_title}")

            # Create a reasoning step
            reasoning_step = ReasoningStep(
                title=step_title,
                reasoning=reasoning,
                action=action,
                next_action=NextAction.CONTINUE,
                confidence=confidence,
            )

            # Add the step to the Agent's session state
            if agent.session_state is None:
                agent.session_state = {}

            if "reasoning_steps" not in agent.session_state:
                agent.session_state["reasoning_steps"] = []

            agent.session_state["reasoning_steps"].append(reasoning_step)

            # Add the step to the run response if we can
            if hasattr(agent, "run_response") and agent.run_response is not None:
                if agent.run_response.extra_data is None:
                    from agno.run.response import RunResponseExtraData

                    agent.run_response.extra_data = RunResponseExtraData()

                if agent.run_response.extra_data.reasoning_steps is None:
                    agent.run_response.extra_data.reasoning_steps = []

                agent.run_response.extra_data.reasoning_steps.append(reasoning_step)

                # Yield a reasoning step event if streaming
                if agent.stream_intermediate_steps and hasattr(agent, "create_run_response"):
                    agent.create_run_response(
                        content=reasoning_step,
                        content_type=reasoning_step.__class__.__name__,
                        event=RunEvent.reasoning_step,
                    )

            # Return a summary of the reasoning step
            return f"Step: {step_title}\n\nReasoning: {reasoning}\n\nAction: {action or 'Continue reasoning'}"

        except Exception as e:
            logger.error(f"Error recording reasoning step: {e}")
            return f"Error recording reasoning step: {e}"

    def analyze(
        self,
        agent: Agent,
        step_title: str,
        result: str,
        reasoning: str,
        next_action: str = "continue",
        confidence: float = 0.8,
    ) -> str:
        """Analyze results from a reasoning step and determine next actions.

        Args:
            step_title: A concise title for this analysis step
            result: The outcome of the previous action
            reasoning: Your analysis of the results
            next_action: What to do next ("continue", "validate", or "final_answer")
            confidence: How confident you are in this analysis (0.0 to 1.0)

        Returns:
            A summary of the analysis
        """
        try:
            log_debug(f"Analysis step: {step_title}")

            # Map string next_action to enum
            next_action_enum = NextAction.CONTINUE
            if next_action.lower() == "validate":
                next_action_enum = NextAction.VALIDATE
            elif next_action.lower() in ["final", "final_answer", "finalize"]:
                next_action_enum = NextAction.FINAL_ANSWER

            # Create a reasoning step for the analysis
            reasoning_step = ReasoningStep(
                title=step_title,
                result=result,
                reasoning=reasoning,
                next_action=next_action_enum,
                confidence=confidence,
            )

            # Add the step to the Agent's session state
            if agent.session_state is None:
                agent.session_state = {}

            if "reasoning_steps" not in agent.session_state:
                agent.session_state["reasoning_steps"] = []

            agent.session_state["reasoning_steps"].append(reasoning_step)

            # Add the step to the run response if we can
            if hasattr(agent, "run_response") and agent.run_response is not None:
                if agent.run_response.extra_data is None:
                    from agno.run.response import RunResponseExtraData

                    agent.run_response.extra_data = RunResponseExtraData()

                if agent.run_response.extra_data.reasoning_steps is None:
                    agent.run_response.extra_data.reasoning_steps = []

                agent.run_response.extra_data.reasoning_steps.append(reasoning_step)

                # Yield a reasoning step event if streaming
                if agent.stream_intermediate_steps and hasattr(agent, "create_run_response"):
                    agent.create_run_response(
                        content=reasoning_step,
                        content_type=reasoning_step.__class__.__name__,
                        event=RunEvent.reasoning_step,
                    )

            # Return a summary of the analysis
            return f"Analysis: {step_title}\n\nResult: {result}\n\nReasoning: {reasoning}\n\nNext action: {next_action}"

        except Exception as e:
            logger.error(f"Error recording analysis step: {e}")
            return f"Error recording analysis step: {e}"

    def finalize(self, agent: Agent, final_answer: str, summary: str) -> str:
        """Finalize your reasoning and provide a conclusive answer.

        Args:
            final_answer: The conclusive answer to the original question
            summary: A summary of the reasoning process that led to this answer

        Returns:
            The final answer with reasoning summary
        """
        try:
            log_debug(f"Finalizing reasoning: {final_answer}")

            # Create a final reasoning step
            final_step = ReasoningStep(
                title="Final Answer",
                result=final_answer,
                reasoning=summary,
                next_action=NextAction.FINAL_ANSWER,
                confidence=1.0,
            )

            # Add the step to the Agent's session state
            if agent.session_state is None:
                agent.session_state = {}

            if "reasoning_steps" not in agent.session_state:
                agent.session_state["reasoning_steps"] = []

            agent.session_state["reasoning_steps"].append(final_step)

            # Get all reasoning steps
            all_steps = agent.session_state["reasoning_steps"]

            # Add the reasoning steps to the run response
            if hasattr(agent, "run_response") and agent.run_response is not None:
                if agent.run_response.extra_data is None:
                    from agno.run.response import RunResponseExtraData

                    agent.run_response.extra_data = RunResponseExtraData()

                if agent.run_response.extra_data.reasoning_steps is None:
                    agent.run_response.extra_data.reasoning_steps = []

                agent.run_response.extra_data.reasoning_steps.append(final_step)

                # Collect reasoning content for the message
                reasoning_content = "\n\n".join(
                    [
                        f"Step: {step.title}\n"
                        f"Reasoning: {step.reasoning}\n"
                        f"{'Action: ' + step.action if step.action else ''}"
                        f"{'Result: ' + step.result if step.result else ''}"
                        for step in all_steps
                    ]
                )

                # Add reasoning content to the most recent assistant message
                if hasattr(agent, "memory") and agent.memory is not None:
                    messages = agent.memory.get_messages()
                    for msg in reversed(messages):
                        if hasattr(msg, "role") and msg.role == "assistant" and hasattr(msg, "reasoning_content") and msg.reasoning_content is None:
                            msg.reasoning_content = reasoning_content
                            break

                # Yield a reasoning completed event if streaming
                if agent.stream_intermediate_steps and hasattr(agent, "create_run_response"):
                    agent.create_run_response(
                        content=ReasoningSteps(reasoning_steps=all_steps),
                        content_type=ReasoningSteps.__class__.__name__,
                        event=RunEvent.reasoning_completed,
                    )

            # Return the final answer with summary
            return f"Final Answer: {final_answer}\n\nReasoning Summary: {summary}"

        except Exception as e:
            logger.error(f"Error finalizing reasoning: {e}")
            return f"Error finalizing reasoning: {e}"
