"""
Fills in blank fields (phone/address only, per this sheet's columns) on existing
customers, matched by email. Never overwrites a field that already has a value.
Run from backend/: python scripts/fill_customer_gaps.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import Customer

# (email, phone, address) — from the "customers" sheet pasted 2026-08-20.
# Company Name column intentionally not used for matching/overwrite: emails are
# the reliable join key, and every company name here already matches an existing record.
ROWS = [
    ("info@berrydesign.com", "+905335975537", None),
    ("cuzun@boytorunarch.com", "+902122294770", "Sakıp Sabancı Caddesi Kalamış Sokak No:3 Daire:1 Emirgan / İstanbul"),
    ("info@go-design.us", "+905537947579", "İçerenköy Mahallesi Üsküdar İçerenköy Yolu Cad. No: 4 K:1 /3 Ataşehir/İSTANBUL"),
    ("gustaw@ecostand.pl", "+48 34 372 11 88", "Ul. Mielczarskiego 21/23, 42-200 Częstochowa/Poland"),
    ("constantdesigngr@gmail.com", "+30 6941418880", "53 Agiou Dimitriou Oplon St | Athens 10445 | Greece"),
    ("info@whimsicalexhibits.eu", "+31 97010205195", "Transpolispark, Siriusdreef 17-27, Hoofddorp, 2132 WT, Netherlands"),
    ("lucia@eurods.net", "+39 339 468 4866", "Via de Pisis, 7, 42124 Reggio Emilia (RE) Italy"),
    ("Sarah@the-inside.nl", "+31 570 745 763", "Teugseweg 13, 7418 AM Deventer, The Netherlands"),
    ("maroua.laadnani@nova-tr.com", "+90 553 543 81 41", "Pelitli Koyu Merkez Mah. Pelitli Yolu Cad. No 19141400 / Gebze-Kocaeli, Turkey"),
    ("laura.poser@externe-messeabteilung.de", "+49 7666 88486 28", "Robert-Bunsen-Str. 9, 79211 Denzlingen"),
    ("pcheze@mission.fr", "+33 4 37 44 19 81", "395 rue Gustave Eiffel, 69330 Meyzieu, France"),
    ("manfred@craftpro.com.hk", "(852) 9788 5760", "Unit 1101, Tower 1, Cheung Sha Wan Plaza, No. 833 Cheung Sha Wan Road, Lai Chi Kok, Kowloon, Hong Kong"),
    ("exhibit@agenziacreattiva.com", "+39 351 789 21 65", "Via Roma 32, Caponago – MI, Italy"),
    ("damask@deezen.gr", "(+30) 6978991768", "18th Kilometer Spaton 18, 19004 Greece"),
    ("yigitermehmet411@gmail.com", "+49 171 6869836", None),
    ("operations4@triumfo.de", "+49 (0) 33 2774 99-105", "Zum See 7, 14542 Werder (Havel), Germany"),
    ("ozge@visualasusual.com", "+905335936493", "Levent Mah. Karanfil Sok. No:13 Besiktas/Istanbul/Turkey"),
    ("m.majewska@silverplate.pl", "+48 501 125 494", "ul. Macedońska 4, 02-761 Warszawa"),
]


def main():
    db = SessionLocal()
    updated_fields = 0
    matched, not_found = 0, []

    try:
        for email, phone, address in ROWS:
            customer = db.query(Customer).filter(Customer.email == email).first()
            if not customer:
                not_found.append(email)
                continue
            matched += 1

            changes = []
            if not customer.phone and phone:
                customer.phone = phone
                changes.append("phone")
            if not customer.address and address:
                customer.address = address
                changes.append("address")

            if changes:
                updated_fields += len(changes)
                print(f"UPDATED {customer.company_name or customer.contact_name} <{email}>: filled {', '.join(changes)}")
            else:
                print(f"no gaps  {customer.company_name or customer.contact_name} <{email}>")

        db.commit()
        print(f"\nMatched {matched}/{len(ROWS)} rows. Filled {updated_fields} blank field(s) total.")
        if not_found:
            print(f"Not found in DB ({len(not_found)}): {', '.join(not_found)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
