import os
from typing import cast

import logfire
from pydantic import BaseModel

from pydantic_ai import Agent
from pydantic_ai.models import KnownModelName
from prompt import SEARCH_NEWSLINK
# 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured
logfire.configure(send_to_logfire='if-token-present')


class NewslinkAnswer(BaseModel):
    
    is_valid: bool
    reasoning: str


model = cast(KnownModelName, os.getenv('PYDANTIC_AI_MODEL', 'openai:gpt-4o'))

print(f'Using model: {model}')

agent = Agent(model, result_type=NewslinkAnswer, num_results=3)

def verify_newslink(newslink: str) -> tuple[bool, str]:

    prompt = ""
    
    result = agent.run_sync('The windy city in the US of A.')
    
    print(result.data)
    print(result.usage())

    answer = result.data
    return answer.is_valid, answer.reasoning