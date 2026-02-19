import json
import pickle
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

print("Loading intents...")
with open('backend/intents.json', 'r') as file:
    data = json.load(file)

training_sentences = []
training_labels = []
labels = []
responses = {}

for intent in data['intents']:
    for pattern in intent['patterns']:
        training_sentences.append(pattern)
        training_labels.append(intent['tag'])
    responses[intent['tag']] = intent['responses']
    
    if intent['tag'] not in labels:
        labels.append(intent['tag'])

print(f"Training on {len(training_sentences)} sentences across {len(labels)} tags.")

# Create Pipeline
model = Pipeline([
    ('tfidf', TfidfVectorizer(lowercase=True, stop_words='english')),
    ('clf', LogisticRegression(random_state=42, max_iter=1000))
])

# Train
print("Training model...")
model.fit(training_sentences, training_labels)

# Accuracy Check (Internal)
print("Model Score:", model.score(training_sentences, training_labels))

# Save Model and Data
print("Saving artifacts...")
joblib.dump(model, 'backend/chat_model.pkl')
joblib.dump(responses, 'backend/responses.pkl')

print("Training Complete! Model saved to backend/chat_model.pkl")
