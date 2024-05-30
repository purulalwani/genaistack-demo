import utils
import streamlit as st
from streaming import StreamHandler

from langchain_cohere import ChatCohere
from langchain.chains import ConversationChain
import cohere
import os

st.set_page_config(page_title="Chatbot", page_icon="💬")
st.header('Basic Chatbot')
st.write('Allows users to interact with the LLM')
st.write('[![view source code ](https://img.shields.io/badge/view_source_code-gray?logo=github)](https://github.com/shashankdeshpande/langchain-chatbot/blob/master/pages/1_%F0%9F%92%AC_basic_chatbot.py)')

class BasicChatbot:

    def __init__(self):
        self.openai_model = utils.configure_cohere()
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
    
    def setup_chain(self):
        llm = ChatCohere(model_name=self.openai_model, temperature=0, streaming=False)
        chain = ConversationChain(llm=llm, verbose=True)
        return chain
    
    def setup_chat(self):
        chat = ChatCohere(model_name=self.openai_model, temperature=0, streaming=False)
        
        return chat
    
    def setup_cohere_client(self):
        cohere_client = cohere.Client(api_key=self.cohere_api_key)
        
        return cohere_client

    @utils.enable_chat_history
    def main(self):
        chain = self.setup_chain()
        # chat = self.setup_chat()
        # cohere_client = self.setup_cohere_client()
        user_query = st.chat_input(placeholder="Ask me anything!")
        if user_query:
            with st.chat_message("user"):
                utils.display_msg(user_query, 'user')
            with st.chat_message("assistant"):
                # st_cb = StreamHandler(st.empty())
                result = chain.invoke(user_query
                    # {"input":user_query},
                    # {"callbacks": [st_cb]}
                )
                # result = chat.invoke(user_query)
                # for result in chat.astream(user_query):

                response = result["response"]
                # print("Calling chat stream.....")
                # for event in cohere_client.chat_stream(message=user_query):
                #     print("in chat stream.....", event.event_type)
                #     if event.event_type == "text-generation":
                #         # print(event)
                #         # st.session_state.messages.append({"role": "assistant", "content": event.text})
                #         # st.write(event.text)
                #         utils.display_msg(event.text, "assistant")
                #     elif event.event_type == "stream-end":
                #         # print(event)
                #         # st.session_state.messages.append({"role": "assistant", "content": event.text})
                #         # st.write(event.text)
                #         utils.display_msg(event.text, "assistant")
                #     elif event.event_type == "stream-start":
                #         # print(event)
                #         # st.session_state.messages.append({"role": "assistant", "content": event.text})
                #         # st.write(event.text)
                #         utils.display_msg(event.text, "assistant")
                # response = result.content
                # print(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.write(response)
                

if __name__ == "__main__":
    obj = BasicChatbot()
    obj.main()