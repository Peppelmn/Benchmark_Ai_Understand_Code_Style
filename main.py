import os
import json
from AISystem import AISystem
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
            text=f"Nella definizione di una variabile nel file {spacingAnalyzer.question_S01()[0]}, quanti spazi vengono utilizzati per separare i token?"
        ),
        Question(
            id="S02",
            category="spacing",
            text=f"Nella definizione della condizione in una struttura di controllo nel file {spacingAnalyzer.question_S02()[0]}, quanti spazi vengono usati per separare i token?"
        ),
        Question(
            id="S03",
            category="spacing",
            text=f"Nelle liste di argomenti delle funzioni nel file {spacingAnalyzer.question_S03_S04("before")[0]}, quanti spazi vengono utilizzati prima della virgola?"
        ),
        Question(
            id="S04",
            category="spacing",
            text=f"Nelle liste di argomenti delle funzioni nel file {spacingAnalyzer.question_S03_S04("after")[0]}, quanti spazi vengono utilizzati dopo la virgola?"
        ),
        Question(
            id="S05",
            category="spacing",
            text=f"Nel file {spacingAnalyzer.question_S05()[0]}, quante righe vuote ci sono dopo la definizione di una funzione (incluso il corpo della funzione)?"
        ),
        Question(
            id="S06",
            category="spacing",
            text=f"Nel file {spacingAnalyzer.question_S06()[0]}, qual è la lunghezza massima di una riga di codice (esclusi i commenti e le docstring)?"
        ),
        Question(
            id="S07",
            category="spacing",
            text=f"Nel file {spacingAnalyzer.question_S07()[0]}, quanti spazi vengono utilizzati per l'indentazione del codice?"
        ),
    ]
    # Crea il sistema
    system = BenchmarkSystem(codebase_path=codebase_path)

    # Genera il benchmark
    benchmark = system.generate_benchmark(questions, output_path="benchmark.json")


    # Inizializza il sistema AI
    ai_system = AISystem(model="llama3.1", provider="ollama")
    
    # Valuta l'AI sul benchmark
    evaluation_results = ai_system.evaluate_benchmark(
        benchmark_items=system.get_benchmark_items("benchmark.json"),
        codebase_path=codebase_path,
        output_path="ai_evaluation.json"
    )
    
    print("\n=== ANALISI DETTAGLIATA ===\n")
    
    # Mostra domande sbagliate
    wrong_answers = [r for r in evaluation_results['results'] if not r['is_correct']]
    right_answers = [r for r in evaluation_results['results'] if r['is_correct']]
    
    if wrong_answers:
        print(f"Domande sbagliate ({len(wrong_answers)}):")
        for result in wrong_answers:
            print(f"\n  ID: {result['question_id']}")
            print(f"  Domanda: {result['question']}")
            print(f"  Risposta AI: {result['ai_answer']}")
            print(f"  Risposta corretta: {result['correct_label']}")
            print(f"  Risposta completa AI: {result['ai_raw_response']}")

        if right_answers:
            print(f"\nDomande corrette ({len(right_answers)}):")
            for result in right_answers:
                print(f"\n  ID: {result['question_id']}")
                print(f"  Domanda: {result['question']}")
                print(f"  Risposta AI: {result['ai_answer']}")
                print(f"  Risposta corretta: {result['correct_label']}")
                print(f"  Risposta completa AI: {result['ai_raw_response']}")

    else:
        print("✓ Tutte le risposte sono corrette!\n")
        for result in right_answers:
            print(f"\n  ID: {result['question_id']}")
            print(f"  Domanda: {result['question']}")
            print(f"  Risposta AI: {result['ai_answer']}")
            print(f"  Risposta corretta: {result['correct_label']}")
            print(f"  Risposta completa AI: {result['ai_raw_response']}")
    
    print("\n" + "="*60)
    print("Valutazione completata!")
    print("="*60)