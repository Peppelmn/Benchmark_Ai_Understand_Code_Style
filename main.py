import os
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
            text=f"Nella definizione di una variabile quanti spazi vengono utilizzati per separare i token?",
            target_file=spacingAnalyzer.question_S01()[0]
        ),
        Question(
            id="S02",
            category="spacing",
            text=f"Nella definizione della condizione in una struttura di controllo, quanti spazi vengono usati per separare i token?",
            target_file=spacingAnalyzer.question_S02()[0]
        ),
        Question(
            id="S03",
            category="spacing",
            text=f"Nelle liste di argomenti delle funzioni, quanti spazi vengono utilizzati prima della virgola?",
            target_file=spacingAnalyzer.question_S03_S04("before")[0]
        ),
        Question(
            id="S04",
            category="spacing",
            text=f"Nelle liste di argomenti delle funzioni, quanti spazi vengono utilizzati dopo la virgola?",
            target_file=spacingAnalyzer.question_S03_S04("after")[0]
        ),
        Question(
            id="S05",
            category="spacing",
            text=f"Quante righe vuote ci sono dopo la definizione di una funzione?",
            target_file=spacingAnalyzer.question_S05()[0]
        ),
        Question(
            id="S06",
            category="spacing",
            text=f"Qual è la lunghezza massima di una riga di codice (esclusi i commenti e le docstring)?",
            target_file=spacingAnalyzer.question_S06()[0]
        ),
        Question(
            id="S07",
            category="spacing",
            text=f"Quanti spazi vengono utilizzati per l'indentazione del codice?",
            target_file=spacingAnalyzer.question_S07()[0]
        ),
        Question(
            id="S08",
            category="spacing",
            text=f"Quante righe vuote ci sono sopra un commento?",
            target_file=spacingAnalyzer.question_S08_S09("above")[0]
        ),
        Question(
            id="S09",
            category="spacing",
            text=f"Quante righe vuote ci sono dopo un commento?",
            target_file=spacingAnalyzer.question_S08_S09("below")[0]
        ),
        Question(
            id="S10",
            category="spacing",
            text=f"Quante righe vuote ci sono dopo ogni import o blocco di import?",
            target_file=spacingAnalyzer.question_S10()[0]
        ),
        Question(
            id="S11",
            category="spacing",
            text=f"Quante righe vuote ci sono dopo la definizione di una classe?",
            target_file=spacingAnalyzer.question_S11()[0]
        ),
        Question(
            id="S12",
            category="spacing",
            text=f"Quante righe vuote ci sono dopo la definizione di una costante o di un blocco di costanti?",
            target_file=spacingAnalyzer.question_S12()[0]
        ),
    ]
    # Crea il sistema
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