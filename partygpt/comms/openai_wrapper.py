
import logging
import time
from typing import Tuple

import openai


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
        openai.organization = organisation
        openai.api_key = api_key

    def get_model_list(self):
        model_list = openai.Model.list()
        return model_list

    def _update_total_tokens(self, usage_addendum):
        try:
            completion_t = usage_addendum['completion_tokens']
            prompt_t = usage_addendum['prompt_tokens']
        except KeyError:
            logger.error(
                f'Provided usage_addendum does not contain expected fields: {usage_addendum}')

        if not (isinstance(completion_t, (int, float)) and
                isinstance(prompt_t, (int, float))):
            logger.error(f'Cannot update total token sum with input {completion_t} and {prompt_t}.')
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
            user_prompt,
            function=None) -> list:
        # TODO: make this method more useful
        res = []
        res.append({'role': 'system', 'content': system_content})
        res.append({'role': 'user', 'content': user_prompt})

        if function is not None:  # NOTE: solved via functions arg in request_completion
            # TODO
            raise NotImplementedError()
        return res

    def request_completion(
            self,
            messages: str,
            model: str,
            wait_s: float,
            max_tokens: int,
            # temperature: float=1.0,
            top_p: float=0.8,
            functions: list=[],
            function_call: str='auto') -> Tuple[str, dict]:
        """Requests completion by a transformer model.
        https://platform.openai.com/docs/guides/gpt/chat-completions-api

        Args:
            messages (list): The messages. It's structure must obey the following pattern:
                [
                    {'role': 'system', 'content': '<system_content>'},
                    {'role': 'user', 'content': '<user_prompt>'},
                    {'role': 'assistant', 'content': '<assistant_response>'},
                    {'role': 'function', 'name': '<name>', 'function_call': '<function_name_arguments>'}  # not supported at the moment
                ]
            model (str): The transformer model to use.
            wait_s (float): How long to wait before evaluating the model's response.
            max_tokens (int): The maximum tokens to use.
            ~~temperature (float, optional): The temperature to use. Defaults to 1.0.~~
            top_p (float, optional): The top_p to use. Defaults to 0.8.
            functions (list, optional): A list of function documentations. For details, see
                https://platform.openai.com/docs/guides/gpt/function-calling. Defaults to [].
            function_call (str, optional): The behavior for function calling. Defaults to 'auto'.

        Returns:
            Tuple[str, dict]: The message content of the response and function details if one is
                called.
        """
        cc = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            # temperature=temperature,
            top_p=top_p,
            functions=functions,
            function_call=function_call)

        time.sleep(wait_s)

        finish_reason = cc['choices'][0]['finish_reason']
        if finish_reason == 'stop':
            logger.info('ChatCompletion finished successfully.')
        elif finish_reason in ['length']:
            logger.warning(f'ChatCompletion terminated due to restriction {finish_reason}.')
        elif finish_reason == 'function_call':
            logger.info('ChatCompletion finished successfully (made function call).')
        elif finish_reason == 'null':
            logger.error('WHAT TO DO? finish reason is null.')  # TODO
        elif finish_reason == 'content_filter':
            logger.warning('Content filter fired.')
            # TODO: what to do here? block/confront user?
        else:
            logger.error(f'Unexpected finish_reason "{finish_reason}".')

        self._update_total_tokens(usage_addendum=cc['usage'])

        msg = ''
        try:
            msg = cc['choices'][0]['message']['content']
        except Exception as e:
            logger.critical('Unknown error evaluating response from ChatCompletion: '
                            f'{type(e).__name__}: {e}')
        if msg is None:
            msg = ''

        fct = {}
        try:
            fct = cc['choices'][0]['message']['function_call']
            fct_name = fct['name']
        except KeyError:
            pass  # No function called by assistant
        except Exception as e:
            logger.critical('Unknown error evaluating function_call from ChatCompletion: '
                            f'{type(e).__name__}: {e}')

        return msg, fct
