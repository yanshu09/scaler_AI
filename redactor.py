import re
import spacy
from faker import Faker

class PIIRedactor:
    
    def __init__(self):

        self.faker = Faker()
        

        self.nlp = spacy.load("en_core_web_sm")
        

        self.mapping_dict = {}

    def get_fake_value(self, original_text: str, pii_type: str) -> str:
        
        if original_text in self.mapping_dict:
            return self.mapping_dict[original_text]
        

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
        

        elif pii_type == "PERSON":
            fake_val = self.faker.name()
        elif pii_type == "ORG":
            fake_val = self.faker.company()
        elif pii_type == "ADDRESS":

            fake_val = self.faker.address().replace('\n', ', ')
            
        else:
            fake_val = "*****" # Fallback redaction
            

        self.mapping_dict[original_text] = fake_val
        return fake_val

    def redact_regex_patterns(self, text: str) -> str:
        

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

    def redact_ner_patterns(self, text: str) -> str:
        
        doc = self.nlp(text)
        redacted_text = text
        

        for ent in doc.ents:
            pii_type = None
            

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
        
        if not text.strip():
            return text
            

        text = self.redact_regex_patterns(text)

        text = self.redact_ner_patterns(text)
        
        return text