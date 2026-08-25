"""Text formatting utilities."""

def fix_spacing(text):
    return " ".join(text.split())

def capitalize_sentences(text):
    return ". ".join(s.strip().capitalize() for s in text.split("."))

def apply_punctuation(text):
    return text.replace("!!", "!").replace("??", "?")

def format_text(text):
    """Apply all formatting rules to text."""
    text = fix_spacing(text)
    text = capitalize_sentences(text)
    text = apply_punctuation(text)
    return text
