import datetime
from dateutil.parser import parse
from datetime import datetime

def ISOtoDate(date):
    months = {
    "01": "January",
    "02": "February",
    "03": "March",
    "04":"April",
    "05":"May",
    "06":"June",
    "07":"July",
    "08":"August",
    "09":"September",
    "10":"October",
    "11":"November",
    "12":"December"}
    datestr = str(datetime.fromisoformat(date))
    date2 = list(datestr)[0:10]
    daynum = ''.join(date2[8]+date2[9])
    if date2[9] == "1":
        day = daynum+"st"
    elif daynum == "02" or daynum == "22":
        day = daynum+"st"
    elif daynum == "03" or daynum == "23":
        day = daynum+"rd"
    else:
        day = daynum +"th"
    if day[0] == "0":
        day = list(day)
        day = day[1:6]
        day = ''.join(day)
    month = months[''.join(date2[5]+date2[6])]
    year = ''.join(date2[0:4])
    return f"{day} {month} {year}"

def convert_to_datetime(input_str, parserinfo=None):
    return parse(input_str, parserinfo=parserinfo)