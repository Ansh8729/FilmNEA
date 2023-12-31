import PyPDF4 
import PyPDF2

def NoSpaces(filename): # Removes spaces from a file's name
    if filename.count(" ") > 0:
        chars = list(filename)
        newname = ""
        for char in chars:
            if char != " ":
                newname += char
        return newname
    else:
        return filename
    
def IsPDF(filename): # Checks if a file is in the PDF format
    name = (filename).split(".")
    ext = name[1]
    if ext == "pdf":
        return True
    else:
        return False
    
def Watermark(InputPDF, OutputPDF, watermark): # Watermarks the pages of a given PDF
    watermark = PyPDF4.PdfFileReader(watermark)
    PageWatermark = watermark.getPage(0)
    InputFile = PyPDF4.PdfFileReader(InputPDF)
    OutputFile = PyPDF4.PdfFileWriter()
    for page in range(InputFile.getNumPages()):
        page = InputFile.getPage(page)
        page.mergePage(PageWatermark)
        OutputFile.addPage(page)
    with open(OutputPDF, "wb") as output:
        OutputFile.write(output)

def ExtractPDF(input, output, start, end): # Extracts a specific range of pages from a PDF
    start -= 1
    reader = PyPDF2.PdfReader(input)
    writer = PyPDF2.PdfWriter()
    for page_num in range(start,end): 
        selected_page = reader.pages[page_num]
        writer.add_page(selected_page)
    with open(output,"wb") as out:
        writer.write(out)