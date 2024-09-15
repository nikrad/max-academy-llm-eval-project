import json
import openai
from langsmith import traceable
from langsmith.evaluation import evaluate
from langsmith.schemas import Run, Example
from langsmith.wrappers import wrap_openai

client = wrap_openai(openai.OpenAI())

RATING_SCALE_LENGTH = 10


@traceable
def prompt_compliance_evaluator(run: Run, example: Example) -> dict:
    inputs = example.inputs["input"]
    outputs = example.outputs["output"]
    # Extract system prompt
    system_prompt = next(
        (msg["data"]["content"] for msg in inputs if msg["type"] == "system"), ""
    )

    # Extract message history
    message_history = []
    for msg in inputs:
        if msg["type"] in ["human", "ai"]:
            message_history.append(
                {
                    "role": "user" if msg["type"] == "human" else "assistant",
                    "content": msg["data"]["content"],
                }
            )

    # Extract latest user message and model output
    latest_message = message_history[-1]["content"] if message_history else ""
    model_output = outputs["data"]["content"]

    evaluation_prompt = f"""
    System Prompt: {system_prompt}

    Message History:
    {json.dumps(message_history, indent=2)}

    Latest User Message: {latest_message}

    Model Output: {model_output}

    Based on the above information, evaluate the model's output for compliance with the system prompt and context of the conversation. 

    Use the following two key metrics to evaluate the quality of the response:
    1. Informativeness. This metric measures how well the summary captures the most important and relevant points from the original document. An ideal summary should retain the key information while omitting redundant or less important details. This can be evaluated through rating a summary based on its coverage of essential points.
    2. Adherence to User Specifications. This metric measures how well the summary aligns with specific preferences set by the user, such as desired length, structure, or format. How well did the generated summary meets the user’s specified length requirements? Does the summary conform to the user's requested format (sentences versus bullet points) and stylistic preferences (e.g. tone)?
    
    Provide a score on a scale of 1 to {RATING_SCALE_LENGTH}, where 1 is completely non-compliant and {RATING_SCALE_LENGTH} is perfectly compliant.
    Also provide a brief explanation for your score.

    Respond in the following JSON format:
    {{
        "score": <int>,
        "explanation": "<string>"
    }}
    """

    response = client.chat.completions.create(
        model="chatgpt-4o-latest",
        messages=[
            {
                "role": "system",
                "content": "You are an AI assistant tasked with evaluating the compliance of model outputs to given prompts and conversation context.",
            },
            {"role": "user", "content": evaluation_prompt},
        ],
        temperature=0.2,
    )

    try:
        result = json.loads(response.choices[0].message.content)
        return {
            "key": "prompt_compliance",
            "score": result["score"] / RATING_SCALE_LENGTH,  # Normalize to 0-1 range
            "reason": result["explanation"],
        }
    except json.JSONDecodeError:
        return {
            "key": "prompt_compliance",
            "score": 0,
            "reason": "Failed to parse evaluator response",
        }


# Name of the LangSmith dataset to evaluate
dataset_name = "Week-1-Project"

# String prefix for the experiment name
experiment_prefix = "Document summarizer prompt compliance"

# List of evaluators to score the outputs of target task
evaluators = [
    prompt_compliance_evaluator,
]

experiment_results = evaluate(
    lambda inputs: inputs,
    data=dataset_name,
    evaluators=evaluators,
    experiment_prefix=experiment_prefix,
)
