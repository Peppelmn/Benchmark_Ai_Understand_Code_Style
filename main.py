import os
from BenchmarkSystem import BenchmarkSystem
from DataClassesDefiner import Question
from Spacing.SpacingAnalyzer import SpacingAnalyzer


if __name__ == "__main__":
    
    codebase_path = os.path.join(os.path.dirname(__file__), "Codebase", "black-main")
    spacingAnalyzer=SpacingAnalyzer(codebase_path=codebase_path)
    # Definisci le tue domande
    questions = [
        Question(
            id="S01",
            category="spacing",
            text=f"Nella definizione di una variabile nel file {spacingAnalyzer.question_S01()[0]} della codebase, quanti spazi vengono utilizzati per separare i token?"
        ),
    ]

    # Crea il sistema
    system = BenchmarkSystem(codebase_path=codebase_path)

    # Genera il benchmark
    benchmark = system.generate_benchmark(questions, output_path="benchmark.json")