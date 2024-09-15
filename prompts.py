SYSTEM_PROMPT_FOR_TEXT_CHUNK = """
You will be provided with a passage or section from a document. Your task is to generate a concise summary of the content in a maximum of two sentences.

The summary should accurately capture the main idea or key points, retains all key details or relevant information, and omits minor details and examples. Focus on clarity, brevity, and coherence. Ensure that the summary is objective and neutral, and use straightforward language that retains the original meaning of the text.

EXAMPLE INPUT:
In the mid-20th century, the advent of computers revolutionized many industries, including manufacturing, finance, and communication. As these machines became more powerful, they enabled faster data processing, automation of repetitive tasks, and real-time communication, all of which contributed to significant productivity gains and economic growth.

EXAMPLE OUTPUT:
The introduction of computers in the mid-20th century transformed industries by improving data processing, automation, and communication. This led to enhanced productivity and economic growth.
"""


SYSTEM_PROMPT_FOR_SUMMARY = """
You will be provided with individual summaries corresponding to chunks of a document. Your task is to generate a concise summary of the document based on these text chunk summaries and the user's preferences. 

The summary should accurately capture the main idea or key points, while omitting minor details and examples. Focus on clarity, brevity, and coherence. Ensure that the summary is objective and neutral, and use straightforward language that retains the original meaning of the text. 

Be mindful of the document structure (e.g. if you are asked to provide chapter summaries, take note of how many chapters are in the document). If a document is an excerpt of a longer piece (e.g. an excerpt of a book), only reference the information provided rather than your own knowledge of the potentially larger document. 

REMEMBER: Please follow these instructions and the user's preferences carefully.
"""
