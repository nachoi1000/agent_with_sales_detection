import os
import uuid
from openai import OpenAI
from utils.file_manager import FileManager
from utils.conversation import Conversation
from utils.llm_manager import Assistant
from db.db_manager import MongoDBManager
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

#MongoDB
db = MongoDBManager()



def format_var_chat_history(resultados: list[dict])-> str:
    """This function recievesa list of Conversations and for each row (dict), retrieves the questiona dn answer, and generate a string based on that values."""
    conversacion = ""
    
    for registro in resultados:
        question = registro.get("question")
        answer = registro.get("answer")
        
        if question:
            conversacion += f"\nUser: {question}"
        
        if answer:
            conversacion += f"\nAssistant: {answer}"
    
    return conversacion.strip()  # Remove any unnecessary line breaks at the beginning or end




def generate_answer(user_input: str, id: str, db_manager: MongoDBManager)-> str:
    """generate_answer recieves a user_input, an id and a db_manager, and returns the answer of teh user_input. It alsosave the conversation in the db"""
    conversation = db_manager.buscar_conversaciones_por_id(conversation_id=id)
    if len(conversation) == 0: # When it is the first message in the conversation
        question = user_input
        sales_intention = client.send_chat_request(assistant="SalesDetector", messages=helper.set_user_message(content=question), variables=[], revision=5)
        if sales_intention in ["Strong", "Moderate"]:
            sales_intention = True
        else:
            sales_intention = False
        consent = None
        profile = client.send_chat_request(assistant="PersonaDetector", messages=helper.set_user_message(content=question), variables=[], revision=4)
        answer = client.send_execute_request(profile=profile, question=question)
        conversation_to_save = Conversation(conversation_id=id, question=question, answer=answer, sales_intention=sales_intention, consent=consent)
        db_manager.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
        #print(answer)
        return answer # it also should return id.
    
    else: # When the conversation has previos messages.
        last_sales_intention = conversation[-1].get("sales_intention")
        last_consent = conversation[-1].get("content")
        var_chat_history = format_var_chat_history(resultados=conversation)

        # when last_sales_intention is False:
        if last_sales_intention is False:
            question = user_input
            sales_intention = client.send_chat_request(assistant="SalesDetector", messages=helper.set_user_message(content=question), variables=[], revision=5)
            if sales_intention in ["Strong", "Moderate"]:
                sales_intention = True
            else:
                sales_intention = False
            consent = None
            profile = client.send_chat_request(assistant="PersonaDetector", messages=helper.set_user_message(content=question), variables=[], revision=4)
            chat_history = client.send_chat_request(assistant="Conversation_history", messages =[], variables=helper.set_variables(chat_history_value=var_chat_history, question_value=question), revision=2)
            answer = client.send_execute_request(profile=profile, question=chat_history)
            conversation_to_save = Conversation(conversation_id=id, question=question, answer=answer, sales_intention=sales_intention, consent=consent)
            db_manager.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
            return answer
        
        # when last_sales_intention is True and last_consent is None:
        if last_sales_intention is True and last_consent is None:
            question = user_input
            sales_intention = True
            concent = client.send_chat_request(assistant="ConsentimentDetector", messages=helper.set_user_message(content=question), variables=[], revision=3)
            if consent in ["Strong", "Moderate"]:
                consent = True
                answer = client.send_chat_request(assistant="thanksAndRequestData", messages=helper.set_user_message(content=question), variables=[], revision=2)
                #answer = "Thank you for giving your consent! To proceed, in the next message, please provide both your full name and email address. This information is necessary for us to assist you further."
                conversation_to_save = Conversation(conversation_id=id, question=question, answer=answer, sales_intention=sales_intention, consent=consent)
                db_manager.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
                return answer
            else:
                consent = False
                profile = client.send_chat_request(assistant="PersonaDetector", messages=helper.set_user_message(content=question), variables=[], revision=4)
                chat_history = client.send_chat_request(assistant="Conversation_history", messages =[], variables=helper.set_variables(chat_history_value=var_chat_history, question_value=question), revision=2)
                answer = client.send_execute_request(profile=profile, question=chat_history)
                conversation_to_save = Conversation(conversation_id=id, question=question, answer=answer, sales_intention=sales_intention, consent=consent)
                db_manager.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
                return answer

                
        # when last_sales_intention is True and last_content is not None:
        if last_sales_intention is True and last_consent is not None:
            question = user_input
            sales_intention = True
            consent = last_consent
            profile = client.send_chat_request(assistant="PersonaDetector", messages=helper.set_user_message(content=question), variables=[], revision=4)
            chat_history = client.send_chat_request(assistant="Conversation_history", messages =[], variables=helper.set_variables(chat_history_value=var_chat_history, question_value=question), revision=2)
            answer = client.send_execute_request(profile=profile, question=chat_history)
            conversation_to_save = Conversation(conversation_id=id, question=question, answer=answer, sales_intention=sales_intention, consent=consent)
            db_manager.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
            return answer
        


#sales_intention = assistant_sales_detector.assistant_chat_completion_response(prompt=assistant_sales_detector.base_prompt, question=quetsion)
#if sales_intention in ["Strong", "Moderate"]:
#    sales_intention = True
#else:
#    sales_intention = False