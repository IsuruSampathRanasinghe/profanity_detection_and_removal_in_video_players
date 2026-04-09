from transformers import pipeline

ml_model = pipeline("text-classification", model="unitary/toxic-bert")

def is_toxic(text):
    result = ml_model(text[:512])[0]
    return result["label"] == "TOXIC" and result["score"] > 0.7