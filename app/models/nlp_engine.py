import re

import spacy
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Tuple, Any
import joblib


class HybridNLPEngine:
    def __init__(self):
        print("🚀 Initializing Hybrid NLP Engine...")

        # Load spaCy
        try:
            self.spacy_nlp = spacy.load("en_core_web_sm")
            print("✅ spaCy model loaded")
        except:
            print("⚠️ Could not load spaCy model, please run: python -m spacy download en_core_web_sm")
            self.spacy_nlp = None

        # Load trained models if they exist
        self.vectorizer = None
        self.intent_classifier = None

        try:
            self.vectorizer = joblib.load('app/models/tfidf_vectorizer.pkl')
            self.intent_classifier = joblib.load('app/models/intent_classifier.pkl')
            print("✅ Trained models loaded")
        except FileNotFoundError:
            print("⚠️ Trained model files not found")
            print("📝 Please run: python train_models.py")
            print("📝 Using keyword-based intent detection for now")

        # Load SentenceTransformer if available
        try:
            from sentence_transformers import SentenceTransformer
            self.sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ SentenceTransformer loaded")
        except ImportError:
            print("⚠️ SentenceTransformer not available")
            self.sbert_model = None

        # Intent examples for keyword matching (fallback)
        self.intent_examples = {
            'book_search': ['find', 'search', 'locate', 'book', 'textbook'],
            'library_hours': ['hour', 'open', 'close', 'schedule', 'time'],
            'book_availability': ['available', 'availability', 'in stock', 'on shelf'],
            'book_renewal': ['renew', 'extension', 'prolong'],
            'book_reservation': ['reserve', 'hold', 'booking'],
            'borrowing_policy': ['policy', 'rule', 'limit', 'fine', 'how many', 'how long'],
            'contact_info': ['contact', 'phone', 'email', 'call', 'address', 'department'],
            'research_assistance': ['research', 'journal', 'article', 'database', 'citation', 'paper', 'literature'],
            'study_rooms': ['study room', 'booking space', 'reserve room'],
            'library_services': ['printing', 'scanning', 'workshop', 'service'],
            'greeting': ['hello', 'hi', 'hey', 'greetings', 'morning', 'afternoon', 'evening'],
            'farewell': ['bye', 'goodbye', 'thank', 'thanks']
        }

        self.library_intents = self.intent_examples

        # Also add library_keywords for the other method
        self.library_keywords = self.library_intents  # Use same dictionary

        # Load trained models if they exist
        # self.vectorizer = None
        # self.intent_classifier = None

    def process(self, text: str) -> Dict[str, Any]:
        """
        Process text through the hybrid NLP pipeline
        Returns: Dict with text, intent, entities, confidence, etc.
        """
        # Clean and normalize text
        text = text.lower().strip()

        # Get spaCy analysis
        doc = self.spacy_nlp(text) if self.spacy_nlp else None

        # Extract entities using multiple methods
        entities = self._extract_entities(doc)

        # Classify intent using hybrid approach
        intent, confidence = self._classify_intent_simple(text)

        # Analyze sentiment
        sentiment = self._analyze_sentiment(text)

        # Extract keywords
        keywords = self._extract_keywords(text)

        return {
            'text': text,
            'original_text': text,
            'intent': intent,
            'confidence': float(confidence),
            'entities': entities,
            'sentiment': sentiment,
            'keywords': keywords,
            'tokens': [token.text for token in doc],
            'processed': True
        }

    def _extract_entities(self, doc) -> List[Dict]:
        """Extract entities using spaCy and custom rules"""
        entities = []

        # spaCy named entities
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'type': 'spacy',
                'start': ent.start_char,
                'end': ent.end_char
            })

        # Custom library entities
        custom_entities = self._extract_custom_entities(doc.text)
        entities.extend(custom_entities)

        return entities

    def analyze(self, text: str, context: Dict = None) -> Dict:
        """Advanced NLP analysis with multiple techniques"""

        # 1. SpaCy processing
        doc = self.spacy_nlp(text)

        # 2. Entity extraction
        entities = self._extract_library_entities(doc)

        # 3. Intent classification (multiple methods)
        intent_scores = self._classify_intent_ensemble(text)

        # 4. Semantic similarity with knowledge base
        kb_similarity = self._find_kb_match(text)

        # 5. Sentiment analysis
        sentiment = self._analyze_sentiment(text)

        return {
            'text': text,
            'tokens': [token.text for token in doc],
            'lemmas': [token.lemma_ for token in doc],
            'pos_tags': [(token.text, token.pos_) for token in doc],
            'entities': entities,
            'intent': max(intent_scores, key=intent_scores.get),
            'intent_scores': intent_scores,
            'kb_match': kb_similarity,
            'sentiment': sentiment,
            'confidence': self._calculate_confidence(intent_scores, kb_similarity),
            'requires_clarification': self._needs_clarification(entities, intent_scores)
        }

    def _extract_library_entities(self, doc) -> List[Dict]:
        """Extract library-specific entities"""
        entities = []

        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })

        # Custom entity extraction for library context
        library_entities = self._extract_custom_entities(doc)
        entities.extend(library_entities)

        return entities

    def _classify_intent_ensemble(self, text: str) -> Dict[str, float]:
        """Use multiple models for intent classification"""
        scores = {}

        # Method 1: Rule-based pattern matching
        for intent, keywords in self.library_intents.items():
            score = sum(1 for kw in keywords if kw in text.lower()) / len(keywords)
            scores[intent] = score * 0.3  # Weight

        # Method 2: TF-IDF + Classifier
        tfidf_features = self.vectorizer.transform([text])
        classifier_scores = self.intent_classifier.predict_proba(tfidf_features)[0]
        for i, intent in enumerate(self.intent_classifier.classes_):
            scores[intent] = scores.get(intent, 0) + (classifier_scores[i] * 0.5)

        # Method 3: Semantic similarity with SBERT
        query_embedding = self.sbert_model.encode(text)
        # Compare with predefined intent examples
        for intent, examples in self.intent_examples.items():
            example_embeddings = self.sbert_model.encode(examples)
            similarities = np.dot(example_embeddings, query_embedding)
            scores[intent] = scores.get(intent, 0) + (np.max(similarities) * 0.2)

        return scores

    def _find_kb_match(self, query: str) -> Dict:
        """Find similar questions in knowledge base"""
        # Implement semantic search using FAISS or similar
        pass

    def _classify_intent(self, text: str, doc) -> tuple:
        """Classify intent using rule-based and ML approaches"""
        # Rule-based matching first
        print(f"\n🔍 _classify_intent called with: '{text}'")
        print(f"library_keywords keys: {list(self.library_keywords.keys())}")

        # Rule-based matching first
        for intent, keywords in self.library_keywords.items():
            print(f"  Checking intent: {intent}, keywords: {keywords}")
            for keyword in keywords:
                if keyword in text:
                    print(f"    Matched keyword: '{keyword}' in text")
                    return intent, 0.9

        print("  No keyword matches found")

        # If no rule matches, use keyword frequency
        intent_scores = {}
        for intent, keywords in self.library_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                intent_scores[intent] = score

        print(f"  Intent scores: {intent_scores}")

        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent] / len(self.library_keywords[best_intent])
            return best_intent, min(confidence, 0.8)

        # Fallback to greeting detection
        greeting_words = ['hello', 'hi', 'hey', 'greetings']
        if any(word in text for word in greeting_words):
            return 'greeting', 0.7

        # Default to unknown
        return 'unknown', 0.5

    def _extract_custom_entities(self, text):
        """
        Extract custom entities from text using rule-based patterns
        """
        entities = []

        if hasattr(text, 'text'):
            text_str = text.text  # This is a spaCy Doc object
        else:
            text_str = str(text)  # Convert to string

        # Book-related entities
        book_patterns = {
            'book_title': r'book (?:called|titled|named) ["\'](.+?)["\']',
            'author': r'by (\w+(?:\s+\w+)*)',
            'isbn': r'ISBN(?:\s+)?(\d{10}|\d{13})',
            'genre': r'(fiction|non-fiction|science fiction|fantasy|mystery|biography|textbook)',
        }

        # Library-related entities
        library_patterns = {
            'library_section': r'(reference|circulation|periodicals|archives|digital lab)',
            'service': r'(borrow|return|renew|reserve|interlibrary loan)',
            'duration': r'(\d+)\s+(day|week|month)s?',
            'time': r'(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM))',
        }

        # Search patterns
        for entity_type, pattern in {**book_patterns, **library_patterns}.items():
            matches = re.finditer(pattern, text_str, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'type': entity_type,
                    'value': match.group(1),
                    'start': match.start(),
                    'end': match.end()
                })

        return entities

    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis"""
        positive_words = ['good', 'great', 'excellent', 'thank', 'thanks', 'helpful', 'nice']
        negative_words = ['bad', 'poor', 'terrible', 'wrong', 'incorrect', 'problem']

        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)

        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        else:
            return 'neutral'

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords"""
        if self.spacy_nlp:
            doc = self.spacy_nlp(text)
            keywords = [token.text for token in doc if not token.is_stop and not token.is_punct]
        else:
            # Simple split-based extraction
            words = text.lower().split()
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            keywords = [word for word in words if word not in stopwords and len(word) > 2]

        return list(set(keywords))

    def get_similarity(self, text1: str, text2: str) -> float:
        """Get semantic similarity between two texts"""
        embedding1 = self.sentence_transformer.encode(text1)
        embedding2 = self.sentence_transformer.encode(text2)

        # Cosine similarity
        similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )

        return float(similarity)

    def _calculate_confidence(self, intent_scores: Dict[str, float], kb_similarity: Dict = None) -> float:
        """
        Calculate overall confidence score from intent scores and KB similarity
        """
        if not intent_scores:
            return 0.0

        # Get the highest intent score
        max_score = max(intent_scores.values())

        # Normalize confidence
        confidence = min(max_score, 1.0)

        # Boost confidence if we have a good KB match
        if kb_similarity and 'similarity' in kb_similarity:
            kb_conf = kb_similarity.get('similarity', 0)
            confidence = (confidence * 0.7) + (kb_conf * 0.3)

        return confidence

    def _needs_clarification(self, entities: List[Dict], intent_scores: Dict[str, float]) -> bool:
        """
        Check if we need clarification from the user
        """
        if not entities and max(intent_scores.values(), default=0) < 0.5:
            return True

        # Check for ambiguous intent (multiple intents with similar scores)
        if len(intent_scores) >= 2:
            sorted_scores = sorted(intent_scores.values(), reverse=True)
            if len(sorted_scores) >= 2 and sorted_scores[0] - sorted_scores[1] < 0.2:
                return True

        return False

    def _find_kb_match(self, query: str) -> Dict:
        """Find similar questions in knowledge base (dummy implementation)"""
        return {
            'similarity': 0.0,
            'match_found': False,
            'best_match': None
        }

    def _classify_intent_simple(self, text: str) -> tuple:
        """Simple intent classification using keywords"""
        if not text:
            return 'unknown', 0.0

        text_lower = text.lower()

        # Check for each intent
        best_intent = 'unknown'
        max_score = 0.3

        for intent, keywords in self.library_intents.items():
            score = 0
            for kw in keywords:
                if kw in text_lower:
                    score += 0.4

            if score > max_score:
                max_score = score
                best_intent = intent

        # Overrides for better accuracy
        if any(word in text_lower for word in ['hour', 'open', 'close', 'time']):
            if 'library hour' in text_lower: return 'library_hours', 0.95
            best_intent, max_score = 'library_hours', max(max_score, 0.85)

        if any(word in text_lower for word in ['book', 'find', 'search']):
            if 'available' in text_lower: return 'book_availability', 0.9
            best_intent, max_score = 'book_search', max(max_score, 0.8)

        if any(word in text_lower for word in ['renew']): return 'book_renewal', 0.9
        if any(word in text_lower for word in ['reserve', 'hold']): return 'book_reservation', 0.9

        if any(word in text_lower for word in ['contact', 'phone', 'email']): return 'contact_info', 0.9

        if any(word in text_lower for word in ['research', 'citation', 'paper']): return 'research_assistance', 0.85

        if any(word in text_lower for word in ['hello', 'hi', 'hey', 'greeting', 'morning', 'afternoon', 'evening']):
            return 'greeting', 0.9

        return best_intent, min(max_score, 0.95)