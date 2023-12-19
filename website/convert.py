import datetime
from dateutil.parser import parse
from datetime import datetime

def ISOtoDate(date): # Reformats a date in the ISO format into a human-readable format
    # Dictionary mapping month numbers to month names
    months = {
        "01": "January",
        "02": "February",
        "03": "March",
        "04": "April",
        "05": "May",
        "06": "June",
        "07": "July",
        "08": "August",
        "09": "September",
        "10": "October",
        "11": "November",
        "12": "December"
    }

    # Convert ISO format to a string
    datestr = str(datetime.fromisoformat(date))

    # Extract day, month, and year components
    datenums = list(datestr)[0:10]
    daynum = ''.join(datenums[8] + datenums[9])

    # Determine day suffix
    if datenums[9] == "1":
        day = daynum + "st"
    elif daynum == "02" or daynum == "22":
        day = daynum + "nd"
    elif daynum == "03" or daynum == "23":
        day = daynum + "rd"
    else:
        day = daynum + "th"

    # Remove leading zero if present
    if day[0] == "0":
        day = list(day)
        day = day[1:6]
        day = ''.join(day)

    # Get the month name
    month = months[''.join(datenums[5] + datenums[6])]
    
    # Get the year
    year = ''.join(datenums[0:4])

    # Return final string
    return f"{day} {month} {year}"

def convert_to_datetime(input_str, parserinfo=None): # Converts date string into datetime ISO format
    return parse(input_str, parserinfo=parserinfo)
