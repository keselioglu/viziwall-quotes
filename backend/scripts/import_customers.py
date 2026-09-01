"""
One-off import of the real Viziwall customer list into the database.
Run from backend/: python scripts/import_customers.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import Customer

# (external_id, company_name, contact_name, phone, email, address)
# company_name is None where the source data had "(company not recorded)".
# Phone/address cleaned of stray embedded newlines from the source paste.
ROWS = [
    ("260013", None, "Camilla Metelka", None, "c.metelka@protonmail.com", None),
    ("260024", None, "Ender Onder", "+491774490369", None, None),
    ("260045", None, "Jissmon Joseph", "+4915217582555", "gizjoseph2002@gmail.com", "Hoeppnerstr 29, 12101 Berlin"),
    ("250036", "AGENZIA CREATTIVA SRL", "Mr. Umberto", "+39 351 789 21 65", "exhibit@agenziacreattiva.com", "Via Roma 32, Caponago – MI, Italy"),
    ("260017", "ALMA ALLESTIMENTI MASTROMONACO s.r.l.", "Fabio Ing. Gnagnarella", "+390736 227832", "fabio@almastand.it", "Zona Industriale Campolungo, 63100 Ascoli Piceno"),
    ("260014", "ARREDART STUDIO S.R.L.", "Elena Rugina", "+39 388 8992785", "elenarugina@arredart.it", "VIA RIGOSA, 40 – 40069 ZOLA PREDOSA (BO) – ITALY"),
    ("250027", "Adhoc S.R.L", "Romina Mariani", "+39.0362.1730311-2", "info@adhocsrl.net", "via Piave, 17 - 20843 Verano Brianza (MB) – Italy"),
    ("260040", "Aemmebi di Marchina", "Alessandra Bossini", "030 6865316", "amministrazione@aemmebi.it", "Via dell'industria 91/93/95 - 25039 Travagliato (BS)"),
    ("260036", "Appe publicidad", "FERNANDO APARICIO SÁNCHEZ", "+34639501547", "faparicio@appepublicidad.com", "Valencia, Spain"),
    ("260016", "Arredo Stand Design", "Caterina Beschi", "+39 045 85 31 911 Int. 108", "beschi.c@arredostandesign.com", "Via Nazionale 72, San Martino Buon Albergo - VR Italy"),
    ("260035", "BALBOA DESIGN & PRODUCTION d.o.o.", "Igor Trninić", "+385 1 3498 531", "igor.trninic@balboa.hr", "Industrijska 6, 10431 Novaki, Sv.Nedelja | Hrvatska"),
    ("250012", "Berry Design", "Berrin Arslan", "+905335975537", "info@berrydesign.com", "Anadolu Hisarı Mah. Sakabayırı Sk. NO: 7 İç Kapı No: 1 Beykoz Istanbul/Turkey"),
    ("250018", "Boytorun Architecture", "Ceyhun UZUN", "+902122294770", "cuzun@boytorunarch.com", "Sakıp Sabancı Caddesi Kalamış Sokak No:3 Daire:1 Emirgan / İstanbul"),
    ("250028", "Constant Design", "Constantine Lapiotis", "+30 6941418880", "constantdesigngr@gmail.com", "53 Agiou Dimitriou Oplon St | Athens 10445 | Greece"),
    ("250035", "Craft Pro Ltd.", "Manfred Li", "(852) 9788 5760", "manfred@craftpro.com.hk", "Unit 1101, Tower 1, Cheung Sha Wan Plaza, No. 833 Cheung Sha Wan Road, Lai Chi Kok, Kowloon, Hong Kong"),
    ("260027", "Creativ Design SRL", "Ahmed Rageh", "+393248244990", "ahmedrageh20@icloud.com", "Via A. Di Dio, 18, 21010 Besnate VA, Italy"),
    ("250026", "DEEG exhibition & more GmbH", "Sebastian Deeg", "+49 (0)221 - 99 96 72 40", "Sebastian.deeg@deeg-more.de", "Emil-Hoffmann-Str. 43, 50996 Köln"),
    ("260019", "DVG Studio", "Dear Olek", "+48 505 662 405", "martyna@dvgstudio.eu", "01-842 Warsaw, Aleja Władysława Reymonta 24/3"),
    ("250037", "DeeZen", "Vassilis Damaskinidis", "(+30) 6978991768", "damask@deezen.gr", "18th Kilometer Spaton 18, 19004 Greece"),
    ("250030", "EURODESIGN S.r.l.", "Lucia Hascakova", "+39 339 468 4866", "lucia@eurods.net", "Via de Pisis, 7, 42124 Reggio Emilia (RE) Italy"),
    ("250027", "EcoStand", "Gustaw Kubara", "+48 34 372 11 88", "gustaw@ecostand.pl", "Ul. Mielczarskiego 21/23, 42-200 Częstochowa/Poland"),
    ("260023", "Envision Enterprise Solutions", "S. A Raju", None, "a.raju@envisionesl.com", "Block D, Level 2, Wing 2, Cyber Gateway, Hitec City, Madhapur, Hyderabad 500081, Telangana, India"),
    ("260038", "European Travel Exhibition SAS", "Julie Liu", "+33(0)750853217", "lj71750@gmail.com", None),
    ("260043", "Eurostands", "Roberto Bottiroli", "+39 351 3117826", "robertobottiroli@eurostands.it", "Via delle Industrie, 51 20040 Cambiago, Milan — Italy"),
    ("260028", "Eve Energy", "Ana Wu", "+86-752-2630809", "anawu2024@gmail.com", "NO.38, Huifeng 7th Road, Zhongkai Hi-Tech Zone, Huizhou, Guangdong Province, China"),
    ("260021", "Exhibition House", "Dear Akash", "+91-9310715845", "sales@exhibitionhouse.in", "15th Eros Corporate Tower, Nehru Place, New Delhi"),
    ("260022", "Expo Stand Service", "Dear Rita", "+91 70113 11202", "enquiry@expostandservice.com", "C-49, Ground Floor, C Block, Sector 10, Noida, Uttar Pradesh 201301 India"),
    ("250033", "Externe Messeabteilung", "Laura Poser", "+49 7666 88486 28", "laura.poser@externe-messeabteilung.de", "Robert-Bunsen-Str. 9, 79211 Denzlingen"),
    ("250026", "Go Stand", "MR. Ibrahim", "+905537947579", "info@go-design.us", "İçerenköy Mahallesi Üsküdar İçerenköy Yolu Cad. No: 4 K:1 /3 Ataşehir/İSTANBUL"),
    ("260030", "Inovasyon Dizayn", "Şebnem Sonbahar", "+90 216 504 87 88 / +90 553 174 0288", None, "Ritim İstanbul, Cevizli, Zuhal Cd. A5 Blok Kat:10 D:48, 34846 Maltepe/İstanbul"),
    ("260020", "Ita.Pro.Srl", "Morena Fratini", "+393939383657", "m.fratini@itapro.it", "Via Tavarnelle Val di Pesa 16, Rome, 00148, Italy"),
    ("260031", "JetCube Sp. z o.o.", "Grzegorz Sworowski", "+48 783 825 245", "g.sworowski@jetcube.eu", "ul. Hawelańska 9/53, 61-625 Poznań, NIP/Tax ID: PL7822579745"),
    ("260041", "Just Brands", "Hauke Kamphorst", None, "Hauke.Kamphorst@justbrands.nl", "New Yorkstraat 50, 1175 RD Lijnden, Netherlands"),
    ("260039", "KUNST-WERKE BERLIN e. V.", "Lukas Frank", "+49 30 243459 - 975", "lfr@kw-berlin.de", "Auguststraße 69, 10117 Berlin"),
    ("260037", "MM STROY REMONT LTD", "Lora Hubanova", "+359/0/988880952", "lora_hubanova@mmexpo-design.eu", "Perjanovits street 10; 1278 Sofia, Bulgaria"),
    ("260042", "MT Messe fuar stant hizm. Ltd", "Hakan Kurt", "+90 505 468 29 64", "Hakan@mtmessestand.com", "Trump towers 402 şişli ist."),
    ("250034", "Mission", "Philemon Cheze", "+33 4 37 44 19 81", "pcheze@mission.fr", "395 rue Gustave Eiffel, 69330 Meyzieu, France"),
    ("250032", "NOVA CORPORATE ID MOBİLYA VE REKLAMCILIK SAN. TİC. A.Ş", "Maroua Laadnani", "+90 553 543 81 41", "maroua.laadnani@nova-tr.com", "Pelitli Koyu Merkez Mah. Pelitli Yolu Cad. No 19141400 / Gebze-Kocaeli, Turkey"),
    ("260046", "Noma Pozitif Exhibition Services", "Derya Karatekeli", "+90 216 363 31 69", "derya@nomapozitif.com", "Yalı Mahallesi Kale Sokak Esen Apt. No:5 D:1 Maltepe/İstanbul/Turkey"),
    ("250032", "Nova TR", "Maroua Laadnani", "+90 553 543 81 41", "maroua.laadnani@nova-tr.com", "Pelitli Koyu Merkez Mah. Pelitli Yolu Cad. No 19141400 / Gebze-Kocaeli, Turkey"),
    ("260025", "SAS Bookingsync", "Sophie Vaz", None, "sophie.v@smily.com", "The Chazals, 05100 Nevache, France"),
    ("260034", "SPIE Excelsius Global Services GmbH", "Emrah Kahraman", "+49 171 2275566", "Emrah.Kahraman@spie-isw.com", "Bgm-Dr-Nebel-Str. 14, 97816 Lohr"),
    ("260024", "Seda International Packaging Group", "Valeria Amitrano", "+39 081 731 91 11", "valeria_amitrano@sedagroup.com", "Corso Salvatore D'Amato 73, 80022 Arzano, Naples – Italy"),
    ("260012", "Silver Plate", "MARTYNA MAJEWSKA", "+48 501 125 494", "m.majewska@silverplate.pl", "ul. Macedońska 4, 02-761 Warszawa"),
    ("260026", "Simplex Mimarlık Dekorasyon Sanayi ve Ticaret A.Ş.", "Göker Çetin", "+90 212 403 5442 / +90 554 814 1138", "goker@simplexmimarlik.com", "Rasimpaşa Mahallesi, Siftah Sokak, Özbaykan İş Merkezi No:3, Kat:5, D:17, 34716 Kadıköy / İstanbul – Türkiye (TR)"),
    ("250028", "Smartlift", "Birgit Ankjaer", "+45 4038 9914", "bia@smartlift.com", "N.A. Christensensvej 39, DK-7900 Nykøbing Mors Denmark"),
    ("260032", "Sojo Cultural S.L.", "Yun Feng", "+86-752-2630809", "esinfosojo@gmail.com", None),
    ("250038", "Stand Design", "Mehmet Yigiter", "+49 171 6869836", "yigitermehmet411@gmail.com", None),
    ("250031", "The Inside B.V.", "Sarah Olliges", "+31 570 745 763", "Sarah@the-inside.nl", "Teugseweg 13, 7418 AM Deventer, The Netherlands"),
    ("250039", "Triumfo International GmbH", "Dear Princy", "+49 (0) 33 2774 99-105", "operations4@triumfo.de", "Zum See 7, 14542 Werder (Havel), Germany"),
    ("260015", "Vimar", "Marlene Barros", "+351 915 028 182", "marlene.barros@vimar.pt", "Quinta dos Estrangeiros, Rua A - Pavilhão 3, 2669-908 Venda do Pinheiro Portugal"),
    ("260018", "Vissual Events", "Matias Valenzuela", "+34 625 354 552", "hello@vissualevents.com", "C/Varsovia 70, 72, 08041, Barcelona, Spain"),
    ("260011", "Visual As Usual", "Ozge Babaoglu", "+905335936493", "ozge@visualasusual.com", "Levent Mah. Karanfil Sok. No:13 Besiktas/Istanbul/Turkey"),
    ("260044", "Volter sro", "Libuse Bubenikova", "+420 704 882 950", "bubenikova@volter.cz", "Klimentská 1216/46 110 00 Prague 1 – Nové Město Czech Republic"),
    ("250029", "Whimsical Exhibits", "SASMIT NARVEKAR", "+31 97010205195", "info@whimsicalexhibits.eu", "Transpolispark, Siriusdreef 17-27, Hoofddorp, 2132 WT, Netherlands"),
    ("260033", "XS Worldwide", "Vivaan Raghuvanshi", "+91 9870303641", "vivaan@xs-worldwide.com", "A-84 Sector-83 Noida, Uttar Pradesh 201305 India"),
]


def main():
    db = SessionLocal()
    created, skipped = 0, 0
    seen_emails = {row[0] for row in db.query(Customer.email).filter(Customer.email.isnot(None)).all()}
    try:
        for external_id, company, contact, phone, email, address in ROWS:
            if email and email in seen_emails:
                print(f"SKIP (email already exists): {company or contact} <{email}>")
                skipped += 1
                continue

            db.add(Customer(
                external_id=external_id,
                company_name=company,
                contact_name=contact,
                phone=phone,
                email=email,
                address=address,
            ))
            if email:
                seen_emails.add(email)  # catches duplicates within this same import batch too
            created += 1

        db.commit()
        print(f"\nDone. Created {created} customer(s), skipped {skipped} duplicate(s).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
