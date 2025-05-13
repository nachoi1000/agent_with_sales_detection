from typing import Tuple
from utils.logger import logger
from utils.conversation import Conversation, ConversationForSales
from utils.user_data import UserInformation
from config import db_manager_conversations, db_manager_userdata, assistant_content_filter, assistant_memory, assistant_sales_detector, assistant_consentiment, assistant_request_data, rag, limit_messages_in_conversation



def format_var_chat_history(resultados: list[dict])-> str:
    """This function recieves a list of ConversationForSales and for each row (dict), retrieves the questiona dn answer, and generate a string based on that values."""
    conversacion = ""
    
    for registro in resultados:
        question = registro.get("question")
        answer = registro.get("answer")
        
        if question:
            conversacion += f"\nUser: {question}"
        
        if answer:
            conversacion += f"\nAssistant: {answer}"
    
    return conversacion.strip()  # Remove any unnecessary line breaks at the beginning or end


def format_var_conversationforsales_messages(resultados: list[dict])-> str:
    """This function recieves a list of Conversations and for each row (dict), retrieves the questiona dn answer, and generate a string based on that values."""
    conversacion = ""
    
    for i, registro in enumerate(resultados, start=1):
        message = registro.get("message")
        
        if message:
            conversacion += f"\nMessage {i}: {message}"
    
    return conversacion.strip()  # Remove any unnecessary line breaks at the beginning or end


request_consent = "\n\nWe have noticed that you seems to be interested in know more deeply about QuantumChain's products and services.\n\nIf you would like one of our specialists to contact you and provide more detailed information, Do you give giving consent?\n\nFeel free to review our [Privacy Policy] if you have any concerns about the security or integrity of your personal data."
thanks_and_true_consent = "Thank you for giving your consent! To proceed, in the next message, please provide both your full name and email address. This information is necessary for us to assist you further."
thanks_and_false_consent= "Understood. You have not given your consent, so we won’t collect any personal information. However, feel free to continue asking any questions you may have — we're here to help!"

def generate_answer(id: str, user_input: str, limit_messages: int = limit_messages_in_conversation)-> Tuple[str, int]:
    """generate_answer recieves a user_input, a conversation_id, a db_manager and a limit_messages, and returns the answer of the user_input and a integer indicating the remaining messages available in the conversation. It also saves the conversation in the db"""
    
    tokens_input = 0
    tokens_output = 0
    question = user_input
    logger.info(f"conversation_id: {id} - question: {question}")

    assistant_content_filter_api_call = assistant_content_filter.chat_completion_response(prompt=assistant_content_filter.base_prompt, question=question)
    tokens_input += assistant_content_filter_api_call.get("tokens_input")
    tokens_output += assistant_content_filter_api_call.get("tokens_output")
    content_filter = assistant_content_filter_api_call.get("answer")
    logger.info(f"conversation_id: {id} - assistant_content_filter_api_call: {assistant_content_filter_api_call}")
    
    if "true" in content_filter: # Safe user_input
        conversation = db_manager_conversations.buscar_conversaciones_por_id(conversation_id=id)
        
        if len(conversation) == 0: # When it is the first message in the conversation
            sales_intention_api_call = assistant_sales_detector.chat_completion_response(prompt=assistant_sales_detector.base_prompt, question=question)
            tokens_input += sales_intention_api_call.get("tokens_input")
            tokens_output += sales_intention_api_call.get("tokens_output")
            logger.info(f"conversation_id: {id} - sales_intention_api_call: {sales_intention_api_call}")
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
            db_manager_conversations.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
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
                logger.info(f"conversation_id: {id} - sales_intention_api_call: {sales_intention_api_call}")
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
                    db_manager_conversations.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
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
                    db_manager_conversations.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
                    remaining_messages = limit_messages - len(conversation) - 1
                    return {"answer":answer, "remaining_messages":remaining_messages} 
            
            # when last_sales_intention is True and last_consent is None:
            if last_sales_intention is True and last_consent is None:
                sales_intention = True
                logger.info(f"conversation_id: {id} - sales_intention: {sales_intention}")
                consent_api_call = assistant_consentiment.chat_completion_response(prompt=assistant_consentiment.base_prompt, question=question)
                tokens_input += consent_api_call.get("tokens_input")
                tokens_output += consent_api_call.get("tokens_output")
                if consent_api_call.get("answer") in ["Strong", "Moderate"]:
                    consent = True
                    logger.info(f"conversation_id: {id} - consent: {consent}")
                    answer = thanks_and_true_consent
                    logger.info(f"conversation_id: {id} - answer: {answer}")
                    conversation_to_save = Conversation(conversation_id=id, question=question, answer=answer, sales_intention=sales_intention, consent=consent)
                    db_manager_conversations.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
                    remaining_messages = limit_messages - len(conversation) - 1
                    return {"answer":answer, "remaining_messages":remaining_messages} 
                else:
                    consent = False
                    logger.info(f"conversation_id: {id} - consent: {consent}")
                    answer = thanks_and_false_consent
                    logger.info(f"conversation_id: {id} - answer: {answer}")
                    conversation_to_save = Conversation(conversation_id=id, question=question, answer=answer, sales_intention=sales_intention, consent=consent)
                    db_manager_conversations.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
                    remaining_messages = limit_messages - len(conversation) - 1
                    return {"answer":answer, "remaining_messages":remaining_messages} 

            # when last_sales_intention is True and last_content is True:        
            if last_sales_intention is True and last_consent is True:
                conversation_for_sale = db_manager_userdata.buscar_conversaciones_por_id(conversation_id=id)
                last_name = conversation_for_sale[-1].get("name")
                last_email = conversation_for_sale[-1].get("email")

                if last_name or last_email is None: #There are variables missing to "catch" the sale
                    if len(conversation_for_sale) == 0:
                        messages = question
                    else:
                        messages = format_var_conversationforsales_messages(resultados=conversation) + f"\nLast Message : {question}"
                    
                    sales_intention = True
                    logger.info(f"conversation_id: {id} - sales_intention: {sales_intention}")
                    consent = True
                    logger.info(f"conversation_id: {id} - consent: {consent}")
                    
                    # Scrap User Data in the message.
                    user_data_api_call = assistant_request_data.chat_completion_structured_response(prompt=messages, output_format=UserInformation)
                    tokens_input += user_data_api_call.get("tokens_input")
                    tokens_output += user_data_api_call.get("tokens_output")
                    user_data = user_data_api_call.get("answer")
                    logger.info(f"conversation_id: {id} - user_data: {user_data}")
                    user_data_to_save = ConversationForSales(conversation_id=id, name=user_data.name, email=user_data.email, message=question)
                    db_manager_userdata.add_conversation(user_data_to_save) # SAVE conversation_to_save IN DB

                    # Generate a responses requesting the missing user data.
                    response_api_call = assistant_request_data.chat_completion_response(prompt=assistant_request_data.base_prompt.format(user_data = UserInformation.schema_json(indent=2), current_data = user_data.get("answer")), question="")
                    tokens_input += response_api_call.get("tokens_input")
                    tokens_output += response_api_call.get("tokens_output")
                    answer = response_api_call.get("answer")
                    conversation_to_save = Conversation(conversation_id=id, question=question, answer=answer, sales_intention=sales_intention, consent=consent)
                    db_manager_conversations.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
                    remaining_messages = limit_messages - len(conversation)
                    return {"answer":answer, "remaining_messages":remaining_messages}
                
                else: #There are all the variables to "catch" the sale
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
                    db_manager_conversations.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
                    remaining_messages = limit_messages - len(conversation) - 1
                    return {"answer":answer, "remaining_messages":remaining_messages} 

            # when last_sales_intention is True and last_content is False:
            if last_sales_intention is True and last_consent is False:
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
                db_manager_conversations.add_conversation(conversation_to_save) # SAVE conversation_to_save IN DB
                remaining_messages = limit_messages - len(conversation) - 1
                return {"answer":answer, "remaining_messages":remaining_messages} 

    else:
        answer = f"Bad user input. Please review you message, we have not answer your request due to the following reason: {content_filter}"
        remaining_messages = limit_messages - 1
        return {"answer":answer, "remaining_messages":remaining_messages}