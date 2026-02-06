#!/usr/bin/env python3
"""
Train NLP models for the library chatbot
"""

import os
import joblib
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import numpy as np

print("🚀 Training NLP models for library chatbot...")

# Create directory
os.makedirs('app/models', exist_ok=True)

# Sample training data for library domain
training_data = {
    'texts': [
        # Book search queries
        'find books about computer science',
        'search for python programming books',
        'locate artificial intelligence textbooks',
        'where can i find physics books',
        'i need books on software engineering',

        # Library hours
        'what are the library hours',
        'when does the library open',
        'what time does the library close',
        'is the library open on weekends',
        'library opening hours',

        # Borrowing info
        'how many books can i borrow',
        'what is the loan period',
        'can i renew my books',
        'how do i return books',
        'borrowing policy for students',

        # Research help
        'i need help with research',
        'how do i find journal articles',
        'help with literature review',
        'database access for off campus',
        'research consultation appointment',

        # General
        'hello',
        'hi there',
        'thank you',
        'goodbye',
        'see you later'
    ],
    'intents': [
        'book_search', 'book_search', 'book_search', 'book_search', 'book_search',
        'library_hours', 'library_hours', 'library_hours', 'library_hours', 'library_hours',
        'borrowing_info', 'borrowing_info', 'borrowing_info', 'borrowing_info', 'borrowing_info',
        'research_help', 'research_help', 'research_help', 'research_help', 'research_help',
        'greeting', 'greeting', 'farewell', 'farewell', 'farewell'
    ]
}

# 1. Train TF-IDF Vectorizer
print("📊 Training TF-IDF vectorizer...")
vectorizer = TfidfVectorizer(
    max_features=1000,
    stop_words='english',
    ngram_range=(1, 2)
)
X = vectorizer.fit_transform(training_data['texts'])

# Save vectorizer
vectorizer_path = 'tfidf_vectorizer.pkl'
joblib.dump(vectorizer, vectorizer_path)
print(f"✅ Saved vectorizer to {vectorizer_path}")

# 2. Train Intent Classifier
print("🧠 Training intent classifier...")
y = np.array(training_data['intents'])
classifier = MultinomialNB()
classifier.fit(X, y)

# Save classifier
classifier_path = 'intent_classifier.pkl'
joblib.dump(classifier, classifier_path)
print(f"✅ Saved classifier to {classifier_path}")

# 3. Save training metadata
metadata = {
    'classes': classifier.classes_.tolist(),
    'feature_names': vectorizer.get_feature_names_out().tolist(),
    'training_samples': len(training_data['texts'])
}
metadata_path = 'training_metadata.pkl'
with open(metadata_path, 'wb') as f:
    pickle.dump(metadata, f)
print(f"✅ Saved metadata to {metadata_path}")

# Test the models
test_queries = [
    'find me some books',
    'library hours please',
    'can i borrow books'
]

for query in test_queries:
    X_test = vectorizer.transform([query])
    proba = classifier.predict_proba(X_test)[0]
    pred = classifier.predict(X_test)[0]
    confidence = max(proba)
    print(f"Query: '{query}' → Intent: {pred} (confidence: {confidence:.2f})")

print("\n🎉 Model training complete!")
print("📁 Models saved in: app/models/")
print("📋 You can now run: python run.py")