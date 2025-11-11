import os
import warnings
from AISystem import AISystem
from BenchmarkSystem import BenchmarkSystem
from DataClassesDefiner import Question
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

    # # Inizializza il sistema AI
    # ai_system = AISystem(model="gemini/gemini-2.5-flash", provider="google")
    
    # # Valuta l'AI sul benchmark
    # evaluation_results = ai_system.evaluate_benchmark(
    #     benchmark_items=system.get_benchmark_items("benchmark.json"),
    #     codebase_path=codebase_path,
    #     output_path="ai_evaluation.json"
    # )
    
    # print("\n=== ANALISI DETTAGLIATA ===\n")
    
    # # Mostra domande sbagliate
    # wrong_answers = [r for r in evaluation_results['results'] if not r['is_correct']]
    # right_answers = [r for r in evaluation_results['results'] if r['is_correct']]
    
    # if wrong_answers:
    #     print(f"Domande sbagliate ({len(wrong_answers)}):")
    #     for result in wrong_answers:
    #         print(f"\n  ID: {result['question_id']}")
    #         print(f"  Domanda: {result['question']}")
    #         print(f"  Risposta AI: {result['ai_answer']}")
    #         print(f"  Risposta corretta: {result['correct_label']}")
    #         print(f"  Risposta completa AI: {result['ai_raw_response']}")

    #     if right_answers:
    #         print(f"\nDomande corrette ({len(right_answers)}):")
    #         for result in right_answers:
    #             print(f"\n  ID: {result['question_id']}")
    #             print(f"  Domanda: {result['question']}")
    #             print(f"  Risposta AI: {result['ai_answer']}")
    #             print(f"  Risposta corretta: {result['correct_label']}")
    #             print(f"  Risposta completa AI: {result['ai_raw_response']}")

    # else:
    #     print("✓ Tutte le risposte sono corrette!\n")
    #     for result in right_answers:
    #         print(f"\n  ID: {result['question_id']}")
    #         print(f"  Domanda: {result['question']}")
    #         print(f"  Risposta AI: {result['ai_answer']}")
    #         print(f"  Risposta corretta: {result['correct_label']}")
    #         print(f"  Risposta completa AI: {result['ai_raw_response']}")
    
    # print("\n" + "="*60)
    # print("Valutazione completata!")
    # print("="*60)