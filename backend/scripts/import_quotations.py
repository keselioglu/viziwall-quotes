"""
Imports historical quotations from the sheet pasted 2026-08-20.
Creates minimal placeholder customers for any external_id not already in the DB.
Run from backend/: python scripts/import_quotations.py
"""
import re
import sys
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import Customer, Quotation, QuoteStatus

STATUS_MAP = {
    "Approved": QuoteStatus.approved,
    "Declined": QuoteStatus.declined,
    "Cancelled": QuoteStatus.cancelled,
    "Waiting": QuoteStatus.waiting,
    "New Version Sent": QuoteStatus.new_version_sent,
    "Follow up sent": QuoteStatus.follow_up_sent,
}

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}

# Matches "February 22-26, 2026", "Jan 16 – 18, 2026", "13-17 April 2026", "September 8-12, 2026"
DATE_RANGE_RE = re.compile(
    r'(?:(?P<month1>[A-Za-z]+)\s+)?(?P<day1>\d{1,2})\s*[-–]\s*(?:(?P<month2>[A-Za-z]+)\s+)?(?P<day2>\d{1,2})(?:,)?\s*(?:(?P<month3>[A-Za-z]+)\s+)?(?P<year>\d{4})'
)
SINGLE_DATE_RE = re.compile(r'(?P<month>[A-Za-z]+)\s+(?P<day>\d{1,2}),?\s+(?P<year>\d{4})')


def parse_event_dates(text):
    """Best-effort parse of free-text event date ranges. Returns (start, end) or (None, None)."""
    if not text:
        return None, None

    m = DATE_RANGE_RE.search(text)
    if m:
        month_name = (m.group("month1") or m.group("month2") or m.group("month3") or "").lower()
        month = MONTHS.get(month_name)
        year = int(m.group("year"))
        day1, day2 = int(m.group("day1")), int(m.group("day2"))
        if month:
            try:
                return date(year, month, day1), date(year, month, day2)
            except ValueError:
                pass

    m = SINGLE_DATE_RE.search(text)
    if m:
        month = MONTHS.get(m.group("month").lower())
        if month:
            try:
                d = date(int(m.group("year")), month, int(m.group("day")))
                return d, d
            except ValueError:
                pass

    return None, None


def parse_money(text):
    if not text:
        return None
    cleaned = text.replace("€", "").replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


# (Quote Number, Status, Customer ID, Event Name, Venue, Event Dates, Service Description,
#  Date of Quotation, Discount Amount, Total Amount)
ROWS = [
    ("0882501", "Approved", "250012", "InterTabac 2025", "Dortmund Trade Fair", "September 18–20, 2025", "End-to-End LED Wall Rental & Setup 20m2 Flat", "09/2025", "€500.00", "€6,500.00"),
    ("1882501", "Declined", "250018", "Busworld Europe", "Brussels Expo", "October 4–9, 2025", "End-to-End LED Wall Rental & Setup 34m2 Flat", None, "€0.00", "€15,340.00"),
    ("2182501-R1", "Declined", "250012", "CPHI Frankfurt", "Messe", "October 28–30, 2025", "End-to-End LED Wall Rental & Setup 4 Led walls 26.75m2 Total Flat", None, "€908.75", "€14,625.00"),
    ("2782501", "Declined", "250026", "Eans 2025", "Vienna Congress & Convention Center", "October 5–9, 2025", "End-to-End LED Wall Rental & Setup 3.75m2 Total Flat", None, "€0.00", "€3,440.00"),
    ("23102501", "New Version Sent", "250027", "Euro Shop 2026", "Messe Dusseldorf", "February 22-26, 2026", "End-to-End LED Wall Rental & Setup 12.5m2 Total Flat", None, "€0.00", "€5,170.00"),
    ("24102501", "New Version Sent", "250027", "Euro Shop 2026", "Messe Dusseldorf", "February 22-26, 2026", "End-to-End LED Wall Rental & Setup 6m2 Total Flat", None, "€0.00", "€4,100.00"),
    ("12112501", "Declined", "250028", "Light + Building 2026", "Messe Frankfurt", "March 8-13, 2026", "End-to-End LED Wall Rental & Setup 8m2 Total Flat", None, "€1,092.00", "€4,368.00"),
    ("24102501-v2", "New Version Sent", "250027", "Euro Shop 2026", "Messe Dusseldorf", "February 22-26, 2026", "End-to-End LED Wall Rental & Setup 11.25m2 Total Flat", None, "€0.00", "€4,895.00"),
    ("20112502", "Cancelled", "250029", "WIRE & TUBE 2026", "Messe Dusseldorf", "13-17 April 2026", "End-to-End LED Wall Rental & Setup 19.5m2 Total Flexible/Cylindrical", None, "€0.00", "€9,615.00"),
    ("21112501", "Declined", "250030", "Euro Shop 2026", "Messe Dusseldorf", "February 22-26, 2026", "End-to-End LED Wall&Displays Rental & Setup", None, "€1,395.00", "€12,550.00"),
    ("26112501", "Declined", "250031", "Euro Shop 2026", "Messe Dusseldorf", "February 22-26, 2026", "End-to-End LED Wall Rental & Setup", None, "€1,325.81", "€7,512.94"),
    ("3122501", "New Version Sent", "250032", "Euro Shop 2026", "Messe Dusseldorf", "February 22-26, 2026", "End-to-End LED Wall Rental & Setup 3m2 Total Flat", None, "€0.00", "€1,530.00"),
    ("5122501", "Declined", "250033", "LogiMat Stuttgart 2026", "Stuttgart Trade Fair Centre", "March 24 - 26, 2026", "End-to-End LED Wall Rental & Setup 12m2 Total Flat", None, "€0.00", "€3,640.00"),
    ("5122502", "Approved", "250034", "opti Munich 2026", "Messe München", "Jan 16 – 18, 2026", "End-to-End LED Wall Rental & Setup 3m2 Total Flat", "01/2026", "€0.00", "€2,540.00"),
    ("9122501", "Declined", "250035", "Nobu Hotel Barcelona", "Barcelona, Spain", "Jan 19-21, 2026", "End-to-End LED Wall an Lighting Rental & Setup", None, "€0.00", "€7,965.00"),
    ("11122501", "Cancelled", "250036", "INTERPACK - 2026", "Messe Dusseldorf", "May 7-13, 2026", "End-to-End Booth Stand Construction&Setup", None, "€0.00", "€15,446.20"),
    ("12122501", "Declined", "250037", "Ceramitec 2026", "Messe München", "March 24–26, 2026", "End-to-End 3.75m2 LED Wall&Displays Rental & Setup", None, "€0.00", "€3,933.75"),
    ("3122501-V2", "New Version Sent", "250032", "Euro Shop 2026", "Messe Dusseldorf", "February 22-26, 2026", "End-to-End LED Wall&Displays Rental and Setup 4.5m2 Total Flat", None, "€330.00", "€3,600.00"),
    ("18122501", "Cancelled", "250038", "INTERPACK - 2026", "Messe Dusseldorf", "May 7-13, 2026", "End-to-End LED Wall Rental & Setup 6m2 Total Flat", None, "€0.00", "€2,405.00"),
    ("23122501", "Declined", "250039", "Euroguss 2026", "Nürnberg Messe", "Jan 13-15, 2026", "End-to-End LED Wall&Dislpays Rental and Setup", None, "€0.00", "€3,375.00"),
    ("23122502", "Declined", "250039", "Domotex 2026", "Hannover Exhibition Centre", "Jan 19-22, 2026", "End-to-End LED Wall&Dislpays Rental and Setup", None, "€0.00", "€2,748.75"),
    ("23122503", "Declined", "250039", "E-World 2026", "Messe Essen", "February 10 - 12, 2026", "End-to-End LED Wall&Dislpays Rental and Setup", None, "€0.00", "€4,585.00"),
    ("23122504", "Declined", "250039", "Euro Shop 2026", "Messe Dusseldorf", "February 22-26, 2026", "End-to-End LED Wall&Dislpays Rental and Setup", None, "€0.00", "€4,531.25"),
    ("3122501-V3", "Approved", "250032", "Euro Shop 2026", "Messe Dusseldorf", "February 22-26, 2026", "End-to-End LED Wall&Displays Rental and Setup 4.5m2 Total Flat", "02/2026", "€165.00", "€2,100.00"),
    ("26-050102", "Declined", "250039", "FRUIT LOGISTICA 2026", "Messe Berlin", "4-6 February 2026", "End-to-End LED Dislpays Rental and Setup", None, "€0.00", "€1,300.00"),
    ("26-050103xx", "Cancelled", "250039", "Intertraffic 2026", "RAI Amsterdam", "10 - 13 MAR 2026", "End-to-End Dislpays Rental and Setup", None, "€0.00", "€2,800.00"),
    ("26-050103", "New Version Sent", "250039", "LogiMat Stuttgart 2026", "Stuttgart Trade Fair Centre", "March 24 - 26, 2026", "End-to-End Dislpays Rental and Setup", None, "€0.00", "€1,800.00"),
    ("26-090102-v1", "New Version Sent", "260011", "4.5m2 Total Flat", "Messe Frankfurt", "3 Day Event-Dates TBD", "End-to-End LED Wall Rental & Setup", None, "€0.00", "€2,370.00"),
    ("26-090102-v2", "Declined", "260011", "9m2 Total Flat", "Messe Frankfurt", "3 Day Event-Dates TBD", "End-to-End LED Wall Rental & Setup", None, "€0.00", "€3,465.00"),
    ("26-150101", "Declined", "260012", "E-World 2026", "Messe Essen", "February 10 - 12, 2026", "End-to-End LED Wall&Dislpays Rental and Setup", None, "€0.00", "€22,725.00"),
    ("26-150102", "Declined", "250030", "Hannover Messe 2026", "Messe Hannover", "April 20-24, 2026", "End-to-End LED Wall Rental & Setup", None, "€0.00", "€20,890.00"),
    ("26-150103", "Declined", "260013", None, "Akademie der bildenden Künste in München", "February 5-10, 2026", "End-to-End LED Wall Rental & Setup", None, "€0.00", "€4,372.50"),
    ("26-170101", "Declined", "260014", "INTERPACK - 2026", "Messe Dusseldorf", "May 7-13, 2026", "End-to-End LED Wall Rental & Setup 3.75m2 Total Flat", None, "€0.00", "€2,860.00"),
    ("26-220101", "Declined", "260015", "MIPIM - 2026", "Palais des Festivals, Cannes", "March 9-13, 2026", "End-to-End LED Wall and Displays Rental & Setup", None, "€0.00", "€9,336.25"),
    ("26-260102", "Declined", "260016", "IWA - 2026", "Nürnberg Messe", "February 26- March 1, 2026", "End-to-End Displays Rental & Setup", None, "€500.00", "€500.00"),
    ("24102501-v3", "New Version Sent", "250027", "Euro Shop 2026", "Messe Dusseldorf", "February 22-26, 2026", "End-to-End LED Wall Rental & Setup 11.25m2 Total Flat", None, "€2,450.00", "€2,445.00"),
    ("26-290101", "Declined", "260017", "Spoga Horse 2026", "Koeln Messe", "February 7-9, 2026", "End-to-End Displays & Setup", None, "€0.00", "€1,600.00"),
    ("26-150102-V2", "Declined", "250030", "Hannover Messe 2026", "Messe Hannover", "April 20-24, 2026", "End-to-End LED Wall Rental & Setup", None, "€0.00", "€24,932.00"),
    ("26-210201", "Approved", "260022", "Euro Shop 2026", "Messe Dusseldorf", "February 22-26, 2026", "End-to-End AV Rental&Setup", "02/2026", "€0.00", "€280.00"),
    ("26-030201", "Declined", "260019", "Vitafoods Barcelona", "Fira Barcelona", "May 5-7, 2026", "End-to-End LED Wall Rental & Setup", None, "€0.00", "€3,047.50"),
    ("26-020202", "New Version Sent", "260016", "Automechanika Frankfurt", "Messe Frankfurt", "September 8-12, 2026", "End-to-End LED Wall Rental & Setup", None, "€0.00", "€2,430.00"),
    ("24102501-v4", "Declined", "250027", "Euro Shop 2026", "Messe Dusseldorf", "February 22-26, 2026", "End-to-End LED Wall Rental & Setup 6m2 Total Flat", None, "€2,050.00", "€2,050.00"),
    ("26-060201", "Declined", "250039", "Embedded World 2026", "Nürnberg Messe", "March 10 - 12, 2026", "End-to-End Dislpays Rental and Setup", None, "€0.00", "€4,705.00"),
    ("26-050103-V2", "Cancelled", "250039", "LogiMat Stuttgart 2026", "Stuttgart Trade Fair Centre", "March 24 - 26, 2026", "End-to-End Led Wall&Dislpays Rental and Setup", None, "€0.00", "€7,485.00"),
    ("26-110202", "Declined", "260020", "ITB Berlin 2027", "Messe Berlin", "3 days in March, 2027", "End-to-End LED Wall Rental & Setup 9.75m2 Total Curved", None, "€0.00", "€4,433.75"),
    ("26-140201", "Declined", "260021", "ProWein 2026", "Messe Dusseldorf", "March 15-17, 2026", "End-to-End LED Wall Rental & Setup 3m2 Total Flat", None, "€0.00", "€1,700.00"),
    ("26-170201", "Declined", "260022", "ITB Berlin 2026", "Messe Berlin", "3 - 5 March, 2026", "End-to-End LED Wall Rental & Setup 13m2 Total Flat", None, "€1,425.00", "€3,760.00"),
    ("26-190201", "Declined", "260023", "Private Event", "Dusseldorf Clayton Hotel", "3 - 4 March, 2026", "End-to-End Displays Rental & Setup", None, "€0.00", "€800.00"),
    ("26-120301", "Approved", "250026", "Seafood Expo - 2026", "Fira Barcelona", "April 21-23, 2026", "End-to-End LED Wall Rental & Setup 6m2 Total Flat", "04/2026", "€1,010.00", "€2,400.00"),
    ("26-040301", "Declined", "260024", "INTERPACK - 2026", "Messe Dusseldorf", "May 7-13, 2026", "End-to-End LED Wall Rental & Setup 12.25m2 Total Flexible", None, "€1,218.75", "€3,655.00"),
    ("26-050301", "Cancelled", "260024", "Fiberdays - 2026", "Messe Frankfurt", "March 25-26, 2026", "End-to-End LED Wall Rental & Setup 4m2 Total Flat", None, "€0.00", "€2,385.00"),
    ("26-050302", "Cancelled", "260021", "ProWein 2026", "Messe Dusseldorf", "March 15-17, 2026", "End-to-End Stand Construction & Setup", None, "€0.00", None),
    ("26-110302", "Cancelled", "260025", None, "Parc Chanot", "March 23 - 24, 2026", "End-to-End Led Wall&Dislpays Rental and Setup", None, "€0.00", "€4,565.00"),
    ("26-280301", "Approved", "260026", "ESCMID Munich", "Messe München", "April 17-21, 2026", "End-to-End Displays Rental & Setup", "04/2026", "€0.00", "€1,630.00"),
    ("26-170302", "New Version Sent", "250027", "IFAT Munich", "Messe München", "May 4-7, 2026", "End-to-End LED Wall Rental & Setup", None, "€494.50", "€4,450.50"),
    ("26-260301", "Declined", "250027", "Chemspec Europe", "Koelnmesse", "May 6-7, 2026", "End-to-End LED Wall Rental & Setup", None, "€0.00", "€4,455.00"),
    ("26-030402", "Approved", "260027", "Techtextil", "Messe Frankfurt", "April 21-24, 2026", "End-to-End LED Wall&Audio Rental & Setup", "04/2026", "€0.00", "€2,885.00"),
    ("26-300102", "Approved", "260018", "IFAT Munich", "Messe München", "May 4-7, 2026", "End-to-End LED Wall Rental & Setup", "05/2026", "€0.00", "€2,705.00"),
    ("26-270301", "Approved", "250034", "IFAT Munich", "Messe München", "May 4-7, 2026", "End-to-End Displays Rental & Setup", "05/2026", "€0.00", "€1,250.00"),
    ("26-170302-V2", "Approved", "250027", "IFAT Munich", "Messe München", "May 4-7, 2026", "End-to-End LED Wall &AudioRental & Setup", "05/2026", "€494.50", "€5,500.50"),
    ("26-040802", "Approved", "260031", "Chemspec Europe", "Koelnmesse", "May 6-7, 2026", "End-to-End LED Wall Rental & Setup", "05/2026", "€0.00", "€1,485.00"),
    ("26-060402", "New Version Sent", "260028", None, None, None, None, None, "€0.00", "€4,450.00"),
    ("26-060403", "Cancelled", "260030", "IFAT Munich", "Messe München", "May 4-7, 2026", "End-to-End LED Wall & TV Rental & Setup", None, "€740.00", "€6,700.00"),
    ("26-170302-V4", "Approved", "250027", "IFAT Munich", "Messe München", "May 4-7, 2026", "End-to-End LED Wall &AudioRental & Setup", "05/2026", "€690.00", "€5,100.00"),
    ("26-080401", "New Version Sent", "260028", "Private Event", "Hotel in Munich", "June 22 2026", "End-to-End LED Wall&Audio Rental & Setup", None, "€195.00", "€1,700.00"),
    ("26-300402", "Approved", "260035", "Beauty Istanbul - 2026", "TUYAP", "May 7-9, 2026", "End-to-End LED Wall Rental & Setup 7.5m2 Total Flat 2.6", "05/2026", "€0.00", "€1,847.50"),
    ("26-060402-v2", "Approved", "260028", "Intersolar", "Messe München", "June 23-25, 2026", "End-to-End LED Wall&Audio Rental & Setup", "06/2026", "€535.00", "€4,815.00"),
    ("26-210402", "Waiting", "260032", "Intersolar", "Messe München", "June 23-25, 2026", "End-to-End LED Wall Rental & Setup", "06/2026", "€0.00", "€12,655.00"),
    ("26-080401-V3", "Approved", "260028", "Private Event", "Hotel in Munich", "June 22 2026", "End-to-End LED Wall&Audio Rental & Setup", "06/2026", "€195.00", "€2,510.00"),
    ("26-200501-V2", "Approved", "260038", "Private Event", "The Westin Grand Frankfurt", "June 24, 2026", "End-to-End LED Wall Rental & Setup 11.25m2 Flat", "06/2026", "€232.50", "€5,000.00"),
    ("26-270401", "Cancelled", "250027", "IFAT Munich", "Messe München", "May 4-7, 2026", "End-to-End LED Wall &AudioRental & Setup", None, "€0.00", "€350.00"),
    ("26-280401", "New Version Sent", "250038", "IAA Transportation 2026", "Hannover Messe", "September 15-20, 2026", "End-to-End LED Wall Rental & Setup", None, "€0.00", "€2,656.00"),
    ("26-210403", "Follow up sent", "260033", "Automechanika Frankfurt", "Messe Frankfurt", "September 8-12, 2026", "End-to-End LED Wall and Audio Rental & Setup", "09/2026", "€0.00", "€2,060.00"),
    ("26-040602", "Follow up sent", "260033", "Airmed World Congress2026", "Munich", "September 16 to 18, 2026", "End-to-End LED Wall and Audio Rental & Setup", "09/2026", "€0.00", "€3,130.00"),
    ("26-170602", "Follow up sent", "260016", "Automechanika Frankfurt", "Messe Frankfurt", "September 8-12, 2026", "End-to-End LED Wall Rental & Setup", "09/2026", "€0.00", "€7,987.50"),
    ("26-120501", "Cancelled", "260036", "TECMA 2026", "Ifema Madrid", "June 9-11, 2026", "End-to-End LED Wall Rental & Setup 6m2 Total Flat 2.6", None, "€0.00", "€3,620.00"),
    ("26-280401-V2", "Approved", "250038", "IAA Transportation 2026", "Hannover Messe", "September 15-20, 2026", "End-to-End LED Wall Rental & Setup", "09/2026", "€0.00", "€3,130.00"),
    ("26-020202-v2", "Follow up sent", "260016", "Automechanika Frankfurt", "Messe Frankfurt", "September 8-12, 2026", "End-to-End LED Wall Rental & Setup", None, "€0.00", "€1,923.75"),
    ("26-140502", "Cancelled", "260037", "gamescom 2026", "Koelnmesse", "August 26-30, 2026", "End-to-End LED Wall Rental & Setup 18m2 Flat", "08/2026", "€0.00", "€5,850.00"),
    ("26-200501", "New Version Sent", "260038", "Private Event", "Venue in Frankfurt", "June 24, 2026", "End-to-End LED Wall Rental & Setup 12.5m2 Flat", None, "€0.00", "€5,620.00"),
    ("26-090402", "Follow up sent", "260020", "AUTOMECHANIKA", "Messe Frankfurt", "8-12 September 2026", "End-to-End LED Wall Rental & Setup 15m2 Total", "09/2026", "€0.00", "€5,973.75"),
    ("26-200503", "Cancelled", "260037", "gamescom 2026", "Koelnmesse", "August 26-30, 2026", "End-to-End Displays Rental & Setup", "08/2026", "€0.00", "€3,490.00"),
    ("26-010602", "Cancelled", "260040", "Intersolar", "Messe München", "June 23-25, 2026", "End-to-End LED Wall Rental & Setup", None, "€0.00", "€10,540.00"),
    ("26-260302", "New Version Sent", "250028", "Glasstec - 2026", "Messe Dusseldorf", "October 20-23, 2026", "End-to-End LED Wall Rental & Setup 7m2 Total Flat", "10/2026", "€0.00", "€2,305.00"),
    ("26-280402-V2", "Approved", "260034", "Glasstec - 2026", "Messe Dusseldorf", "October 20-23, 2026", "End-to-End LED Wall Rental & Setup 19.66m2 Total Flat 1.9", "10/2026", "€227.00", "€9,000.00"),
    ("26-100602", "Declined", "260038", "Private Event", "The Westin Grand Frankfurt", "June 24, 2026", "End-to-End LED Audio System Rental & Setup", None, "€180.00", "€1,880.00"),
    ("26-280403", "New Version Sent", "260034", "Glasstec - 2026", "Messe Dusseldorf", "October 20-23, 2026", "End-to-End LED Wall Rental & Setup 20m2 Total Flat 2.6", "10/2026", "€0.00", "€5,880.00"),
    ("26-200502", "Declined", "260039", "Private Event", "KW Berlin", "5.10.2026-01.01.2027", "End-to-End LED Wall Rental & Setup 14m2 Total Flat", "10/2026", "€0.00", "€20,900.00"),
    ("26-270602", "New Version Sent", "250018", "IAA Transportation 2026", "Hannover Messe", "September 14-20, 2026", "End-to-End LED Wall Rental & Setup 45m2 Flat", "09/2026", "€0.00", "€19,545.00"),
    ("26-270603", "Cancelled", "260040", "Chillventa", "Nuernberg Messe", "October 13-15, 2026", "End-to-End LED Wall Rental & Setup 20m2 Flat", "10/2026", "€0.00", "€6,980.00"),
    ("26-020701", "New Version Sent", "260041", "Retail Store", "Osnabruck, Germany", "September 30- October 28, 2026", "End-to-End LED Wall Rental & Setup 6m2 Flat", "09/2026", "€0.00", "€7,690.00"),
    ("26-260302-V2", "Approved", "250028", "Glasstec - 2026", "Messe Dusseldorf", "October 20-23, 2026", "End-to-End LED Wall Rental & Setup 7m2 Total Flat", "10/2026", "€0.00", "€2,505.00"),
    ("26-070702", "Approved", "260034", "Glasstec - 2026", "Messe Dusseldorf", "October 20-23, 2026", "End-to-End Manufacturing & Setup & Dismantling 55m2 Stand", "10/2026", "€0.00", "€19,750.00"),
    ("26-270602", "Declined", "250018", "IAA Transportation 2026", "Hannover Messe", "September 14-20, 2026", "End-to-End LED Wall Rental & Setup 45m2 Flat", "09/2026", "€0.00", "€19,545.00"),
    ("26-020701-V2", "Declined", "260041", "Retail Store", "Osnabruck, Germany", "September 30- October 28, 2026", "End-to-End LED Wall Rental & Setup 6m2 Flat", "09/2026", "€0.00", "€15,630.00"),
    ("26-070702-V2", "Approved", "260034", "Glasstec - 2026", "Messe Dusseldorf", "October 20-23, 2026", "End-to-End Manufacturing & Setup & Dismantling 55m2 Stand", "10/2026", "€2,155.77", "€19,401.93"),
    ("26-150702", "Waiting", "260042", "WindEnergy Hamburg", "Hamburg Messe", "September 22-25, 2026", "End-to-End LED Wall Rental & Setup", "09/2026", "€0.00", "€19,676.25"),
    ("26-160702", "Follow up sent", "260043", "Automechanika Frankfurt", "Messe Frankfurt", "September 8-12, 2026", "End-to-End LED Wall Rental & Setup 13.5m2 Total+Audio", None, "€693.00", "€5,562.00"),
    ("26-220701-V2", "Follow up sent", "260018", "SBC LISBON", "MEO ARENA", "Sep 29 - Oct 1, 2026", "End-to-End LED Wall an Displays Rental & Setup", "09/2026", "€1,285.00", "€11,565.00"),
    ("26-220702", "Follow up sent", "260044", "Rehacare 2026", "Dusseldorf Messe", "Sep 23-26, 2026", "End-to-End LED Wall Rental & Setup 12m2 Flat", "09/2026", "€0.00", "€5,455.00"),
    ("26-270702-V3", "Waiting", "250012", "CPHI 2026 Milano", "Fiera Milano", "October 6-8, 2026", "End-to-End LED Wall and Displays Rental & Setup", "10/2026", "€823.75", "€17,000.00"),
    ("26-280702", "Declined", "260028", "IFA BERLIN 2026", "Messe Berlin", "September 4-8, 2026", "End-to-End LED Wall and Displays Rental & Setup", "09/2026", "€0.00", "€3,560.00"),
    ("26-070802", "Declined", "260045", "South India Celebration Festival", "Berlin", "August 22-23, 2026", "End-to-End LED Wall  Rental & Setup", "08/2026", "€0.00", "€9,080.00"),
    ("26-070803", "Waiting", "260046", "Aluminium Global Exhibition", "Messe Dusseldorf", "October 6-8, 2026", "End-to-End LED Wall Rental & Setup", "10/2026", "€3,258.00", "€13,032.00"),
    ("26-070802-V2", "Declined", "260045", "South India Celebration Festival", "Berlin", "August 22-23, 2026", "End-to-End LED Wall  Rental & Setup", "08/2026", "€4,540.00", "€4,540.00"),
    ("26-170802", "Waiting", "250026", "NFL Event", "Munich Allianz Arena", "November 9-15, 2026", "End-to-End LED Wall Rental & Setup 84m2 Total Flat", "11/2026", "€0.00", "€40,640.00"),
    ("26-180802", "Waiting", "260033", "Intertabac 2026", "Messe Dortmund", "September 15 to 17, 2026", "End-to-End LED Wall and Audio Rental & Setup", "09/2026", "€0.00", "€3,040.00"),
    ("26-200802", "Waiting", "260047", "Circular Tech Awards Gala Dinner", "JW Mariott Berlin", "September 5, 2026", "End-to-End LED Wall Rental & Setup 35m2 Total Flat", "09/2026", "€0.00", "€9,730.00"),
    ("26-200803", "Waiting", "260048", "WindEnergy Hamburg", "Hamburg Messe", "September 22-25, 2026", "End-to-End LED Wall Rental & Setup", "09/2026", "€0.00", "€2,780.00"),
]


def main():
    db = SessionLocal()
    created, updated, placeholder_customers, unmapped_status, unparsed_dates = 0, 0, 0, [], []

    try:
        customers_by_external_id = {
            c.external_id: c for c in db.query(Customer).filter(Customer.external_id.isnot(None)).all()
        }
        seen_quote_numbers = {
            q[0] for q in db.query(Quotation.quote_number).all()
        }

        for row in ROWS:
            (quote_number, status_text, customer_ext_id, event_name, venue, dates_text,
             service_desc, quote_date_text, discount_text, total_text) = row

            customer = customers_by_external_id.get(customer_ext_id)
            if not customer:
                customer = Customer(external_id=customer_ext_id)
                db.add(customer)
                db.flush()
                customers_by_external_id[customer_ext_id] = customer
                placeholder_customers += 1
                print(f"Created placeholder customer for external_id {customer_ext_id}")

            status = STATUS_MAP.get(status_text)
            if not status:
                unmapped_status.append((quote_number, status_text))
                status = QuoteStatus.draft

            start_date, end_date = parse_event_dates(dates_text)
            if dates_text and not start_date:
                unparsed_dates.append((quote_number, dates_text))

            if quote_number in seen_quote_numbers:
                print(f"SKIP (duplicate quote number): {quote_number}")
                continue

            db.add(Quotation(
                quote_number=quote_number,
                customer_id=customer.id,
                event_name=event_name,
                event_venue=venue,
                event_start_date=start_date,
                event_end_date=end_date,
                event_dates_text=dates_text,
                status=status,
                currency="EUR",
                tax_rate_percent=Decimal("0"),
                service_description=service_desc,
                discount_amount=parse_money(discount_text),
                historical_total_amount=parse_money(total_text),
                quotation_date_text=quote_date_text,
            ))
            seen_quote_numbers.add(quote_number)
            created += 1

        db.commit()
        print(f"\nDone. Created {created} quotation(s), {placeholder_customers} placeholder customer(s).")
        if unmapped_status:
            print(f"\nUnmapped status values (defaulted to draft): {unmapped_status}")
        if unparsed_dates:
            print(f"\nCould not parse a structured date for {len(unparsed_dates)} row(s) (kept as event_dates_text):")
            for qn, dt in unparsed_dates:
                print(f"  {qn}: {dt!r}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
