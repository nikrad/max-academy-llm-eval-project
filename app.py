import chainlit as cl
import openai
import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langsmith.wrappers import wrap_openai
from langsmith import traceable
from parse import parse_pdf_file, parse_text_file, parse_docx_file
from prompts import SYSTEM_PROMPT_FOR_SUMMARY, SYSTEM_PROMPT_FOR_TEXT_CHUNK

PDF_TYPE = "application/pdf"
DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
TEXT_TYPE = "text/plain"

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
endpoint_url = os.getenv("OPENAI_ENDPOINT")

client = wrap_openai(openai.AsyncClient(api_key=api_key, base_url=endpoint_url))
model_kwargs = {"model": "chatgpt-4o-latest", "temperature": 0.25, "max_tokens": 500}

text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=250)

@traceable
@cl.on_chat_start
async def on_chat_start():
    files = None

    # Wait for the user to upload a file
    while files == None:
        files = await cl.AskFileMessage(
            content="Please upload a file you would like summarized to begin!",
            accept=[
                TEXT_TYPE,
                PDF_TYPE,
                DOCX_TYPE,
            ],
            max_size_mb=20,
            timeout=180,
        ).send()

    cl.user_session.set("ask_file_response", files[0])
    await cl.Message(
        content=f"What kind of summary would you like for `{files[0].name}`? For example, how long should it be, and do you want it as bullets or sentences)?"
    ).send()

@traceable
@cl.on_message
async def on_message(message: cl.Message):
    # Maintain the file response in the user session
    ask_file_response = cl.user_session.get("ask_file_response")
    document_summary = cl.user_session.get("document_summary", None)
    message_history = cl.user_session.get("message_history", [])
    
    if document_summary is None:       
        file_type = ask_file_response.type
        msg = await cl.Message(content=f"Processing `{ask_file_response.name}`...").send()
        text = None
        with open(ask_file_response.path, "rb") as f:
            content = f.read()
            # Handle different file types
            if file_type == PDF_TYPE:
                # Process PDF file
                text = await parse_pdf_file(content)
            elif file_type == TEXT_TYPE:
                # Process Text file
                text = await parse_text_file(content)
            elif file_type == DOCX_TYPE:
                # Process DOCX file
                text = await parse_docx_file(content)

        text_chunks = text_splitter.split_text(text)
        text_chunk_summaries = []
        for i, text_chunk in enumerate(text_chunks):
            await cl.Message(id=msg.id, content=f"Reviewing chunk {i + 1} of {len(text_chunks)} in `{ask_file_response.name}`...").update()
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT_FOR_TEXT_CHUNK},
                {
                    "role": "user",
                    "content": f"Summarize the following chunk of a document. If a text chunk includes a chapter title or section heading, please make note of it and the title. Here is the text chunk:\n{text_chunk}",
                },
            ]
            text_chunk_summary = await client.chat.completions.create(
                messages=messages, stream=False, **model_kwargs
            )
            text_chunk_summaries.append(text_chunk_summary.choices[0].message.content)

        document_summary = text_chunk_summaries
        cl.user_session.set("document_summary", document_summary)
        message_history = [{"role": "system", "content": SYSTEM_PROMPT_FOR_SUMMARY}, {"role": "user", "content": f"Here are the document section summaries:\n\n{"\n\n".join(document_summary)}"}]
        await cl.Message(id=msg.id, content=f"Summarizing `{ask_file_response.name}`...").update()
    else:
        msg = await cl.Message(content=f"Summarizing `{ask_file_response.name}`...").send()

    message_history.append({"role": "user", "content": message.content})
    stream = await client.chat.completions.create(messages=message_history, stream=True, **model_kwargs)

    await msg.remove()
    response_msg = await cl.Message(content=f"Done! Here is your summary:\n\n").send()

    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await response_msg.stream_token(token)

    message_history.append({"role": "assistant", "content": response_msg.content})
    cl.user_session.set("message_history", message_history)
    await response_msg.update()
