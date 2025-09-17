from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class RiskAssessor:
    def __init__(self):
        self.model_name = "distilbert-base-uncased-finetuned-sst-2-english"
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        except Exception as e:
            # Fallback to simple keyword matching if model fails to load
            self.tokenizer = None
            self.model = None
            self.high_risk_keywords = ['unlimited liability', 'personal guarantee', 'penalty', 'liquidated damages']
            self.medium_risk_keywords = ['indemnification', 'limitation of liability', 'attorney fees']
    
    def assess(self, text: str) -> str:
        if self.model and self.tokenizer:
            return self._assess_with_distilbert(text)
        else:
            return self._assess_with_keywords(text)
    
    def _assess_with_distilbert(self, text: str) -> str:
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
        # Get confidence score for negative sentiment (higher risk)
        negative_confidence = probs[0][0].item()
        
        # Map sentiment to risk levels
        if negative_confidence > 0.8:
            return 'high'
        elif negative_confidence > 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _assess_with_keywords(self, text: str) -> str:
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in self.high_risk_keywords):
            return 'high'
        elif any(keyword in text_lower for keyword in self.medium_risk_keywords):
            return 'medium'
        else:
            return 'low'
