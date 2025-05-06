import os
from typing import Tuple
from openai import OpenAI
from utils.logger import logger
from utils.file_manager import FileManager
from utils.conversation import Conversation
from utils.llm_manager import Assistant, RAG
from storage.db.db_manager import MongoDBManager
from storage.vector_db.vectorstore import ChromaVectorStore
from dotenv import load_dotenv


file_manager = FileManager()
conversation_memory_prompt = file_manager.load_md_file('prompts/conversation_memory.md')
sales_detector_prompt = file_manager.load_md_file('prompts/sales_detector.md')
consentiment_prompt = file_manager.load_md_file('prompts/consentiment.md')
rag_prompt = file_manager.load_md_file('prompts/quantum_rag.md')

load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

limit_messages_in_conversation = int(os.environ.get("LIMIT_MESSAGES_IN_CONVERSATION"))

#ChormaDB
collection_name = "test_2"
persist_directory = "data_ingestion/indexing/vectorstore"
vectorstore = ChromaVectorStore(collection_name=collection_name, persist_directory=persist_directory)

#Assistants
assistant_memory = Assistant(client=client, base_prompt=conversation_memory_prompt)
assistant_sales_detector = Assistant(client=client, base_prompt=sales_detector_prompt)
assistant_consentiment = Assistant(client=client, base_prompt=consentiment_prompt)

#RAG
rag = RAG(client=client, base_prompt=rag_prompt, vectorstore=vectorstore)

#MongoDB
db_manager = MongoDBManager()



def format_var_chat_history(resultados: list[dict])-> str:
    """This function recieves a list of Conversations and for each row (dict), retrieves the questiona dn answer, and generate a string based on that values."""
    conversacion = ""
    
    for registro in resultados:
        question = registro.get("question")
        answer = registro.get("answer")
        
        if question:
            conversacion += f"\nUser: {question}"
        
        if answer:
            conversacion += f"\nAssistant: {answer}"
    
    return conversacion.strip()  # Remove any unnecessary line breaks at the beginning or end

request_consent = "/n/n We have noticed that you seems to be interested in know more deeply about QuantumChain's products and services./n/n Give your consent!!!"
thanks_and_true_consent = "Thank you for giving your consent! To proceed, in the next message, please provide both your full name and email address. This information is necessary for us to assist you further."
thanks_and_false_consent= "Understood. You have not given your consent, so we won’t collect any personal information. However, feel free to continue asking any questions you may have — we're here to help!"

def generate_answer(id: str, user_input: str, db_manager: MongoDBManager = db_manager, limit_messages: int = limit_messages_in_conversation)-> Tuple[str, int]:
    """generate_answer recieves a user_input, a conversation_id, a db_manager and a limit_messages, and returns the answer of the user_input and a integer indicating the remaining messages available in the conversation. It also saves the conversation in the db"""
    conversation = db_manager.buscar_conversaciones_por_id(conversation_id=id)
    tokens_input = 0
    tokens_output = 0
    question = user_input
    logger.info(f"conversation_id: {id} - question: {question}")
    
    if len(conversation) == 0: # When it is the first message in the conversation
        sales_intention_api_call = assistant_sales_detector.chat_completion_response(prompt=assistant_sales_detector.base_prompt, question=question)
        tokens_input += sales_intention_api_call.get("tokens_input")
        tokens_output += sales_intention_api_call.get("tokens_output")
        if sales_intention_api_call.get("answer") in ["Strong", "Moderate"]:
            sales_intention = True
        else:
            sales_intention = False
        logger.info(f"conversation_id: {id} - sales_intention: {sales_intention}")
        consent = None
        logger.info(f"conversation_id: {id} - consent: {consent}")
        context = rag.get_context(question=question)
        rag_api_call = rag.chat_completion_response(prompt=rag.base_prompt.format(context=context, question = question), question=question)
        tokens_input += rag_api_call.get("tokens_input")
        tokens_output += rag_api_call.get("tokens_output")
        answer = rag_api_call.get("answer")
        logger.info(f"conversation_id: {id} - answer: {answer}")
        conversation_to_save = Conversation(conversation_id=id, question=question, answer=answer, sales_intention=sales_intention, consent=consent)
        db_manager.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
        #print(answer)
        remaining_messages = limit_messages - 1
        return {"answer":answer, "remaining_messages":remaining_messages} 
    
    else: # When the conversation has previos messages.
        last_sales_intention = conversation[-1].get("sales_intention")
        last_consent = conversation[-1].get("consent")
        var_chat_history = format_var_chat_history(resultados=conversation)
        chat_history_api_call = assistant_memory.chat_completion_response(prompt=assistant_memory.base_prompt.format(var_chat_history=var_chat_history,question=question), question="")
        tokens_input += chat_history_api_call.get("tokens_input")
        tokens_output += chat_history_api_call.get("tokens_output")
        chat_history = chat_history_api_call.get("answer")

        # when last_sales_intention is False:
        if last_sales_intention is False:
            sales_intention_api_call = assistant_sales_detector.chat_completion_response(prompt=assistant_sales_detector.base_prompt, question=question)
            tokens_input += sales_intention_api_call.get("tokens_input")
            tokens_output += sales_intention_api_call.get("tokens_output")
            if sales_intention_api_call.get("answer") in ["Strong", "Moderate"]:
                sales_intention = True
                logger.info(f"conversation_id: {id} - sales_intention: {sales_intention}")
                consent = None
                logger.info(f"conversation_id: {id} - consent: {consent}")
                context = rag.get_context(question=question)
                rag_api_call = rag.chat_completion_response(prompt=rag.base_prompt.format(context=context, question = chat_history), question=chat_history)
                tokens_input += rag_api_call.get("tokens_input")
                tokens_output += rag_api_call.get("tokens_output")
                answer = rag_api_call.get("answer") + request_consent
                logger.info(f"conversation_id: {id} - answer: {answer}")
                conversation_to_save = Conversation(conversation_id=id, question=question, answer=answer, sales_intention=sales_intention, consent=consent)
                db_manager.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
                remaining_messages = limit_messages - len(conversation) + 2
                return {"answer":answer, "remaining_messages":remaining_messages} 
            else:
                sales_intention = False
                logger.info(f"conversation_id: {id} - sales_intention: {sales_intention}")
                consent = None
                logger.info(f"conversation_id: {id} - consent: {consent}")
                context = rag.get_context(question=question)
                rag_api_call = rag.chat_completion_response(prompt=rag.base_prompt.format(context=context, question = chat_history), question=chat_history)
                tokens_input += rag_api_call.get("tokens_input")
                tokens_output += rag_api_call.get("tokens_output")
                answer = rag_api_call.get("answer")
                logger.info(f"conversation_id: {id} - answer: {answer}")
                conversation_to_save = Conversation(conversation_id=id, question=question, answer=answer, sales_intention=sales_intention, consent=consent)
                db_manager.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
                remaining_messages = limit_messages - len(conversation) - 1
                return {"answer":answer, "remaining_messages":remaining_messages} 
        
        # when last_sales_intention is True and last_consent is None:
        if last_sales_intention is True and last_consent is None:
            sales_intention = True
            logger.info(f"conversation_id: {id} - sales_intention: {sales_intention}")
            consent_api_call = assistant_consentiment.chat_completion_response(prompt=assistant_consentiment.base_prompt, question=question)
            tokens_input += consent_api_call.get("tokens_input")
            tokens_output += consent_api_call.get("tokens_output")
            if consent.get("answer") in ["Strong", "Moderate"]:
                consent = True
                logger.info(f"conversation_id: {id} - consent: {consent}")
                answer = thanks_and_true_consent
                logger.info(f"conversation_id: {id} - answer: {answer}")
                conversation_to_save = Conversation(conversation_id=id, question=question, answer=answer, sales_intention=sales_intention, consent=consent)
                db_manager.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
                remaining_messages = limit_messages - len(conversation) - 1
                return {"answer":answer, "remaining_messages":remaining_messages} 
            else:
                consent = False
                logger.info(f"conversation_id: {id} - consent: {consent}")
                answer = thanks_and_false_consent
                logger.info(f"conversation_id: {id} - answer: {answer}")
                conversation_to_save = Conversation(conversation_id=id, question=question, answer=answer, sales_intention=sales_intention, consent=consent)
                db_manager.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
                remaining_messages = limit_messages - len(conversation) - 1
                return {"answer":answer, "remaining_messages":remaining_messages} 

                
        # when last_sales_intention is True and last_content is not None:
        if last_sales_intention is True and last_consent is not None:
            sales_intention = True
            logger.info(f"conversation_id: {id} - sales_intention: {sales_intention}")
            consent = last_consent
            logger.info(f"conversation_id: {id} - consent: {consent}")
            context = rag.get_context(question=question)
            rag_api_call = rag.chat_completion_response(prompt=rag.base_prompt.format(context=context, question = chat_history), question=chat_history)
            tokens_input += rag_api_call.get("tokens_input")
            tokens_output += rag_api_call.get("tokens_output")
            answer = rag_api_call.get("answer")
            logger.info(f"conversation_id: {id} - answer: {answer}")
            conversation_to_save = Conversation(conversation_id=id, question=question, answer=answer, sales_intention=sales_intention, consent=consent)
            db_manager.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
            remaining_messages = limit_messages - len(conversation) - 1
            return {"answer":answer, "remaining_messages":remaining_messages} 
