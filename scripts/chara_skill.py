from typing import List
from scripts.common_utils import convert_ocr_string
from scripts.common_utils import calculate_similarity
import csv
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
    def find_best_match(cls, chara_skills: dict, query_skill: str, threshold: int = 50):
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

