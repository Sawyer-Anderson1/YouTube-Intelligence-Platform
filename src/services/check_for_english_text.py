import re
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

# function to check if an input string has letters
def has_letters(string):
    return bool(re.search('[a-zA-Z]', string))

# function to check for english
def check_english(text):
    is_english_video = False
    try:
        # use langdetect on the titel and description
        if has_letters(text):
            text_lang = detect(text)
            is_english_video = (text_lang == 'en')
    except LangDetectException:
        is_english_video = False

    return is_english_video
