import io
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import re

def remove_emojis(text):
    if not isinstance(text, str):
        return text
    # Remove basic emoji patterns for PDF rendering
    return re.sub(r'[^\w\s\.,;:\-\(\)%€]', '', text)

def generate_excel_report(df, city):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=f'RM_Report_{city}')
    return output.getvalue()

def generate_pdf_report(df, city):
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Lighthouse RM Pro - Rapport Strategique ({city})", ln=True, align='C')
    
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, f"Date d'export : {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    # Summary
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Recommandations d'Ajustement Tarifaire ({len(df)} alertes)", ln=True)
    pdf.ln(5)
    
    # Table Header
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(25, 10, "Date", border=1)
    pdf.cell(45, 10, "Recommandation", border=1)
    pdf.cell(25, 10, "Prix Actuel", border=1)
    pdf.cell(25, 10, "Prix Cible", border=1)
    pdf.cell(70, 10, "Logique IA", border=1, ln=True)
    
    # Table Body
    pdf.set_font("Arial", '', 9)
    for _, row in df.iterrows():
        date_str = str(row['Date'])[:10]
        rec = remove_emojis(str(row.get('Recommendation', '')))
        logic = remove_emojis(str(row.get('Decision_Logic', '')))
        price = f"{row.get('Price', 0):.0f} EUR"
        target = f"{row.get('Prix_Suggere', 0):.0f} EUR"
        
        pdf.cell(25, 10, date_str, border=1)
        pdf.cell(45, 10, rec[:25], border=1)  # Truncate to fit
        pdf.cell(25, 10, price, border=1)
        pdf.cell(25, 10, target, border=1)
        pdf.cell(70, 10, logic[:40], border=1, ln=True)
        
    output_bytes = pdf.output(dest='S')
    if isinstance(output_bytes, str):
        return output_bytes.encode('latin-1', 'replace')
    return bytes(output_bytes)
