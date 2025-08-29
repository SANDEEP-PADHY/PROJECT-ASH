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

def generate_certificate(entry):
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    cert_name = os.path.join(CERT_DIR, f"CodeMonk_SecureCertificate_{now}.pdf")
    try:
        c = canvas.Canvas(cert_name, pagesize=A4)
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
        c.drawString(80, y, f"Method    : Scramble -> Delete -> Overwrite -> Junk -> Quick Format")
        y -= 18
        c.drawString(80, y, f"Date      : {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
        y -= 36
        c.drawString(80, y, "Signature:")
        c.line(80, y-6, 260, y-6)
        c.save()
        return cert_name
    except Exception as e:
        return f"ERROR_GEN_CERT: {e}"
