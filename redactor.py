import re
import spacy
from faker import Faker

class PIIRedactor:
    """
    A robust PII Redaction Engine that uses a hybrid approach (Regex + NER).
    It replaces sensitive data with consistent fake alternatives.
    """
    
    def __init__(self):
        # Initialize Faker for generating realistic dummy data
        self.faker = Faker()
        
        # Load spaCy's English NLP model for Named Entity Recognition (NER)
        self.nlp = spacy.load("en_core_web_sm")
        
        # Hash map to maintain state for deterministic replacements
        # Ensures that the same original text is always replaced by the exact same fake text
        self.mapping_dict = {}

    def get_fake_value(self, original_text: str, pii_type: str) -> str:
        """
        Retrieves a consistent fake value for a given PII string.
        Generates a new one if it doesn't exist in the state map.
        """
        # Return existing mapped value to maintain consistency
        if original_text in self.mapping_dict:
            return self.mapping_dict[original_text]
        
        # Generate new fake value based on the specific PII category
        if pii_type == "EMAIL":
            fake_val = self.faker.email()
        elif pii_type == "PHONE":
            # Formatted to resemble Indian standard +91 XXXXXXXXXX
            fake_val = "+91 " + "".join([str(self.faker.random_int(0, 9)) for _ in range(10)])
        elif pii_type == "CREDIT_CARD":
            fake_val = self.faker.credit_card_number()
        elif pii_type == "SSN":
            fake_val = self.faker.ssn()
        elif pii_type == "IP_ADDRESS":
            fake_val = self.faker.ipv4()
        elif pii_type == "DOB":
            fake_val = self.faker.date_of_birth().strftime("%d/%m/%Y")
        
        # NER Specific Types
        elif pii_type == "PERSON":
            fake_val = self.faker.name()
        elif pii_type == "ORG":
            fake_val = self.faker.company()
        elif pii_type == "ADDRESS":
            # Replace newlines to fit better in document flow
            fake_val = self.faker.address().replace('\n', ', ')
            
        else:
            fake_val = "*****" # Fallback redaction
            
        # Store in state map for future encounters
        self.mapping_dict[original_text] = fake_val
        return fake_val

    def redact_regex_patterns(self, text: str) -> str:
        """
        Scans text for fixed-pattern PII (Email, IP, Phone, etc.) using Regular Expressions.
        """
        # Dictionary containing strict regex patterns for structured PII
        patterns = {
            "EMAIL": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            "IP_ADDRESS": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            "PHONE": r'(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3}\)?[\s-]?)?\d{3}[\s-]?\d{4}', 
            "CREDIT_CARD": r'\b(?:\d[ -]*?){13,16}\b',
            "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
            "DOB": r'\b\d{2}[-/]\d{2}[-/]\d{4}\b|\b\d{4}[-/]\d{2}[-/]\d{2}\b'
        }

        redacted_text = text
        for pii_type, pattern in patterns.items():
            matches = re.findall(pattern, redacted_text)
            # Use set() to avoid redundant processing of duplicates
            for match in set(matches): 
                fake_replacement = self.get_fake_value(match, pii_type)
                redacted_text = redacted_text.replace(match, fake_replacement)
                
        return redacted_text

    def redact_ner_patterns(self, text: str) -> str:
        """
        Scans text for contextual PII (Names, Orgs, Addresses) using spaCy NER.
        """
        doc = self.nlp(text)
        redacted_text = text
        
        # Iterate through detected entities
        for ent in doc.ents:
            pii_type = None
            
            # Map spaCy entity labels to our internal types
            if ent.label_ == "PERSON":
                pii_type = "PERSON"
            elif ent.label_ == "ORG":
                pii_type = "ORG"
            elif ent.label_ in ["GPE", "LOC", "FAC"]: 
                pii_type = "ADDRESS"
                
            if pii_type:
                fake_replacement = self.get_fake_value(ent.text, pii_type)
                redacted_text = redacted_text.replace(ent.text, fake_replacement)
                
        return redacted_text

    def redact_all(self, text: str) -> str:
        """
        Master orchestration function.
        Executes Regex redaction first, followed by NER redaction.
        """
        if not text.strip():
            return text
            
        # 1. Apply strict regex patterns
        text = self.redact_regex_patterns(text)
        # 2. Apply contextual NLP entity extraction
        text = self.redact_ner_patterns(text)
        
        return text