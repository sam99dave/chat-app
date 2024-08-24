from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

class Prompts:

    @staticmethod
    def chat_prompt(system = "You are a helpful assitant", human_inp = "{input}"):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", human_inp),
            ]
        )

        return prompt

    @staticmethod
    def chat_prompt_with_history(system = "You are a helpful assitant", human_inp = "{input}"):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                MessagesPlaceholder(variable_name="history"),
                ("human", human_inp),
            ]
        )

        return prompt