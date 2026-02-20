from fpdf import FPDF
import os

class DocumentationPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Echo AI - Project Documentation', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf(input_file, output_file):
    pdf = DocumentationPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    if not os.path.exists(input_file):
        print(f"File {input_file} not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Simple MD to PDF conversion
            line = line.strip()
            if line.startswith('# '):
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, line[2:], 0, 1)
                pdf.set_font("Arial", size=12)
            elif line.startswith('## '):
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, line[3:], 0, 1)
                pdf.set_font("Arial", size=12)
            elif line.startswith('### '):
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, line[4:], 0, 1)
                pdf.set_font("Arial", size=12)
            elif line.startswith('```'):
                continue # Skip code blocks for simple PDF
            else:
                pdf.multi_cell(0, 10, line)
                pdf.ln(2)

    pdf.output(output_file)
    print(f"PDF saved to {output_file}")

if __name__ == "__main__":
    create_pdf('ECHO_DOCS.md', 'ECHO_DOCS.pdf')
