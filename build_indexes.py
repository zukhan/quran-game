'''
Reads the Qur'an from a text file, parses it, and builds indexes for efficient
lookups based on various filters (e.g. juz, surah, or ayah numbers). It stores
the JSON representation of the indexes to files to allow them to be easily 
loaded during bootstrapping of the "Guess The Surah" game without having to
perform expensive computations every time which increase the game startup time.
'''

import json

# { 1: (1:1, 2:141), 2: (2:142, 2:252), ... }
juz_num_to_ayah_range = {}

# { '1:3':'1:2', '2:1':'1:7' }
ayah_num_to_prev_ayah_num = {}

# { '1:3': 'الرَّحْمَـٰنِ الرَّحِيمِ' }
ayah_num_to_ayah = {}

# { 1: '1 Al-Fatihah', 2: '2 Al-Baqarah' }
surah_num_to_name = {}

# { 1: ['1:1', '1:2', '1:3'], 2: ['2:1'] }
surah_num_to_ayah_nums = {}

# { 110: ['الْعَالَمِينَ', 'الْحَمْدُ'] }
surah_num_to_phrases = {}

# { 'الْعَالَمِينَ' : '2:30' }
phrase_to_ayah_num = {}

basmalah = 'بِسْمِ اللَّهِ الرَّحْمَـٰنِ الرَّحِيمِ'

#
# This function populates the surah number to surah name map.
#
def populate_surah_names():
    with open("resources/surah_names.csv") as file:
        for line in file:
            tokens = line.strip().split(',')
            surah_num = int(tokens[0])
            surah_name = tokens[1].strip()
            surah_num_to_name[surah_num] = surah_name

#
# This function populates the map which defines the juz boundaries (starting
# and ending ayahs).
#
def populate_juz_maps():
    with open("resources/juz_boundaries.csv") as file:
        for line in file:
            tokens = line.strip().split(',')
            juz_num = int(tokens[0])
            ayah_range = tokens[1].split('-')

            juz_num_to_ayah_range[juz_num] = (ayah_range[0], ayah_range[1])

#
# Given an 'ayah_range' tuple (e.g. '(2:52, 3:20)') and a 'target_ayah_num'
# (e.g. '2:52'), this function determines whether the target_ayah_num is less
# than the ayah_range, within the ayah_range, or greater than the ayah_range.
#
# Returns:
#   -1 if the target ayah is less than the range
#   0 if the target ayah is within the range
#   1 if the target ayah is greater than the range
#
def compare_ayah(ayah_range, target_ayah_num):
    (start_ayah, end_ayah) = ayah_range
    surah_num = int(target_ayah_num.split(':')[0])
    ayah_num = int(target_ayah_num.split(':')[1])

    start_surah_num = int(start_ayah.split(':')[0])
    start_ayah_num = int(start_ayah.split(':')[1])

    end_surah_num = int(end_ayah.split(':')[0])
    end_ayah_num = int(end_ayah.split(':')[1])

    # target surah is less than start surah
    if surah_num < start_surah_num:
        return -1

    # target surah is greater than end surah
    if surah_num > end_surah_num:
        return 1

    # target surah is in between start and end surahs
    if surah_num > start_surah_num and surah_num < end_surah_num:
        return 0

    # target surah is equal to the starting and ending surahs
    if surah_num == start_surah_num and surah_num == end_surah_num:
        if ayah_num < start_ayah_num:
            return -1
        if ayah_num > end_ayah_num:
            return 1
        return 0

    # target surah is equal to the starting surah in the range
    if surah_num == start_surah_num:
        if ayah_num < start_ayah_num:
            return -1
        return 0

    # target surah is equal to the ending surah in the range
    if surah_num == end_surah_num:
        if ayah_num > end_ayah_num:
            return 1
        return 0

    raise Exception("There is a bug in the compare_ayah logic")

#
# Given an ayah_num (e.g. '2:210'), this function finds and returns the number
# of the juz that the ayah resides in.
#
def find_juz_num(ayah_num):
    start_idx = 1
    end_idx = 30

    while start_idx <= end_idx:
        mid_idx = (start_idx + end_idx) // 2

        res = compare_ayah(juz_num_to_ayah_range[mid_idx], ayah_num)
        if res == 0:
            return mid_idx
        if res < 0:
            end_idx = mid_idx - 1
        else:
            start_idx = mid_idx + 1

    raise Exception("There is a bug in the find_juz_num logic")

#
# For a given ayah, this function populates the 'ayah_phrases' set with all of
# the phrases in that ayah. To take an English example, for the sentence,
# "I am Sherlock", after this function executes, 'ayah_phrases' will be
# populated with the following phrases:
#
#   ["I", "am", I am", "Sherlock", "am Sherlock", "I am Sherlock"]
#
def populate_phrases(ayah_words, ayah_phrases):
    prev_phrases = []
    cur_phrases = []

    for ayah_word in ayah_words:
        cur_phrases.append(ayah_word)
        for prev_phrase in prev_phrases:
            cur_phrases.append(f"{prev_phrase} {ayah_word}")

        ayah_phrases.update(cur_phrases)
        prev_phrases = cur_phrases
        cur_phrases = []
#
# This function reads the entire Qur'an from a file and finds the minimal length
# unique phrases for each ayah and builds up lookup index maps based on various
# parameters (e.g. by juz number, surah number, ayah number, etc.)
#
def parse_quran():
    with open("resources/quran-simple-plain.txt", encoding="utf_8") as file:
        lines = [l.strip() for l in file if l.strip() and not l.startswith('#')]

    # ['مِنْ', 'إِنَّ اللَّهَ']
    non_unique_phrases = set()

    prev_ayah_num = None
    for line in lines:
        # 'line' has the following format: "1|2|الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ"
        tokens = line.split('|')
        surah_num = tokens[0]
        ayah_num = f"{surah_num}:{tokens[1]}"
        ayah = tokens[2].replace(basmalah, '').strip()
        if not ayah:
            continue
        ayah_words = ayah.split(' ')
        ayah_phrases = set()

        if not surah_num_to_ayah_nums.get(surah_num):
            surah_num_to_ayah_nums[surah_num] = []
        surah_num_to_ayah_nums[surah_num].append(ayah_num)

        ayah_num_to_ayah[ayah_num] = ayah

        populate_phrases(ayah_words, ayah_phrases)

        for ayah_phrase in ayah_phrases:
            if ayah_phrase in phrase_to_ayah_num:
                non_unique_phrases.add(ayah_phrase)
            else:
                phrase_to_ayah_num[ayah_phrase] = ayah_num

        # Do not go outside the surah boundary
        if prev_ayah_num and ayah_num.split(':')[0] == prev_ayah_num.split(':')[0]:
            ayah_num_to_prev_ayah_num[ayah_num] = prev_ayah_num
        prev_ayah_num = ayah_num

    # Remove duplicates
    for non_unique_phrase in non_unique_phrases:
        del phrase_to_ayah_num[non_unique_phrase]

    # {'2:30': 'الْعَالَمِينَ'}
    ayah_num_to_phrases = {}

    # Build reverse indexes
    for phrase, ayah_num in phrase_to_ayah_num.items():
        if ayah_num not in ayah_num_to_phrases:
            ayah_num_to_phrases[ayah_num] = set()
        ayah_num_to_phrases[ayah_num].add(phrase)

        surah_num = ayah_num.split(':')[0]
        if surah_num not in surah_num_to_phrases:
            surah_num_to_phrases[surah_num] = set()
        surah_num_to_phrases[surah_num].add(phrase)

    # Only keep the phrases per ayah that have the fewest words
    for ayah_num, phrases in ayah_num_to_phrases.items():
        min_words = 10000
        for phrase in phrases:
            min_words = min(min_words, len(phrase.split(' ')))

        surah_num = ayah_num.split(':')[0]
        for phrase in phrases:
            if len(phrase.split(' ')) != min_words:
                del phrase_to_ayah_num[phrase]
                surah_num_to_phrases[surah_num].remove(phrase)

#
# json.dumps(...) does not handle sets without a custom encoder
#
class SetEncoder(json.JSONEncoder):
    def default(self, obj):
       if isinstance(obj, set):
          return sorted(list(obj))
       return json.JSONEncoder.default(self, obj)

#
# Building up the indexes every time is expensive. Build them once,
# save them to files and just deserialize the files for subsequent
# game invocations.
#
def dump_lookup_maps_to_file():
    dir = "resources/indexes"

    with open(f"{dir}/juz_num_to_ayah_range.json", 'w') as file:
        file.write(json.dumps(juz_num_to_ayah_range, indent=2))

    with open(f"{dir}/ayah_num_to_prev_ayah_num.json", 'w') as file:
        file.write(json.dumps(ayah_num_to_prev_ayah_num, indent=2))

    with open(f"{dir}/surah_num_to_ayah_nums.json", 'w') as file:
        file.write(json.dumps(surah_num_to_ayah_nums, indent=2))

    with open(f"{dir}/ayah_num_to_ayah.json", 'w') as file:
        file.write(json.dumps(ayah_num_to_ayah, ensure_ascii=False, indent=2))

    with open(f"{dir}/surah_num_to_name.json", 'w') as file:
        file.write(json.dumps(surah_num_to_name, indent=2))

    with open(f"{dir}/surah_num_to_phrases.json", 'w') as file:
        file.write(json.dumps(surah_num_to_phrases, cls=SetEncoder, ensure_ascii=False, indent=2))

    with open(f"{dir}/phrase_to_ayah_num.json", 'w') as file:
        sorted_phrase_to_ayah_num = dict(sorted(phrase_to_ayah_num.items()))
        file.write(json.dumps(sorted_phrase_to_ayah_num, ensure_ascii=False, indent=2))

populate_surah_names()
populate_juz_maps()
parse_quran()
dump_lookup_maps_to_file()
