import csv

# 誤認しやすい文字の変換テーブル
ocr_conversion = str.maketrans(
    "がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽ"
    "ガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポ"
    "シソぁぃぅぇぉゎっゃゅょァィゥェォヮッャュョ"
    "三一－-",
    "かきくけこさしすせそたちつてとはひふへほはひふへほ"
    "カキクケコサツスセソタチツテトハヒフヘホハヒフヘホ"
    "ツンあいうえおわつやゆよアイウエオワツヤユヨ"
    "二ーーー",
    "゛゜！!？?～~、。.　 ♡："
)

def convert_ocr_string(text):
    text = text.translate(ocr_conversion)
    return text

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def calculate_similarity(s1, s2):
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    similarity = (max_len - distance) / max_len
    return similarity * 100

class CharaSkill:
    file_path = 'resources/skill.tsv'

    char_data : dict 
    
    def from_tsv():
        chara_skills = dict()
        with open(CharaSkill.file_path, 'r', encoding='utf-8') as file:
            for line in csv.reader(file, delimiter= '\t'):
                if len(line) < 2:
                    continue
                chara_name = line[0]
                skill_name = line[1]
                skill_detail = line[2] if len(line) > 2 else ''
                chara_skills[chara_name] =  (skill_name, skill_detail)
        return chara_skills
    
    @classmethod
    def find_best_match(cls, chara_skills: dict, query_skill: str, threshold: int = 20):
        if query_skill == '':
            return None, 0

        best_match = None
        highest_similarity = 0
        query_skill = convert_ocr_string(query_skill)

        for chara_name, chara_skill in chara_skills.items():
            similarity = calculate_similarity(chara_skill[0], query_skill)
            if similarity > highest_similarity and similarity >= threshold:
                highest_similarity = similarity
                best_match = chara_name

        return best_match, highest_similarity

