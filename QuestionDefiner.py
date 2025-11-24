import re
from DataClassesDefiner import Question
from Spacing.SpacingAnalyzer import SpacingAnalyzer 
from Naming.NamingAnalyzer import NamingAnalyzer
from typing import List, Dict, Any

def get_all_questions(spacingAnalyzer: SpacingAnalyzer = None, namingAnalyzer: NamingAnalyzer = None) -> List[Question]:
    """
    Genera la lista di tutte le domande di spacing e naming,
    eseguendo il pre-calcolo dei dati necessari.
    """
    data_map: Dict[str, Any] = {}
    print("Pre-calcolo delle domande...")

    try:
        # Trova e chiama automaticamente tutti i metodi question_...
        
        analyzers = [spacingAnalyzer, namingAnalyzer]
        
        for analyzer in analyzers:
            # Itera su tutti gli attributi dell'oggetto analyzer
            for method_name in dir(analyzer):
                
                # Salta se non è un metodo-domanda O se è uno che abbiamo già gestito
                if not method_name.startswith("question_"):
                    continue
                
                # Estrai l'ID dal nome del metodo
                # Es: "question_S01" -> "S01"
                # Es: "question_N01" -> "N01"
                # Usiamo un'espressione regolare per essere sicuri
                match = re.search(r"question_([SN]\d+)$", method_name)
                
                if not match:
                    # Salta metodi che non corrispondono (es. helper)
                    continue

                question_id = match.group(1) # Es. "S01"

                # Prendi la funzione vera e propria dall'oggetto
                method_to_call = getattr(analyzer, method_name)
                
                # Eseguila (senza argomenti)
                result = method_to_call()
                
                # Salva il risultato nel dizionario
                data_map[question_id] = result
                # print(f"  -> Trovato e aggiunto dinamicamente: {question_id}")

        if any(data is None for data in data_map.values()):
            # Trova quali chiavi sono None per un debug migliore
            failed_keys = [k for k, v in data_map.items() if v is None]
            raise ValueError(f"Uno o più analyzer non hanno trovato file consistenti: {failed_keys}")
            
    except Exception as e:
        print(f"Errore fatale durante la pre-analisi (in get_all_questions): {e}")
        raise e 
    
    print("Dati pre-calcolati con successo.")

    questions = []

    # Loop generico per creare le Question dagli oggetti in data_map
    # Definiamo i template di testo manualmente
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
        if not results_list: continue # Salta se vuoto
        
        template = templates.get(q_id, "Domanda generica...")
        category = "spacing" if q_id.startswith("S") else "naming"
        
        # Estraiamo le liste parallele
        target_files = [r[0] for r in results_list]
        correct_answers = [r[1] for r in results_list]
        
        # Gestione dati extra (es. N06, N08, N09 hanno 3 elementi nella tupla)
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