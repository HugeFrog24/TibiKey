import logging

import openai

# Configure the logging for utils.py
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(name)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def get_openai_models(client):
    try:
        models = client.models.list()
        # Filter out only models that begin with 'gpt-'
        gpt_models = [
            model.id for model in models.data if model.id.startswith('gpt-')]
        return gpt_models
    except openai.APIConnectionError as e:  # Catch connection-related errors
        logger.error(f"API connection error occurred: {e}")
        return []
    except openai.APIError as e:  # Catch API-related errors
        logger.error(f"API error occurred: {e}")
        if isinstance(
                e,
                openai.AuthenticationError) and "invalid_api_key" in str(e):
            raise openai.AuthenticationError(
                "Incorrect API key provided", response=e.response, body=e.body)
        return []
    except openai.OpenAIError as e:  # Catch all other OpenAI errors
        logger.error(f"OpenAI error occurred: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return []


def get_openai_stream_response(client, messages, max_tokens, model):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content:  # Corrected attribute access
                # Yield each chunk content
                yield chunk.choices[0].delta.content
    except Exception as e:
        logger.error(f"An error occurred during OpenAI API call: {e}")
        raise


def get_openai_non_stream_response(client, messages, max_tokens, model):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            stream=False
        )
        # Correctly access the 'content' attribute using dot notation
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"An error occurred during OpenAI API call: {e}")
        raise


def validate_model(model, client):
    gpt_models = get_openai_models(client)
    if model not in gpt_models:
        raise ValueError(f"The model {model} is not a valid GPT model.")


def validate_max_tokens(max_tokens, allowed_tokens_range):
    if not isinstance(
            max_tokens,
            int) or not allowed_tokens_range[0] <= max_tokens <= allowed_tokens_range[1]:
        raise ValueError(
            f"max_tokens must be between {
                allowed_tokens_range[0]} and {
                allowed_tokens_range[1]}.")
