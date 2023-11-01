import os

import openai

import converse

openai.api_key = os.getenv("OPENAI_API_KEY")


class Agent(object):
    """An agent in a conversation."""

    def __init__(self, agent_data: dict, context: str) -> None:
        self.name = agent_data['name']
        self.desc = agent_data['description']
        system_prompt = context['prompt_template'].format(name=self.name, desc=self.desc)
        self.messages = [{'role': 'system', 'content': system_prompt}]
        self.conversation = ''
        self.subagents = None

        if subagents := (agent_data.get('subagents')):
            self.subagent_conv_len = subagents['conversation_len']
            self.subagent_conv_prompt = subagents['initial_prompt']
            self.subagents = self.instantiate_agents(subagents)
    
    @staticmethod
    def instantiate_agents(data: dict):
        return [Agent(agent, data) for agent in data['agents']]
   
    def get_response(self, input: str, model: str = 'gpt-4', subagent_conv: bool = True) -> str:
        """Get agent's response via OpenAI, given input.
        Appends the response to the agent's messages then returns it.
        If the agent has subagents, runs a conversation between them
        and then generates a response from that based on its 
        system prompt.

        Args:
            input (str): The input to the agent.
            model (str, optional): The model to use. Defaults to 'gpt-4'.
            subagent_conv (bool, optional): Whether to run conversation between subagents.
                Defaults to True.
        
        Returns:
            str: The agent's response.
        """

        input_messages = self.messages

        # If agent has subagents, run a conversation
        # between them for the agent to generate its 
        # response from.
        if subagent_conv and self.subagents:
            print(f'{self.name} conversation:\n')
            subagent_output = converse.run_conversation(
                agents=self.subagents,
                initial_prompt=self.subagent_conv_prompt,
                conversation_length=self.subagent_conv_len,
                model=model
            )
            subagent_prompt = (
                f'Statements: {self.conversation}\n' +
                f'{self.name} conversation:\n' + 
                '\n'.join(subagent_output)
            )
            # Input the deliberation to the agent to summarise, 
            # but don't save the deliberation to the agent's messages.
            input_messages = self.messages + [
                {'role': 'user', 'content': subagent_prompt}
            ]

        # Fetch OpenAI response.
        print(f'---{self.name}---')
        response = openai.ChatCompletion.create(
            model=model,
            messages=input_messages,
            temperature=1.0
        )

        # Add input to conversation and messages.
        self.messages.append({'role': 'user', 'content': input})
        self.conversation += input + '\n'

        # Add newest response to conversation and messages.
        newest = response.choices[0].message
        self.messages.append(newest)
        self.conversation += newest.content + '\n'

        return newest['content']
