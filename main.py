import os
import docx
from redactor import PIIRedactor

def process_docx(input_path: str, output_path: str, redactor: PIIRedactor):
   
    print(f"Loading document: {input_path}...")
    doc = docx.Document(input_path)
    
    print("Redacting normal paragraphs...")

    for para in doc.paragraphs:
        if para.text.strip():

            para.text = redactor.redact_all(para.text)
            
    print("Redacting tables...")
   
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    if para.text.strip():
                        para.text = redactor.redact_all(para.text)
                        
    print(f"Saving redacted document to: {output_path}...")
    doc.save(output_path)
    print("Done!")

if __name__ == "__main__":

    redactor = PIIRedactor()
    

    input_file = "Red Herring Prospectus.docx"
    output_file = "Redacted_Red_Herring_Prospectus.docx"
    

    if os.path.exists(input_file):
        process_docx(input_file, output_file, redactor)
    else:
        print(f"Error: '{input_file}' not found in the current directory.")