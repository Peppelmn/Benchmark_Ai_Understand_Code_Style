import json
from typing import Dict

from pyparsing import List
from DistractorGenerator import DistractorGenerator
from CodebaseAnalyzer import CodebaseAnalyzer
from Naming.NamingAnalyzer import NamingAnalyzer
from Spacing.SpacingAnalyzer import SpacingAnalyzer
from DataClassesDefiner import Answer, Question, BenchmarkItem
from Naming.NamingDistractorGenerator import NamingDistractorGenerator
from Spacing.SpacingDistractorGenerator import SpacingDistractorGenerator

class BenchmarkSystem:
    """
    Core system responsible for generating, managing, and retrieving benchmark items.
    It orchestrates the interaction between Question definitions, Distractor Generators,
    and the final JSON output structure.
    """    
    def __init__(self, codebase_path: str):
        """
        Initializes the BenchmarkSystem and registers the necessary distractor generators.

        Args:
            codebase_path (str): The root path to the codebase being analyzed.
        """
        self.codebase_path = codebase_path
        
        self.distractor_generators: Dict[str, DistractorGenerator] = {
            "naming": NamingDistractorGenerator(),
            "spacing": SpacingDistractorGenerator(),
        }
    
    def process_question(self, question: Question) -> BenchmarkItem:
        """
        Processes a single Question object to generate a complete BenchmarkItem,
        including the correct answer and valid distractors.

        Args:
            question (Question): The abstract question definition.

        Returns:
            BenchmarkItem: A fully constructed item ready for the benchmark.

        Raises:
            ValueError: If no distractor generator is found for the question's category.
        """
        
        correct_answer = Answer(question.correct_answer_value, True)
        
        generator = self.distractor_generators.get(question.category)
        if not generator:
            raise ValueError(f"Generator non trovato: {question.category}")
        
        distractors = generator.generate(correct_answer, question)
        
        return BenchmarkItem(
            question=question,
            correct_answer=correct_answer,
            distractors=distractors
        )

    def generate_benchmark(self, questions: List[Question], output_path: str = None) -> List[Dict]:
        """
        Generates the full benchmark dataset by expanding abstract Questions into specific items for each target file.
        
        For each question in the input list, this method iterates through its associated target files (e.g., 10 files per question type),
        creates specific question instances with context (e.g., formatting variable names), generates distractors, and optionally saves the result to a JSON file.

        Args:
            questions (List[Question]): A list of Question objects populated with analysis data (target files and correct answers).
            output_path (str, optional): The file path where the generated benchmark JSON should be saved.

        Returns:
            List[Dict]: A list of dictionaries representing the generated benchmark items.
        """
        benchmark_items = []
        
        for q in questions:
            for i, target_file in enumerate(q.target_files):
                try:
                    if q.extra_data:
                        formatted_text = q.text_template.format(q.extra_data[i])
                    else:
                        formatted_text = q.text_template

                    correct_val = q.correct_answer_values[i]
                    correct_answer_obj = Answer(correct_val, True)

                    proxy_q = Question(
                        id=q.id, category=q.category, text_template=formatted_text,
                        target_files=[target_file], correct_answer_values=[correct_val]
                    )
                    
                    generator = self.distractor_generators.get(q.category)
                    distractors = generator.generate(correct_answer_obj, proxy_q)
                    
                    if distractors is None: distractors = []

                    single_file_q = Question(
                        id=f"{q.id}_{i+1}",
                        category=q.category,
                        text_template=formatted_text,
                        target_files=[target_file],
                        correct_answer_values=[correct_val]
                    )

                    item = BenchmarkItem(
                        question=single_file_q,
                        correct_answer=correct_answer_obj,
                        distractors=distractors
                    )
                    
                    item_dict = item.to_dict()
                    item_dict["target_file"] = target_file
                    item_dict["question_template"] = q.text_template.format("choosen_item") if q.extra_data else q.text_template
                    item_dict["choosen_item"] = q.extra_data[i] if q.extra_data else None
                    
                    benchmark_items.append(item_dict)

                except Exception as e:
                    print(f"Errore generando item {q.id}_{i+1}: {e}")

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(benchmark_items, f, indent=2, ensure_ascii=False)

        return benchmark_items
        
    def get_benchmark_items(self, benchmark_path: str) -> List[Dict]:
        """
        Loads an existing benchmark dataset from a JSON file.

        Args:
            benchmark_path (str): The path to the benchmark JSON file.

        Returns:
            List[Dict]: The list of benchmark items loaded from the file.
        """
        with open(benchmark_path, 'r', encoding='utf-8') as f:
            benchmark_items = json.load(f)
        return benchmark_items