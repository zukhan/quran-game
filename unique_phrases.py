"""
Finds minimum length unique phrases in the Qur'an and indexes them by ayah 
number. Can be extended and used to quiz yourself by displaying a random unique
phrase and having to continue reciting from there (and guess which surah it's
from). 

MIN_WORDS constant can be used to set the minimum number of words you would like
in the unique phrases.

Usage: python3 unique_phrases.py
"""

MIN_WORDS = 1

with open('quran-simple-plain.txt', encoding='utf_8') as file:
    ayahs = [l.rstrip() for l in file if l.rstrip() and not l.startswith("#")]

ayah_num_to_phrases = {}
phrase_to_ayah_num = {}
non_unique_phrases = set()

# We are not currently going beyond the ayah boundaries
def unique_phrases(ayah_words, word_idx, ayah_phrases, cur_phrase, cache):
    cache_key = cur_phrase + str(word_idx)
    if cache_key in cache:
        return

    cur_phrase = cur_phrase.strip()
    if len(cur_phrase.split(" ")) >= MIN_WORDS:
        ayah_phrases.add(cur_phrase)

    if word_idx >= len(ayah_words):
        return

    cur_word = ayah_words[word_idx].strip()
    new_phrase = cur_phrase + " " + cur_word

    # Append the current word to the phrase
    unique_phrases(ayah_words, word_idx + 1, ayah_phrases, new_phrase, cache)
    # Start a new phrase with current word as the beginning of the phrase
    unique_phrases(ayah_words, word_idx + 1, ayah_phrases, cur_word, cache)

    cache.add(cache_key)

# 'ayah' has the following format:
# "1|2| الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ"
for ayah in ayahs:
    tokens = ayah.split(' ')
    surah_num = tokens[0].split('|')[0]
    ayah_num = tokens[0].split('|')[1]

    ayah_phrases = set()
    unique_phrases(tokens, 1, ayah_phrases, "", set())

    for ayah_phrase in ayah_phrases:
        if ayah_phrase in phrase_to_ayah_num:
            non_unique_phrases.add(ayah_phrase)
        else:
            phrase_to_ayah_num[ayah_phrase] = surah_num + ":" + ayah_num

# Remove duplicates
for non_uniq_phrase in non_unique_phrases:
    del phrase_to_ayah_num[non_uniq_phrase]

# Build a reverse index of unique phrases by ayah number
for phrase, ayah_num in phrase_to_ayah_num.items():
    if ayah_num not in ayah_num_to_phrases:
        ayah_num_to_phrases[ayah_num] = set()
    ayah_num_to_phrases[ayah_num].add(phrase)

# Only keep the phrases per ayah that have the fewest words
for phrases in ayah_num_to_phrases.values():
    min_phrase_words = 10000
    for phrase in phrases:
        min_phrase_words = min(min_phrase_words, len(phrase.split(" ")))

    for phrase in phrases.copy():
        if len(phrase.split(" ")) != min_phrase_words:
            phrases.remove(phrase)

# Write the output to a file
with open('min-one-word-phrases.txt', 'w', encoding='utf-8') as file:
    old_surah_num = 0
    for ayah_num, phrases in ayah_num_to_phrases.items():
        new_surah_num = ayah_num.split(':')[0]
        if new_surah_num != old_surah_num:
            file.write('\n')
            file.write('Surah ' + new_surah_num + ':\n')
            file.write('\n')
            old_surah_num = new_surah_num

        file.write(ayah_num + ' - ' + str(phrases))
        file.write('\n')
