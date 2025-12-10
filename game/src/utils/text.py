import re
import json

import json

def remove_emojis(text):
    # Emoji-Regex-Pattern basierend auf Unicode-Ranges
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F]|"  # Emoticons
        "[\U0001F300-\U0001F5FF]|"  # Symbole & Piktogramme
        "[\U0001F680-\U0001F6FF]|"  # Transport & Karten
        "[\U0001F700-\U0001F77F]|"  # Alchemie-Symbole
        "[\U0001F780-\U0001F7FF]|"  # Geometrische Formen erweitert
        "[\U0001F800-\U0001F8FF]|"  # Ergänzende Symbole
        "[\U0001F900-\U0001F9FF]|"  # Ergänzende Symbole und Piktogramme
        "[\U0001FA00-\U0001FA6F]|"  # Symbole aus asiatischen Kulturen
        "[\U0001FA70-\U0001FAFF]|"  # Weiter Symbole
        "[\U00002702-\U000027B0]|"  # Verschiedene Symbole
        "[\U000024C2-\U0001F251]"   # Umkreiste Zahlen und Symbole
        "",
        re.UNICODE
    )
    text = emoji_pattern.sub('', text)  # Emojis entfernen
    text = re.sub(r"[\s\u200B\u200C\u200D]{2,}", " ", text)  # Doppelte Leerzeichen und unsichtbare Zeichen
    return text.strip()  # Überflüssige Leerzeichen entfernen

def remove_think_tag(input_text):
    # Entfernt alle <think>...</think>-Tags rekursiv
    think_tag_regex = re.compile(r"<think>[\s\S]*?<\/think>", re.MULTILINE)
    sanitized_output = input_text
    while think_tag_regex.search(sanitized_output):
        sanitized_output = think_tag_regex.sub('', sanitized_output).strip()
    return sanitized_output

def sanitize_output_text(input_text):
    return remove_emojis(remove_think_tag(input_text))

def extract_json_text_from_raw_text(raw_content):
    # JSON-Markdown-Blöcke erkennen
    json_block_regex = re.compile(r"```json([\s\S]*?)```", re.MULTILINE)
    generic_block_regex = re.compile(r"```([\s\S]*?)```", re.MULTILINE)

    cleaned_content = raw_content

    # Prüfen auf explizite JSON-Blöcke
    json_block_match = json_block_regex.search(raw_content)
    if json_block_match and json_block_match.group(1):
        cleaned_content = json_block_match.group(1).strip()
    else:
        # Fallback auf generische Blöcke
        generic_block_match = generic_block_regex.search(raw_content)
        if generic_block_match and generic_block_match.group(1):
            cleaned_content = generic_block_match.group(1).strip()

    # Rückgabe von None bei leerem oder "None"-Inhalt
    if cleaned_content in ["None", "[]", ""]:
        return None

    # JSON-Inhalt validieren und bereinigen
    try:
        json.loads(cleaned_content)  # Prüfen, ob es sich um gültiges JSON handelt
        return cleaned_content
    except json.JSONDecodeError as e:
        print(f"Erster Parsing-Versuch fehlgeschlagen: {e}")
        print(f"Rohdaten: ===========================================================\n{raw_content}\n==============================================================")

        # Zweiter Versuch: Ungültige Zeichen entfernen
        try:
            cleaned_content = re.sub(r"^[^{\[]*", "", cleaned_content)  # Entferne alles vor { oder [
            cleaned_content = re.sub(r"[^}\]]*$", "", cleaned_content)  # Entferne alles nach } oder ]
            json.loads(cleaned_content)  # Prüfen, ob es sich um gültiges JSON handelt
            return cleaned_content
        except json.JSONDecodeError as second_error:
            print(f"Zweiter Parsing-Versuch fehlgeschlagen: {second_error}")
            return None
