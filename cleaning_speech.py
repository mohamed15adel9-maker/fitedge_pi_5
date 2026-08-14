import re

def clean_for_speech(text):
    """Remove markdown/symbols that TTS would read aloud."""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)   # **bold** -> bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)        # *italic* -> italic
    text = text.replace('*', '')                     # stray asterisks
    text = text.replace('#', '')                     # headers
    text = text.replace('`', '')                     # code ticks
    text = re.sub(r'^\s*[-•]\s*', '', text, flags=re.MULTILINE)  # bullet dashes
    text = re.sub(r'\n{2,}', '. ', text)             # blank lines -> pause
    text = re.sub(r'\s+', ' ', text).strip()         # collapse whitespace
    return text