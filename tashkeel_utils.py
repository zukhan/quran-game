# tashkeel_utils.py
import re

tashkeel_pattern = re.compile(r'[\u064B-\u0652\u0670]')

dotless_map = {
    'ب': 'ٮ',
    'ت': 'ٮ',
    'ث': 'ٮ',
    'ج': 'ح',
    'خ': 'ح',
    'ذ': 'د',
    'ز': 'ر',
    'ش': 'س',
    'ض': 'ص',
    'ظ': 'ط',
    'غ': 'ع',
    'ف': 'ڡ',
    'ة': 'ه',
    'أ': 'ا',
    'إ': 'ا',
    'آ': 'ا',
    'ؤ': 'و',
}

letter_placement = {
    'ق': {'beginning': 'ڡ', 'middle': 'ڡ', 'end': 'ٯ', 'alone': 'ٯ'},
    'ي': {'beginning': 'ٮ', 'middle': 'ٮ', 'end': 'ى', 'alone': 'ى'},
    'ئ': {'beginning': 'ٮ', 'middle': 'ٮ', 'end': 'ى', 'alone': 'ى'},
    'ن': {'beginning': 'ٮ', 'middle': 'ٮ', 'end': 'ں', 'alone': 'ں'},
}

def strip_tashkeel(text):
    return tashkeel_pattern.sub('', text)

def get_contextual_form(char, prev_char, next_char):
    if char not in letter_placement:
        return char

    if prev_char == ' ' or prev_char is None:
        form_type = 'beginning' if next_char and next_char != ' ' else 'alone'
    elif next_char == ' ' or next_char is None:
        form_type = 'end'
    else:
        form_type = 'middle'

    return letter_placement[char][form_type]

def remove_tashkeel(text):
    text = strip_tashkeel(text)
    stripped_text = []
    length = len(text)

    for i, char in enumerate(text):
        prev_char = text[i - 1] if i > 0 else None
        next_char = text[i + 1] if i < length - 1 else None

        converted_char = dotless_map.get(char, char)

        if converted_char in letter_placement:
            converted_char = get_contextual_form(converted_char, prev_char, next_char)

        stripped_text.append(converted_char)
    return ''.join(stripped_text)

