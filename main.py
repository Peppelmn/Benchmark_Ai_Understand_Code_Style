import os
import warnings
from AISystem import AISystem
from BenchmarkSystem import BenchmarkSystem
from QuestionDefiner import get_all_questions
from Spacing.SpacingAnalyzer import SpacingAnalyzer
from Naming.NamingAnalyzer import NamingAnalyzer

warnings.filterwarnings("ignore", category=SyntaxWarning)

if __name__ == "__main__":
    codebase_path = os.path.join(os.path.dirname(__file__), "Codebase", "black-main")
    spacingAnalyzer=SpacingAnalyzer(codebase_path=codebase_path)
    namingAnalyzer=NamingAnalyzer(codebase_path=codebase_path)
    try:
        questions = get_all_questions(spacingAnalyzer, namingAnalyzer)
        print(f"File saltati (Spacing): {spacingAnalyzer.parse_error_count} (a causa di errori di sintassi)")
        print(f"File saltati (Naming):  {namingAnalyzer.parse_error_count} (a causa di errori di sintassi)")
    except Exception as e:
        print(f"Errore durante la generazione delle domande: {e}")
        exit()

    system = BenchmarkSystem(codebase_path=codebase_path)

    # Genera il benchmark
    benchmark = system.generate_benchmark(questions, output_path="benchmark.json")

    # Inizializza il sistema AI

    ai_system = AISystem(model="gemini/gemini-2.5-flash", provider="google")
    
    # Valuta l'AI sul benchmark
    evaluation_results = ai_system.evaluate_benchmark(
        benchmark_items=system.get_benchmark_items("benchmark.json"),
        codebase_path=codebase_path,
        output_path="ai_evaluation.json"
    )
    
    ai_system.print_benchmark_result(evaluation_results)