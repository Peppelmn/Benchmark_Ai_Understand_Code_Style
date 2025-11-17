import random
from typing import List
from DistractorGenerator import DistractorGenerator
from DataClassesDefiner import Question, Answer

class NamingDistractorGenerator(DistractorGenerator):
    """Genera distrattori per domande sul naming"""
    
    def generate(self, correct_answer: Answer, question: Question, num_distractors: int = 3) -> List[Answer]:
        if any(question.id.__eq__(id) for id in ["N01", "N02", "N03", "N07", "N09"]):
            return self.generate_distractors(float(correct_answer.text), num_distractors, question.id)
        elif any(question.id.__eq__(id) for id in ["N04", "N05"]):
            return self.generate_distractors_naming_convention(correct_answer.text, num_distractors=2)
        elif any(question.id.__eq__(id) for id in ["N06", "N08"]):
            return self.generate_distractors_boolean(str(correct_answer.text).lower() == 'true')

    def generate_distractors(self, correct_value: float, num_distractors: int, question_id: str=None) -> List[Answer]:
        distractors = list()
        while len(distractors) < num_distractors:
            # Genera un distrattore casuale vicino al valore corretto
            perturbation = random.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5])
            distractor_value = correct_value + perturbation
            if (distractor_value >= 0 if question_id != "N09" else distractor_value > 0) \
                and distractor_value != correct_value \
                and all(float(d.text) != float(distractor_value) for d in distractors):
                distractors.append(Answer(float(distractor_value), False))
        return distractors
    
    def generate_distractors_naming_convention(self, correct_value: str, num_distractors: int) -> List[Answer]:
        distractors = list()
        for convention in ["snake_case", "camelCase", "PascalCase"]:
            if convention != correct_value:
                distractors.append(Answer(convention, False))
                if len(distractors) == num_distractors:
                    return distractors
                
    def generate_distractors_boolean(self, correct_value: bool) -> List[Answer]:
        distractors = []
        distractor_value = not correct_value
        distractors.append(Answer(str(distractor_value).lower(), False))
        return distractors