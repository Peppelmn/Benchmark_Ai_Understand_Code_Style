import random
from typing import List
from DistractorGenerator import DistractorGenerator
from DataClassesDefiner import Question, Answer

class NamingDistractorGenerator(DistractorGenerator):
    """
    Specialized distractor generator for naming-related questions.
    """
    
    def generate(self, correct_answer: Answer, question: Question, num_distractors: int = 3) -> List[Answer]:
        """
        Orchestrates the generation of distractors by selecting the appropriate strategy (numeric, convention string, or boolean) based on the specific naming question ID.

        Args:
            correct_answer (Answer): The correct answer object containing the ground truth.
            question (Question): The question object containing the ID (e.g., "N01").
            num_distractors (int): The number of wrong answers to generate.

        Returns: A list of Answer objects representing the distractors.
        """
        if any(question.id.__eq__(id) for id in ["N01", "N02", "N03", "N07", "N09"]):
            return self.generate_distractors(float(correct_answer.text), num_distractors, question.id)
        elif any(question.id.__eq__(id) for id in ["N04", "N05"]):
            return self.generate_distractors_naming_convention(correct_answer.text, num_distractors=2)
        elif any(question.id.__eq__(id) for id in ["N06", "N08"]):
            return self.generate_distractors_boolean(str(correct_answer.text).lower() == 'true')

    def generate_distractors(self, correct_value: float, num_distractors: int, question_id: str=None) -> List[Answer]:
        """
        Generates numeric distractors by applying random perturbations to the correct value, ensuring validity (non-negative) and uniqueness.

        Args:
            correct_value (float): The correct numeric value.
            num_distractors (int): The number of distractors to generate.
            question_id (str): The ID of the question, used for specific validation logic (e.g., N09 > 0).

        Returns: A list of Answer objects with incorrect numeric values.
        """
        distractors = list()
        while len(distractors) < num_distractors:
            perturbation = random.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5])
            distractor_value = correct_value + perturbation
            if (distractor_value >= 0 if question_id != "N09" else distractor_value > 0) \
                and distractor_value != correct_value \
                and all(float(d.text) != float(distractor_value) for d in distractors):
                distractors.append(Answer(float(distractor_value), False))
        return distractors
    
    def generate_distractors_naming_convention(self, correct_value: str, num_distractors: int) -> List[Answer]:
        """
        Selects incorrect naming convention strings (e.g., snake_case, camelCase) from a predefined list to serve as distractors.

        Args:
            correct_value (str): The string representing the correct convention.
            num_distractors (int): The number of distractors to generate.

        Returns: A list of Answer objects with incorrect convention strings.
        """
        distractors = list()
        for convention in ["snake_case", "camelCase", "PascalCase"]:
            if convention != correct_value:
                distractors.append(Answer(convention, False))
                if len(distractors) == num_distractors:
                    return distractors
                
    def generate_distractors_boolean(self, correct_value: bool) -> List[Answer]:
        """
        Generates the logical opposite of the correct boolean value as a distractor.

        Args:
            correct_value (bool): The correct boolean value.

        Returns: A list containing a single Answer object with the opposite boolean value.
        """
        distractors = []
        distractor_value = not correct_value
        distractors.append(Answer(str(distractor_value).lower(), False))
        return distractors