"""
certificate.py
Certificate generation logic for Code Monk — Secure Formatter
"""
import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image
from utils import COMPANY_NAME, LOGO_FILE, CERT_DIR, resource_path

def generate_certificate(entry, target_drive=None):
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    cert_filename = f"CodeMonk_SecureCertificate_{now}.pdf"
    
    # Determine where to save the certificate
    if target_drive and os.path.exists(target_drive):
        cert_path = os.path.join(target_drive, cert_filename)
        save_location = f"saved to formatted drive ({target_drive})"
    else:
        cert_path = os.path.join(CERT_DIR, cert_filename)
        save_location = "saved to application directory"
    
    try:
        c = canvas.Canvas(cert_path, pagesize=A4)
        w, h = A4
        logo_path = resource_path(LOGO_FILE)
        if os.path.exists(logo_path):
            try:
                im = Image.open(logo_path)
                iw, ih = im.size
                target_w = 200
                target_h = int(ih * (target_w / iw))
                c.drawImage(logo_path, w/2 - target_w/2, h - 120, width=target_w, height=target_h, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass
        y = h - 160
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(w/2, y, "SECURE FORMAT CERTIFICATE")
        y -= 30
        c.setFont("Helvetica", 11)
        c.drawString(80, y, f"Issued by : {COMPANY_NAME}")
        y -= 18
        c.drawString(80, y, f"Target    : {entry.get('display') or entry.get('device')}")
        y -= 18
        c.drawString(80, y, f"Method    : Overwrite -> Delete -> Free Space Wipe -> Format")
        y -= 18
        c.drawString(80, y, f"Date      : {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
        y -= 18
        c.drawString(80, y, f"Certificate: {save_location}")
        y -= 30
        c.drawString(80, y, "Digital Signature:")
        c.line(80, y-6, 260, y-6)
        
        # Add verification info
        y -= 40
        c.setFont("Helvetica", 9)
        c.drawString(80, y, "This certificate confirms that the specified drive has been securely wiped")
        y -= 12
        c.drawString(80, y, "using industry-standard methods including file overwriting, free space")
        y -= 12
        c.drawString(80, y, "wiping, and complete reformatting. All data has been irreversibly destroyed.")
        
        c.save()
        return f"{cert_path} ({save_location})"
    except Exception as e:
        return f"ERROR_GEN_CERT: {e}"
