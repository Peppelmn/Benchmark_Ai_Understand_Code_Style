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
    
    return [
        Question(
            id="S01",
            category="spacing",
            text=f"Nella definizione di una variabile quanti spazi vengono utilizzati per separare i token?",
            target_file=data_map['S01'][0],
            correct_answer_value=data_map['S01'][1]
        ),
        Question(
            id="S02",
            category="spacing",
            text=f"Nella definizione della condizione in una struttura di controllo, quanti spazi vengono usati per separare i token?",
            target_file=data_map['S02'][0],
            correct_answer_value=data_map['S02'][1]
        ),
        Question(
            id="S03",
            category="spacing",
            text=f"Nelle liste di argomenti delle funzioni, quanti spazi vengono utilizzati prima della virgola?",
            target_file=data_map['S03'][0],
            correct_answer_value=data_map['S03'][1]
        ),
        Question(
            id="S04",
            category="spacing",
            text=f"Nelle liste di argomenti delle funzioni, quanti spazi vengono utilizzati dopo la virgola?",
            target_file=data_map['S04'][0],
            correct_answer_value=data_map['S04'][1]
        ),
        Question(
            id="S05",
            category="spacing",
            text=f"Quante righe vuote ci sono dopo la definizione di una funzione?",
            target_file=data_map['S05'][0],
            correct_answer_value=data_map['S05'][1]
        ),
        Question(
            id="S06",
            category="spacing",
            text=f"Qual è la lunghezza massima di una riga di codice (esclusi i commenti e le docstring)?",
            target_file=data_map['S06'][0],
            correct_answer_value=data_map['S06'][1] 
        ),
        Question(
            id="S07",
            category="spacing",
            text=f"Quanti spazi vengono utilizzati per l'indentazione del codice?",
            target_file=data_map['S07'][0],
            correct_answer_value=data_map['S07'][1]
        ),
        Question(
            id="S08",
            category="spacing",
            text=f"Quante righe vuote ci sono sopra un commento?",
            target_file=data_map['S08'][0],
            correct_answer_value=data_map['S08'][1]
        ),
        Question(
            id="S09",
            category="spacing",
            text=f"Quante righe vuote ci sono dopo un commento?",
            target_file=data_map['S09'][0],
            correct_answer_value=data_map['S09'][1]
        ),
        Question(
            id="S10",
            category="spacing",
            text=f"Quante righe vuote ci sono dopo ogni import o blocco di import?",
            target_file=data_map['S10'][0],
            correct_answer_value=data_map['S10'][1]
        ),
        Question(
            id="S11",
            category="spacing",
            text=f"Quante righe vuote ci sono dopo la definizione di una classe?",
            target_file=data_map['S11'][0],
            correct_answer_value=data_map['S11'][1]
        ),
        Question(
            id="S12",
            category="spacing",
            text=f"Quante righe vuote ci sono dopo la definizione di una costante o di un blocco di costanti?",
            target_file=data_map['S12'][0],
            correct_answer_value=data_map['S12'][1]
        ),
        Question(
            id="N01",
            category="naming",
            text=f"Quanti elementi sono nominati usando la convenzione snake_case?",
            target_file=data_map['N01'][0],
            correct_answer_value=data_map['N01'][1]
        ),
        Question(
            id="N02",
            category="naming",
            text=f"Quanti elementi sono nominati usando la convenzione camelCase?",
            target_file=data_map['N02'][0],
            correct_answer_value=data_map['N02'][1]
        ),
        Question(
            id="N03",
            category="naming",
            text=f"Quanti elementi sono nominati usando la convenzione PascalCase?",
            target_file=data_map['N03'][0],
            correct_answer_value=data_map['N03'][1]
        ),
        Question(
            id="N04",
            category="naming",
            text=f"Qual è la convenzione più utilizzata per nominare gli elementi di questo script?",
            target_file=data_map['N04'][0],
            correct_answer_value=data_map['N04'][1]
        ),
        Question(
            id="N05",
            category="naming",
            text=f"Quale convenzione di denominazione è stata utilizzata in questo caso: {data_map['N05'][2]}?",
            target_file=data_map['N05'][0],
            correct_answer_value=data_map['N05'][1]
        ),
        Question(
            id="N06",
            category="naming",
            text=f"In questo caso: {data_map['N06'][2]}, è stata utilizzata una delle seguenti convenzioni di denominazione: snake_case, camelCase, PascalCase?",
            target_file=data_map['N06'][0],
            correct_answer_value=data_map['N06'][1]
        ),
        Question(
            id="N07",
            category="naming",
            text=f"Quanti elementi non utilizzano una delle seguenti convenzioni di denominazione: snake_case, camelCase, PascalCase?",
            target_file=data_map['N07'][0],
            correct_answer_value=data_map['N07'][1]
        ),
        Question(
            id="N08",
            category="naming",
            text=f"Nel caso della costante: {data_map['N08'][2]}, è stato utilizzato un underscore?",
            target_file=data_map['N08'][0],
            correct_answer_value=data_map['N08'][1]
        ),
        Question(
            id="N09",
            category="naming",
            text=f"Qual è la lunghezza del nome più lungo trovato nel file?",
            target_file=data_map['N09'][0],
            correct_answer_value=data_map['N09'][1]
        ),
    ]