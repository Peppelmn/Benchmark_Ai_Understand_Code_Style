import re
from DataClassesDefiner import Question
from Spacing.SpacingAnalyzer import SpacingAnalyzer 
from Naming.NamingAnalyzer import NamingAnalyzer
from typing import List, Dict, Any

def get_all_questions(spacingAnalyzer: SpacingAnalyzer = None, namingAnalyzer: NamingAnalyzer = None) -> List[Question]:
    """
    Generates a comprehensive list of benchmark questions by dynamically invoking analysis methods 
    from the provided analyzer instances.

    This function performs a pre-calculation step where it:
    1. Inspects the provided analyzers (Spacing and Naming).
    2. Dynamically finds and executes all methods starting with "question_" (e.g., question_S01, question_N05).
    3. Collects the ground truth data (target files, correct answers, extra context) returned by these methods.
    4. Maps the results to specific text templates to construct formal `Question` objects.

    Args:
        spacingAnalyzer (SpacingAnalyzer, optional): An instance of the spacing analyzer. Defaults to None.
        namingAnalyzer (NamingAnalyzer, optional): An instance of the naming analyzer. Defaults to None.

    Returns:
        List[Question]: A list of populated Question objects ready for benchmark generation.

    Raises:
        ValueError: If any analyzer method returns None (indicating a failure to find consistent data).
        Exception: For any fatal errors during the dynamic method invocation.
    """
    data_map: Dict[str, Any] = {}
    print("Pre-calcolo delle domande...")

    try:
        
        analyzers = [spacingAnalyzer, namingAnalyzer]
        
        for analyzer in analyzers:
            for method_name in dir(analyzer):
                
                if not method_name.startswith("question_"):
                    continue
                
                match = re.search(r"question_([SN]\d+)$", method_name)
                
                if not match:
                    continue

                question_id = match.group(1)
                method_to_call = getattr(analyzer, method_name)
                result = method_to_call()
                data_map[question_id] = result

        if any(data is None for data in data_map.values()):
            failed_keys = [k for k, v in data_map.items() if v is None]
            raise ValueError(f"Uno o più analyzer non hanno trovato file consistenti: {failed_keys}")
            
    except Exception as e:
        print(f"Errore fatale durante la pre-analisi (in get_all_questions): {e}")
        raise e 
    
    print("Dati pre-calcolati con successo.")

    questions = []
    templates = {
        "S01": "Nella definizione di una variabile nel file, quanti spazi vengono utilizzati per separare i token?",
        "S02": "Nella definizione della condizione in una struttura di controllo, quanti spazi vengono usati per separare i token?",
        "S03": "Nelle liste di argomenti delle funzioni, quanti spazi vengono utilizzati prima della virgola?",
        "S04": "Nelle liste di argomenti delle funzioni, quanti spazi vengono utilizzati dopo la virgola?",
        "S05": "Quante righe vuote ci sono dopo la definizione di una funzione?",
        "S06": "Qual è la lunghezza massima di una riga di codice (esclusi i commenti e le docstring)?",
        "S07": "Quanti spazi vengono utilizzati per l'indentazione del codice?",
        "S08": "Quante righe vuote ci sono prima di un commento?",
        "S09": "Quante righe vuote ci sono dopo un commento?",
        "S10": "Quante righe vuote ci sono dopo ogni import o blocco di import?",
        "S11": "Quante righe vuote ci sono dopo la definizione di una classe?",
        "S12": "Quante righe vuote ci sono dopo la definizione di una costante o di un blocco di costanti?",
        "S13": "Osservando questa parte di codice: \n\n{0}\n\n, quale delle seguenti strategie di spaziatura degli argomenti viene utilizzata?",
        "N01": "Quanti nomi 'snake_case' sono presenti in questo file?",
        "N02": "Quanti nomi 'camelCase' sono presenti in questo file?",
        "N03": "Quanti nomi 'PascalCase' sono presenti in questo file?",
        "N04": "Qual è la convenzione di naming più utilizzata in questo file?",
        "N05": "Quale convenzione di naming è stata utilizzata per il nome '{0}'?",
        "N06": "Il nome '{0}' segue una convenzione di naming standard (snake_case, camelCase, o PascalCase)?",
        "N07": "Quanti nomi non seguono una convenzione di naming standard (snake_case, camelCase, o PascalCase)?",
        "N08": "Il nome della costante '{0}' utilizza un underscore?",
        "N09": "Qual è la lunghezza del nome più lungo trovato nel file?",
    }

    for q_id, results_list in data_map.items():
        if not results_list: continue
        
        template = templates.get(q_id, "Domanda generica...")
        category = "spacing" if q_id.startswith("S") else "naming"

        target_files = [r[0] for r in results_list]
        correct_answers = [r[1] for r in results_list]
        
        extra_data = None
        if len(results_list[0]) > 2:
            extra_data = [r[2] for r in results_list]

        questions.append(Question(
            id=q_id,
            category=category,
            text_template=template,
            target_files=target_files,
            correct_answer_values=correct_answers,
            extra_data=extra_data
        ))

    return questions