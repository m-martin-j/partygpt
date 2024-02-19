
import logging
from typing import Tuple

from openai import OpenAI


logger = logging.getLogger(__name__)


class OpenaiChat:
    def __init__(
            self,
            organisation,
            api_key) -> None:
        self._total_tokens = {'completion_tokens': 0, 'prompt_tokens': 0, 'sum': 0}

        self._authenticate(organisation=organisation,
                           api_key=api_key)

    def _authenticate(self, organisation, api_key):
        self.client = OpenAI(
            api_key=api_key,
            organization=organisation)

    def get_model_list(self):
        model_list = self.client.models.list().data
        return model_list

    def check_model_availability(self, model_name):
        model_list = self.get_model_list()
        available_models = [m.id for m in model_list]
        return model_name in available_models

    def _update_total_tokens(self, usage_addendum):
        try:
            completion_t = usage_addendum.completion_tokens
            prompt_t = usage_addendum.prompt_tokens
        except KeyError:
            logger.error(
                f'Provided usage_addendum does not contain expected fields: {usage_addendum}')

        if not (isinstance(completion_t, (int, float)) and
                isinstance(prompt_t, (int, float))):
            logger.error('Cannot update total token sum with input types '
                         f'completion_t: {type(completion_t)} and prompt_t: {type(prompt_t)}')
        else:
            sum_t = completion_t + prompt_t
            self._total_tokens['completion_tokens'] += completion_t
            self._total_tokens['prompt_tokens'] += prompt_t
            self._total_tokens['sum'] += sum_t

    def get_total_tokens(self):
        return self._total_tokens

    def assemble_request_messages(
            self,
            system_content,
            user_prompt) -> list:
        # TODO: make this method more useful
        res = []
        res.append({'role': 'system', 'content': system_content})
        res.append({'role': 'user', 'content': user_prompt})
        return res

    def request_completion(
            self,
            messages: list,
            model: str,
            max_tokens: int,
            temperature: float = 1.0,
            top_p: float = 1.0,
            tools: list = None) -> Tuple[str, dict]:
        """Requests completion by a transformer model.
        https://platform.openai.com/docs/api-reference/chat/create

        Args:
            messages (list): The messages. It's structure must obey the following pattern:
                [
                    {'role': 'system', 'content': '<system_content>'},
                    {'role': 'user', 'content': '<user_prompt>'},
                    {'role': 'assistant', 'content': '<assistant_response>'},
                    {'role': 'function', 'name': '<name>', 'function_call': '<function_name_arguments>'}  # not supported at the moment
                ]
            model (str): The transformer model to use.
            max_tokens (int): The maximum number of tokens to use.
            temperature (float, optional): The temperature to use. Defaults to 1.0.
            top_p (float, optional): The top_p to use. Defaults to 1.0.
            tools (list, optional): A list of tools to use. Example:
                [
                    {
                        'type': 'function',
                        {'description': '<a description>', 'name': '<the function name>', 'parameters':
                            {'properties': '<parameter_name>': {'type': '<parameter_type>', 'description': '<description>'}}
                        }
                    },
                ]
                Defaults to [].

        Returns:
            Tuple[str, dict]: The message content of the response and function details if one is
                called.
        """
        cc = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            tools=tools)

        finish_reason = cc.choices[0].finish_reason
        if finish_reason == 'stop':
            logger.info('ChatCompletion finished successfully.')
        elif finish_reason in ['length']:
            logger.warning(f'ChatCompletion terminated due to restriction {finish_reason}.')
        elif finish_reason == 'tool_calls':
            logger.info('ChatCompletion finished successfully (made tool call).')
        elif finish_reason == 'function_call':  # deprecated
            logger.info('ChatCompletion finished successfully (made function call).')
        elif finish_reason == 'null':
            logger.error('WHAT TO DO? finish reason is null.')  # TODO
        elif finish_reason == 'content_filter':
            logger.warning('Content filter fired.')
            # TODO: what to do here? block/confront user?
        else:
            logger.error(f'Unexpected finish_reason "{finish_reason}".')

        self._update_total_tokens(usage_addendum=cc.usage)

        msg = ''
        try:
            msg = cc.choices[0].message.content
        except Exception as e:
            logger.critical('Unknown error evaluating response from ChatCompletion: '
                            f'{type(e).__name__}: {e}')
        if msg is None:
            msg = ''

        if cc.choices[0].message.tool_calls is not None:
            tool_type = cc.choices[0].message.tool_calls[0].type
            if tool_type == 'function':
                fct = {
                    'name': cc.choices[0].message.tool_calls[0].function.name,
                    'arguments': cc.choices[0].message.tool_calls[0].function.arguments
                }
                # fct_name = fct.name
                # fct_args = json.loads(fct.arguments)
            else:
                fct = {}
                logger.critical(f'Tool call type {tool_type} not recognized.')
        else:
            fct = {}  # No function called by assistant

        return msg, fct
