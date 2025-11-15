import re
import os
import anthropic  # Importe le vrai SDK
import time
from typing import Dict, List

# API_KEY = os.environ.get("ANTHROPIC_API_KEY")
API_KEY = "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"

class ClaudeBatchAnalyzer:
    """
    Analyse un transcript d'entretien COMPLET (Batch) et
    retourne la liste de tous les thèmes abordés.
    """
    def __init__(self, themes: Dict[str, str], api_key: str):
        if not api_key:
            raise ValueError("Clé API Anthropic non trouvée.")
            
        self.themes = themes
        self.client = anthropic.Anthropic(api_key=api_key)

    def _build_prompt(self, full_transcript: str) -> str:
        """
        Construit le prompt pour une analyse "post-entretien".
        """
        prompt = "Tu es un assistant expert en analyse de recrutement \"Quant\".\n\n"
        
        prompt += "Voici la liste de tous les thèmes que nous suivons. Lis attentivement leur description :\n"
        prompt += "<themes_a_suivre>\n"
        for tag, description in self.themes.items():
            prompt += f"{tag}: {description}\n"
        prompt += "</themes_a_suivre>\n\n"
        
        prompt += "Voici la transcription complète d'un entretien (Recruteur et Candidat) :\n"
        prompt += "<transcription_complete>\n"
        prompt += full_transcript
        prompt += "\n</transcription_complete>\n\n"
        
        prompt += "TACHE : Analyse la transcription. Identifie TOUS les thèmes qui ont été substantiellement abordés, que ce soit par le recruteur ou le candidat.\n\n"
        prompt += "FORMAT DE RÉPONSE : Réponds *uniquement* avec une liste Python des tags des thèmes couverts. N'ajoute aucun autre texte.\n"
        prompt += "Exemple de format de réponse : ['[CV_TECHNIQUES]', '[STATIONARITY]', '[EXTRA]']"
        
        return prompt

    def _parse_response(self, response_text: str) -> List[str]:
        """
        Extrait la liste des tags de la réponse brute de Claude.
        Cette regex est robuste et trouvera tous les [TAG]
        """
        # re.findall trouve toutes les correspondances
        tags = re.findall(r"\[([A-Z_]+)\]", response_text)
        
        # Retourne les tags avec les crochets, pour rester cohérent
        return [f"[{tag}]" for tag in tags]

    def analyze_full_interview(self, transcript: str) :
        """
        Lance l'analyse complète de la transcription.
        """
        print("[INFO] Lancement de l'analyse 'Post-Entretien' (Batch)...")
        prompt = self._build_prompt(transcript)
        
        start_time = time.time()
        print("  [INFO] Appel à l'API Claude (Opus ou Sonnet recommandé)...")
        
        try:
            # -----------------------------------------------------
            # VRAI APPEL API
            # -----------------------------------------------------
            message = self.client.messages.create(
                # Pour une analyse de transcript long, Sonnet ou Opus
                # est meilleur que Haiku, car le contexte est plus large.
                model="claude-3-haiku-20240307", 
                max_tokens=1000, # On laisse de la place pour la liste
                system="Tu es un analyseur de transcript d'entretien. Réponds au format demandé.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            raw_response = message.content[0].text
            # -----------------------------------------------------
        
        except anthropic.AuthenticationError:
            print("  [ERREUR] Authentification échouée. Clé API correcte ?")
            return []
        except Exception as e:
            print(f"  [ERREUR] Erreur lors de l'appel API: {e}")
            return []
            
        end_time = time.time()
        latency = end_time - start_time
        
        print(f"  [INFO] Réponse reçue en {latency:.2f}s.")
        
        # --- Parser la réponse ---
        covered_themes = self._parse_response(raw_response)
        return covered_themes

# --- FONCTION UTILITAIRE pour formater la conversation ---

def format_conversation(dialogue: List[Dict[str, str]]) -> str:
    """Transforme la liste de dicts en un seul string lisible."""
    transcript = ""
    for turn in dialogue:
        transcript += f"{turn['speaker']}: {turn['text']}\n"
    return transcript

# --- CONFIGURATION (Test set challengeant) ---

# 1. Thèmes
challenging_themes = {
    "[CV_TECHNIQUES]": "Validation croisée, K-Fold, Walk-Forward, backtesting, robustesse out-of-sample.",
    "[REGULARIZATION]": "Régularisation L1/L2, Lasso, Ridge, prévention de l'overfitting par pénalisation des coefficients.",
    "[FEATURE_SELECTION]": "Sélection de variables, feature engineering, SHAP, LIME, PCA, importance des features.",
    "[STATIONARITY]": "Stationnarité, non-stationnarité, tests de racine unitaire (ADF, KPSS), co-intégration.",
    "[TIME_SERIES_MODELS]": "Modèles spécifiques de séries temporelles (ARIMA, GARCH, VAR), modélisation de la volatilité.",
    "[OPTIMIZATION_PYTHON]": "Performance du code Python, vectorisation, NumPy, Pandas, Numba, Cython.",
    "[LOOKAHEAD_BIAS]": "Biais \"look-ahead\", fuite de données futures, erreurs courantes de backtest.",
    "[DATA_PIPELINE]": "Nettoyage des données, ingestion, pipelines ETL, gestion des données de marché.",
    "[BEHAVIORAL_PRESSURE]": "Gestion du stress, des délais serrés, des situations de crise.",
    "[BEHAVIORAL_TEAMWORK]": "Collaboration, gestion des conflits, communication avec les PM ou les traders.",
    "[EXTRA]": "Questions hors-sujet, salutations, transitions, questions sur le poste."
}

# 2. Conversation
long_conversation_flow = [
    {"speaker": "Recruteur", "text": "Bonjour, merci de nous rejoindre. Pouvons-nous commencer ?"},
    {"speaker": "Candidat", "text": "Bonjour, oui, avec plaisir."},
    {"speaker": "Recruteur", "text": "Parfait. J'ai vu votre CV, c'est impressionnant. Pourriez-vous me parler de votre approche générale pour construire un modèle prédictif ?"},
    {"speaker": "Candidat", "text": "Bien sûr. Je commence toujours par une analyse exploratoire (EDA) poussée, puis je passe beaucoup de temps sur le feature engineering..."},
    {"speaker": "Recruteur", "text": "Justement, en parlant de features, comment décidez-vous lesquelles garder ? Si vous en avez des milliers, par exemple."},
    {"speaker": "Candidat", "text": "J'utilise une combinaison de méthodes. Des filtres simples comme la corrélation, mais surtout des méthodes 'embedded' comme la régularisation Lasso, qui est très efficace pour forcer les coefficients non-pertinents à zéro."},
    {"speaker": "Recruteur", "text": "Intéressant. Et si le Lasso pénalise trop votre modèle, quelles autres techniques de régularisation connaissez-vous ?"},
    {"speaker": "Candidat", "text": "Je pourrais utiliser Ridge (L2) si je veux garder toutes les variables, ou ElasticNet pour un mix..."},
    {"speaker": "Recruteur", "text": "D'accord. Et pour valider la robustesse de ce modèle, quelle est votre méthode de backtest préférée ?"},
    {"speaker": "Candidat", "text": "Pour des données 'cross-section', un K-Fold classique suffit. Mais pour des séries temporelles, j'utilise impérativement une validation 'walk-forward' pour respecter l'ordre chronologique."},
    {"speaker": "Recruteur", "text": "Vous avez mentionné les séries temporelles. Quelle est la toute première chose que vous vérifiez avant de modéliser ce type de données ?"},
    {"speaker": "Candidat", "text": "La stationnarité, sans aucun doute. J'utilise un test ADF ou KPSS pour vérifier la présence d'une racine unitaire."},
    {"speaker": "Recruteur", "text": "Très bien. Quels types de modèles aimez-vous utiliser pour capturer la volatilité ?"},
    {"speaker": "Candidat", "text": "Les modèles de type GARCH ou eGARCH sont le standard..."},
    {"speaker": "Recruteur", "text": "Passons à la technique. Votre script de backtest est très lent. Quelle est votre première piste d'investigation en Python ?"},
    {"speaker": "Candidat", "text": "Je cherche immédiatement les boucles 'for'. Je remplace tout par des opérations vectorisées NumPy..."},
    {"speaker": "Recruteur", "text": "Imaginez : votre modèle tourne en production, et vous découvrez que vous aviez un bug dans l'indexation des 'timestamps'. Que faites-vous ?"},
    {"speaker": "Candidat", "text": "C'est le pire scénario, un 'look-ahead bias'. J'arrête le modèle immédiatement..."},
    {"speaker": "Recruteur", "text": "Comment gérez-vous la pression quand le PM vous dit que le modèle doit être 'live' pour demain ?"},
    {"speaker": "Candidat", "text": "Je ne cède pas sur la rigueur. Je montre des preuves objectives..."},
    {"speaker": "Recruteur", "text": "Parfait, merci. Avez-vous des questions pour nous ?"},
    {"speaker": "Candidat", "text": "Oui, quelle est la taille de l'équipe data ?"}
]


# --- EXÉCUTION DE LA DÉMO ---

if not API_KEY or API_KEY == "votre_cle_api_anthropic_ici":
    print("ERREUR : Clé API non configurée.")
else:
    print("Initialisation du Moteur d'Analyse Batch...")
    engine = ClaudeBatchAnalyzer(themes=challenging_themes, api_key=API_KEY)
    
    # Formater la conversation en un seul string
    full_transcript = format_conversation(long_conversation_flow)
    
    # Lancer l'analyse
    themes_couverts = engine.analyze_full_interview(full_transcript)
    
    print("\n--- RAPPORT FINAL DES THÈMES COUVERTS ---")
    if themes_couverts:
        for theme in themes_couverts:
            print(f"  [✅] {theme}")
            
        # Bonus : Calculer le score
        total_themes = len(challenging_themes)
        # On exclut [EXTRA] du calcul de score
        total_themes_pertinents = len([t for t in challenging_themes if t != "[EXTRA]"])
        themes_couverts_pertinents = len([t for t in themes_couverts if t != "[EXTRA]"])
        
        score = (themes_couverts_pertinents / total_themes_pertinents) * 100
        print(f"\nScore de couverture (hors 'EXTRA') : {score:.2f}%")
        
    else:
        print("Aucun thème n'a pu être extrait (vérifiez les erreurs API).")