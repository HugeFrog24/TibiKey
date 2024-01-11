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
        gpt_models = [model.id for model in models.data if model.id.startswith('gpt-')]
        return gpt_models
    except openai.APIConnectionError as e:  # Catch connection-related errors
        logger.error(f"API connection error occurred: {e}")
        return []
    except openai.APIError as e:  # Catch API-related errors
        logger.error(f"API error occurred: {e}")
        return []
    except openai.OpenAIError as e:  # Catch all other OpenAI errors
        logger.error(f"OpenAI error occurred: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return []
    
def get_openai_response(client, prompt, text, max_tokens, model):
    try:
        formatted_text = f"{prompt}\n\n{text}"
        response = client.chat.completions.create(
          model=model,
          messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": formatted_text}
            ],
          max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except openai.APIConnectionError as api_conn_err:  # Catch connection-related errors
        logger.error(f"API connection error occurred: {api_conn_err}")
        return ""
    except openai.APIError as api_err:  # Catch API-related errors
        logger.error(f"API error occurred: {api_err}")
        if hasattr(api_err, 'http_body'):
            logger.error(f"Response content: {api_err.http_body}")
        return ""
    except openai.OpenAIError as openai_err:  # Catch all other OpenAI errors
        logger.error(f"OpenAI error occurred: {openai_err}")
        return ""
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return ""
    
def validate_model(model, client):
    gpt_models = get_openai_models(client)
    if model not in gpt_models:
        raise ValueError(f"The model {model} is not a valid GPT model.")
    
def validate_max_tokens(max_tokens, allowed_tokens_range):
    if not isinstance(max_tokens, int) or not allowed_tokens_range[0] <= max_tokens <= allowed_tokens_range[1]:
        raise ValueError(f"max_tokens must be between {allowed_tokens_range[0]} and {allowed_tokens_range[1]}.")
