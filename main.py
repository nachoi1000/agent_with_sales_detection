import os
import uuid
from openai import OpenAI
from utils.file_manager import FileManager
from utils.conversation import Conversation, ConversationManager
from utils.llm_manager import Assistant
from dotenv import load_dotenv


file_manager = FileManager()
file_manager.load_md_file('prompts')
conversation_memory_prompt = file_manager.load_md_file('prompts/conversation_memory.md')
sales_detector_prompt = file_manager.load_md_file('prompts/sales_detector.md')

load_dotenv()

api_key = os.environ.get("THE_OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

#Assistants
assistant_memory = Assistant(client=client, base_prompt=conversation_memory_prompt)
assistant_sales_detector = Assistant(client=client, base_prompt=sales_detector_prompt)

def orchestratror(user_input:str , first_message:bool):
    # check if user_input is the first_message = True
    if first_message:
        conversation_id = uuid.uuid4()
        quetsion = user_input
        sales_intention = assistant_sales_detector.assistant_chat_completion_response(prompt=assistant_sales_detector.base_prompt, question=quetsion)
        if sales_intention in ["Strong", "Moderate"]:
            sales_intention = True
        else:
            sales_intention = False
        concent = None
        answer = ""


    # if first_message = True: 
    #   generate conversation_id
    # else:
    #   look for conversation_id and obtain the last row of that conversation_id (took the sales_intention and consent)
    #apply the strategy based on sales_intention and consent
    #based on the strategy generate the answer and save the row of the conversation.