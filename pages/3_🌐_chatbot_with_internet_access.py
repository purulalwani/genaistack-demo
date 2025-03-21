import utils
import streamlit as st

from langchain import hub
from langchain_cohere import ChatCohere, create_cohere_react_agent
from langchain.memory import ConversationBufferMemory
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain.agents import AgentExecutor, Tool, create_react_agent
from langchain.prompts import ChatPromptTemplate

st.set_page_config(page_title="ChatWeb", page_icon="🌐")
st.header('Chatbot with Internet Access')
st.write('Equipped with internet access, enables users to ask questions about recent events')
st.write('[![view source code ](https://img.shields.io/badge/view_source_code-gray?logo=github)](https://github.com/shashankdeshpande/langchain-chatbot/blob/master/pages/3_%F0%9F%8C%90_chatbot_with_internet_access.py)')

class InternetChatbot:

    def __init__(self):
        self.openai_model = utils.configure_cohere()

    @st.cache_resource(show_spinner='Connecting..')
    def setup_agent(_self):
        # Define tool
        ddg_search = DuckDuckGoSearchRun()
        tools = [
            Tool(
                name="DuckDuckGoSearch",
                func=ddg_search.run,
                description="Useful for when you need to answer questions about current events. You should ask targeted questions",
            )
        ]

        # Get the prompt - can modify this
        # prompt = hub.pull("hwchase17/react-chat")
        prompt = ChatPromptTemplate.from_template("{input}")

        # Setup LLM and Agent
        llm = ChatCohere(model_name=_self.openai_model, temperature=0, streaming=True)
        memory = ConversationBufferMemory(memory_key="chat_history")
        agent = create_cohere_react_agent(llm, tools, prompt)
        # print("Stream runnable -> ", agent.stream_runnable);
        # print(agent.config_specs)
        # agent_executor = AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        return agent_executor, memory

    @utils.enable_chat_history
    def main(self):
        agent_executor, memory = self.setup_agent()
        user_query = st.chat_input(placeholder="Ask me anything!")
        if user_query:
            with st.chat_message('user'):
                utils.display_msg(user_query, 'user')
            with st.chat_message("assistant"):
                st_cb = StreamlitCallbackHandler(st.container())
                result = agent_executor.invoke(
                    {"input": user_query}
                    # {"input": user_query, "chat_history": memory.chat_memory.messages},
                    # {"callbacks": [st_cb]}
                )
                response = result["output"]
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.write(response)

if __name__ == "__main__":
    obj = InternetChatbot()
    obj.main()