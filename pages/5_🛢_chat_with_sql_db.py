import utils
import sqlite3
import streamlit as st
from pathlib import Path
from sqlalchemy import create_engine

from langchain_cohere import ChatCohere
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool

from operator import itemgetter

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import chat_agent_executor
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.messages import SystemMessage

st.set_page_config(page_title="ChatSQL", page_icon="🛢")
st.header('Chat with SQL database')
st.write('Enable the chatbot to interact with a SQL database through simple, conversational commands.')
st.write('[![view source code ](https://img.shields.io/badge/view_source_code-gray?logo=github)](https://github.com/shashankdeshpande/langchain-chatbot/blob/master/pages/5_%F0%9F%9B%A2_chat_with_sql_db.py)')

class SqlChatbot:

    def __init__(self):
        self.openai_model = utils.configure_cohere()
    
    def setup_db(_self, db_uri):
        if db_uri == 'USE_SAMPLE_DB':
            db_filepath = (Path(__file__).parent.parent / "assets/Chinook.db").absolute()
            
            db_uri = f"sqlite:////{db_filepath}"
            print(db_uri)
            creator = lambda: sqlite3.connect(f"file:{db_filepath}?mode=ro", uri=True)
            db = SQLDatabase(create_engine("sqlite:///", creator=creator))
        else:
            db = SQLDatabase.from_uri(database_uri=db_uri)
        
        with st.sidebar.expander('Database tables', expanded=True):
            st.info('\n- '+'\n- '.join(db.get_usable_table_names()))
        return db
    
    def setup_sql_agent(_self, db):
        llm = ChatCohere(model_name=_self.openai_model, temperature=0, streaming=False)

        agent = create_sql_agent(
            llm=llm,
            db=db,
            # top_k=10,
            verbose=True,
            # agent_type="tool-calling",
            handle_parsing_errors=True,
            handle_sql_errors=True
        )
        return agent
    def setup_sql_chain(_self, db):
        llm = ChatCohere(model_name=_self.openai_model, temperature=0, streaming=False)

        execute_query = QuerySQLDataBaseTool(db=db)
        write_query = create_sql_query_chain(
            llm=llm,
            db=db,
            
        )
        chain = write_query
        # answer_prompt = PromptTemplate.from_template(
        #     """Given the following user question, corresponding SQL query, and SQL result, answer the user question.

        #     Question: {question}
        #     SQL Query: {query}
        #     SQL Result: {result}
        #     Answer: """
        #     )

        # chain = (
        #     RunnablePassthrough.assign(query=write_query).assign(
        #     result=itemgetter("query") | execute_query
        #     )
        #     | answer_prompt
        #     | llm
        #     | StrOutputParser()
        # )
        return chain

    def setup_sql_agent_executor(_self, db):
        llm = ChatCohere(model_name=_self.openai_model, temperature=0, streaming=False)
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)

        tools = toolkit.get_tools()

        SQL_PREFIX = """You are an agent designed to interact with a SQL database.
        Given an input question, create a syntactically correct SQLite query to run, then look at the results of the query and return the answer.
        Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 5 results.
        You can order the results by a relevant column to return the most interesting examples in the database.
        Never query for all the columns from a specific table, only ask for the relevant columns given the question.
        You have access to tools for interacting with the database.
        Only use the below tools. Only use the information returned by the below tools to construct your final answer.
        You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

        DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

        To start you should ALWAYS look at the tables in the database to see what you can query.
        Do NOT skip this step.
        Then you should query the schema of the most relevant tables."""

        system_message = SystemMessage(content=SQL_PREFIX)
        agent_executor = chat_agent_executor.create_tool_calling_executor(
                llm, tools, messages_modifier=system_message
            )
        return agent_executor;

    @utils.enable_chat_history
    def main(self):

        # User inputs
        radio_opt = ['Use sample db - Chinook.db','Connect to your SQL db']
        selected_opt = st.sidebar.radio(
            label='Choose suitable option',
            options=radio_opt
        )
        if radio_opt.index(selected_opt) == 1:
            with st.sidebar.popover(':orange[⚠️ Security note]', use_container_width=True):
                warning = "Building Q&A systems of SQL databases requires executing model-generated SQL queries. There are inherent risks in doing this. Make sure that your database connection permissions are always scoped as narrowly as possible for your chain/agent's needs.\n\nFor more on general security best practices - [read this](https://python.langchain.com/docs/security)."
                st.warning(warning)
            db_uri = st.sidebar.text_input(
                label='Database URI',
                placeholder='mysql://user:pass@hostname:port/db'
            )
        else:
            db_uri = 'USE_SAMPLE_DB'
        
        if not db_uri:
            st.error("Please enter database URI to continue!")
            st.stop()
        
        db = self.setup_db(db_uri)
        # agent = self.setup_sql_agent(db)
        # chain = self.setup_sql_chain(db)
        agent_executor = self.setup_sql_agent_executor(db)
        user_query = st.chat_input(placeholder="Ask me anything!")

        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.chat_message("user").write(user_query)

            with st.chat_message("assistant"):
                st_cb = StreamlitCallbackHandler(st.container())
                # result = agent.invoke(
                #     {"input": user_query},
                #     {"callbacks": [st_cb]}
                # )
                # chain.get_prompts()[0].pretty_print()
                # result = chain.invoke({"question": user_query})
                # response = result
                # print("SQL Query -> ", response)
                # response = db.run(response)
                # response = result["output"]

                response = agent_executor.invoke(
                    {"messages": [HumanMessage(content=user_query)]}
                    )
                response_length = len(response["messages"])
                response = response["messages"]
                print("Response -> ", response_length, response[response_length-1])
                response = response[response_length-1].content
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.write(response)

if __name__ == "__main__":
    obj = SqlChatbot()
    obj.main()