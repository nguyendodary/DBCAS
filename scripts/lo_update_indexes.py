# -*- coding: utf-8 -*-
"""Update DOCX indexes (TOC, list of figures/tables) with LibreOffice UNO.

Usage (LibreOffice python):
  python lo_update_indexes.py <name>
Expects C:/tmp/dbcas_word/<name>.docx and writes <name>-lo.docx/.pdf.
"""
import sys
import time
from pathlib import Path

import uno
from com.sun.star.beans import PropertyValue

NAME = sys.argv[1]
DIR = Path(r"C:\tmp\dbcas_word")
SRC = DIR / (NAME + ".docx")
OUT = DIR / (NAME + "-lo.docx")
PDF = DIR / (NAME + "-lo.pdf")


def prop(name, value):
    p = PropertyValue()
    p.Name = name
    p.Value = value
    return p


local = uno.getComponentContext()
resolver = local.ServiceManager.createInstanceWithContext(
    "com.sun.star.bridge.UnoUrlResolver", local)
ctx = None
for _ in range(40):
    try:
        ctx = resolver.resolve(
            "uno:socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext")
        break
    except Exception:
        time.sleep(0.5)
assert ctx is not None, "cannot connect to soffice"
desktop = ctx.ServiceManager.createInstanceWithContext(
    "com.sun.star.frame.Desktop", ctx)
url = uno.systemPathToFileUrl(str(SRC))
doc = desktop.loadComponentFromURL(url, "_blank", 0, (prop("Hidden", True),))
assert doc is not None, "cannot open " + str(SRC)

indexes = doc.getDocumentIndexes()
print("indexes", indexes.getCount())
for i in range(indexes.getCount()):
    indexes.getByIndex(i).update()
doc.refresh()
print("indexes updated")

doc.storeToURL(uno.systemPathToFileUrl(str(OUT)),
               (prop("FilterName", "MS Word 2007 XML"),))
print("saved", OUT)
doc.storeToURL(uno.systemPathToFileUrl(str(PDF)),
               (prop("FilterName", "writer_pdf_Export"),))
print("pdf", PDF)
doc.close(True)
print("done")
