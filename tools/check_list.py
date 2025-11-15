import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# --- Le Moteur de Suivi ---

class InterviewTracker:
    def __init__(self, question_bank, model, threshold=0.70):
        self.bank = question_bank
        self.model = model
        self.threshold = threshold
        
        # 1. Pré-calculer les vecteurs de la banque
        self.bank_vectors = self.model.encode(self.bank)
        
        # 2. Initialiser le suivi (état)
        self.covered_status = [False] * len(self.bank)
        self.extra_questions = []

    def process_recruiter_question(self, question_text):
        """
        Analyse une question du recruteur et la classe.
        """
        print(f"\n[Recruteur] : \"{question_text}\"")
        
        # 3. Vectoriser la nouvelle question
        question_vector = self.model.encode([question_text])
        
        # 4. Calculer les scores
        scores = cosine_similarity(question_vector, self.bank_vectors)[0]
        
        best_match_index = np.argmax(scores)
        best_score = scores[best_match_index]
        
        # 5. Appliquer la logique du seuil
        if best_score >= self.threshold:
            # Le sujet est assez proche
            
            # On vérifie s'il était déjà coché
            if not self.covered_status[best_match_index]:
                print(f"  ➡️ COCHÉ (Sujet : '{self.bank[best_match_index]}')")
                self.covered_status[best_match_index] = True
            else:
                print(f"  ➡️ DÉJÀ COCHÉ (Sujet : '{self.bank[best_match_index]}')")
        
        else:
            # Le sujet n'est pas dans la banque
            print(f"  ➡️ SUJET 'EXTRA' (Score max : {best_score:.2f})")
            self.extra_questions.append(question_text)

    def get_coverage_report(self):
        """
        Affiche le rapport final de couverture.
        """
        print("\n--- RAPPORT DE COUVERTURE FINAL ---")
        covered_count = 0
        for i, question in enumerate(self.bank):
            if self.covered_status[i]:
                print(f"[✅] {question}")
                covered_count += 1
            else:
                print(f"[❌] {question}")
        
        score = (covered_count / len(self.bank)) * 100
        print(f"\nScore de couverture : {score:.2f}%")
        
        if self.extra_questions:
            print("\nQuestions 'Extra' posées :")
            for q in self.extra_questions:
                print(f"  - \"{q}\"")

# --- 3. EXEMPLE DE FLUX DE DIALOGUE ---

# --- Setup (à faire une fois) ---
question_bank = [
    "Comment vous assurez-vous qu'un modèle n'est pas en sur-apprentissage (overfitting) ?",
    "Expliquez le concept de stationnarité et son importance.",
    "Comment sélectionnez-vous les 'features' (variables) pour un modèle prédictif ?"
]

# Charger le modèle
print("Chargement du modèle...")
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print("Modèle chargé.")

# Initialiser le tracker
tracker = InterviewTracker(question_bank, model, threshold=0.50)

# --- Déroulé de l'entretien (simulé) ---

# On ne traite que les questions du recruteur
dialogue = [
    {"speaker": "Recruteur", "text": "Bienvenue. Pour commencer, parlez-moi de vous."},
    {"speaker": "Candidat", "text": "Bonjour, j'ai 5 ans d'expérience en..."},
    {"speaker": "Recruteur", "text": "Intéressant. Sur vos projets, comment vous évitez le sur-apprentissage ?"},
    {"speaker": "Candidat", "text": "J'utilise beaucoup de cross-validation et un set 'out-of-sample'..."},
    {"speaker": "Recruteur", "text": "D'accord. Et pour les séries temporelles, que pensez-vous de la stationnarité ?"},
    {"speaker": "Candidat", "text": "C'est la base. Sans ça, les régressions sont fallacieuses..."},
    {"speaker": "Recruteur", "text": "Quelle est votre couleur préférée ?"},
    {"speaker": "Candidat", "text": "Euh... le bleu ?"},
    {"speaker": "Recruteur", "text": "Très bien. Et comment vous gérez l'overfitting, par exemple avec les hyperparamètres ?"},
]

# Traitement du flux
for utterance in dialogue:
    if utterance["speaker"] == "Recruteur":
        tracker.process_recruiter_question(utterance["text"])

# Afficher le rapport final
tracker.get_coverage_report()