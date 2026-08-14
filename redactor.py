import re
import spacy
from faker import Faker

class PIIRedactor:
    def __init__(self):
        self.faker = Faker()
        # NLP model load kar rahe hain (Entities detect karne ke liye)
        self.nlp = spacy.load("en_core_web_sm")
        
        # Yeh dictionary mapping save karegi taaki consistent replacement ho
        self.mapping_dict = {}

    def get_fake_value(self, original_text, pii_type):
        """Agar value pehle se map hai toh wahi return karo, warna nayi banao"""
        if original_text in self.mapping_dict:
            return self.mapping_dict[original_text]
        
        # Nayi fake value generate karo based on PII type
        if pii_type == "EMAIL":
            fake_val = self.faker.email()
        elif pii_type == "PHONE":
            fake_val = "+91 " + "".join([str(self.faker.random_int(0, 9)) for _ in range(10)])
        elif pii_type == "CREDIT_CARD":
            fake_val = self.faker.credit_card_number()
        elif pii_type == "SSN":
            fake_val = self.faker.ssn()
        elif pii_type == "IP_ADDRESS":
            fake_val = self.faker.ipv4()
        elif pii_type == "DOB":
            fake_val = self.faker.date_of_birth().strftime("%d/%m/%Y")
        
        # Naye NER types yahan add kiye hain
        elif pii_type == "PERSON":
            fake_val = self.faker.name()
        elif pii_type == "ORG":
            fake_val = self.faker.company()
        elif pii_type == "ADDRESS":
            fake_val = self.faker.address().replace('\n', ', ')
            
        else:
            fake_val = "*****" 
            
        self.mapping_dict[original_text] = fake_val
        return fake_val

    def redact_regex_patterns(self, text):
        """Text mein se regex wale fixed PII dhoondho aur replace karo"""
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
            for match in set(matches): 
                fake_replacement = self.get_fake_value(match, pii_type)
                redacted_text = redacted_text.replace(match, fake_replacement)
                
        return redacted_text

    def redact_ner_patterns(self, text):
        """Text mein se Contextual PII (Names, Companies, Addresses) dhoondho"""
        doc = self.nlp(text)
        redacted_text = text
        
        for ent in doc.ents:
            pii_type = None
            if ent.label_ == "PERSON":
                pii_type = "PERSON"
            elif ent.label_ == "ORG":
                pii_type = "ORG"
            elif ent.label_ in ["GPE", "LOC", "FAC"]: # GPE=Geopolitical Entity, LOC=Location
                pii_type = "ADDRESS"
                
            if pii_type:
                fake_replacement = self.get_fake_value(ent.text, pii_type)
                redacted_text = redacted_text.replace(ent.text, fake_replacement)
                
        return redacted_text

    def redact_all(self, text):
        """Master function jo pehle regex chalayega, phir NER"""
        if not text.strip():
            return text
            
        # Pehle strict regex patterns check karein
        text = self.redact_regex_patterns(text)
        # Phir bache hue contextual words check karein
        text = self.redact_ner_patterns(text)
        return text