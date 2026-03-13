import re
from dataclasses import dataclass
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import ALPHA, BETA, CONFIDENCE_THRESHOLD, ENABLE_SEMANTIC_EMBEDDINGS


@dataclass
class FAQDoc:
    id: int
    question: str
    answer: str
    intent: str


class ESRIFEngine:
    """Enhanced Semantic Retrieval with Intent Filtering engine."""

    def __init__(self):
        self.faqs: List[FAQDoc] = []
        self.tfidf_vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.tfidf_matrix = None
        self.search_texts: List[str] = []
        self.use_semantic = False
        self.semantic_model = None
        if ENABLE_SEMANTIC_EMBEDDINGS:
            try:
                # Import only when semantic embeddings are explicitly enabled.
                from sentence_transformers import SentenceTransformer

                # Model load can fail in restricted/offline environments.
                self.semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
                self.use_semantic = True
            except Exception:
                self.use_semantic = False
        self.semantic_matrix = None

    @staticmethod
    def _intent_context_terms(intent: str) -> str:
        context = {
            "Admissions": "admission admissions application apply eligibility onboarding documents",
            "Fees": "fee fees payment payments refund scholarship dues",
            "Examinations": "exam exams timetable schedule hall ticket admit card result",
            "Attendance": "attendance absent absence shortage condonation",
            "Placements": "placement placements recruiter internship package drive",
            "Academics": "academics academic syllabus calendar course courses credits",
            "General": "helpdesk office hours support",
        }
        return context.get(intent, "")

    @staticmethod
    def preprocess(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def keyword_overlap(query: str, question: str) -> float:
        query_words = set(query.split())
        faq_words = set(question.split())
        if not query_words:
            return 0.0
        return len(query_words.intersection(faq_words)) / len(query_words)

    @staticmethod
    def classify_intent(query: str) -> str:
        intent_rules = {
            "Admissions": ["admission", "apply", "application", "eligibility"],
            "Fees": ["fee", "fees", "payment", "scholarship", "refund"],
            "Examinations": ["exam", "timetable", "result", "hall ticket"],
            "Attendance": ["attendance", "absence", "shortage"],
            "Placements": ["placement", "internship", "recruiter", "package"],
            "Academics": ["course", "syllabus", "credits", "registration", "class"],
        }

        for intent, keywords in intent_rules.items():
            if any(keyword in query for keyword in keywords):
                return intent
        return "General"

    def fit(self, faqs: List[FAQDoc]) -> None:
        self.faqs = faqs
        self.search_texts = [
            f"{self.preprocess(f.question)} {self._intent_context_terms(f.intent)}".strip()
            for f in faqs
        ]
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.search_texts)

        if self.use_semantic and self.semantic_model:
            self.semantic_matrix = self.semantic_model.encode(self.search_texts)

    def answer_query(self, raw_query: str):
        query = self.preprocess(raw_query)
        detected_intent = self.classify_intent(query)

        intent_indices = [
            idx
            for idx, faq in enumerate(self.faqs)
            if faq.intent.lower() == detected_intent.lower()
        ]

        if not intent_indices:
            intent_indices = list(range(len(self.faqs)))

        if not intent_indices:
            return {
                "answer": "Knowledge base is currently empty.",
                "confidence": 0.0,
                "detected_intent": detected_intent,
                "escalated": True,
            }

        query_tfidf = self.tfidf_vectorizer.transform([query])
        tfidf_scores = cosine_similarity(query_tfidf, self.tfidf_matrix[intent_indices]).flatten()

        if self.use_semantic and self.semantic_model and self.semantic_matrix is not None:
            query_sem = self.semantic_model.encode([query])
            sem_scores = cosine_similarity(query_sem, self.semantic_matrix[intent_indices]).flatten()
        else:
            sem_scores = tfidf_scores

        best_score = -1.0
        best_faq = None

        for i, idx in enumerate(intent_indices):
            faq = self.faqs[idx]
            keyword_score = self.keyword_overlap(query, self.search_texts[idx])
            similarity_score = float((tfidf_scores[i] + sem_scores[i]) / 2)
            final_score = ALPHA * similarity_score + BETA * keyword_score

            if final_score > best_score:
                best_score = final_score
                best_faq = faq

        # For clear domain intent queries, allow a lower threshold to avoid false escalations.
        soft_threshold = max(0.35, CONFIDENCE_THRESHOLD - 0.1)
        effective_threshold = soft_threshold if detected_intent != "General" else CONFIDENCE_THRESHOLD
        escalated = best_score < effective_threshold
        if escalated:
            answer = (
                "I am not fully confident about this answer. "
                "Your query has been escalated to the student helpdesk administrator."
            )
        else:
            answer = best_faq.answer

        return {
            "answer": answer,
            "faq_answer": best_faq.answer if best_faq else "",
            "confidence": round(float(best_score), 4),
            "detected_intent": detected_intent,
            "escalated": escalated,
        }
