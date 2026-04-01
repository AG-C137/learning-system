import zipfile
import xml.etree.ElementTree as ET

path = "books/Solano_Osteopatiya_dlya_malyishey_RuLit_Net_192301.epub"

with zipfile.ZipFile(path) as z:
    data = z.read("META-INF/container.xml")
    root = ET.fromstring(data)

    rootfile = root.find(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
    print("OPF:", rootfile.attrib["full-path"])

    opf_data = z.read(rootfile.attrib["full-path"])
    root = ET.fromstring(opf_data)

    title = root.find(".//{http://purl.org/dc/elements/1.1/}title")
    author = root.find(".//{http://purl.org/dc/elements/1.1/}creator")

    print("TITLE:", title.text if title is not None else None)
    print("AUTHOR:", author.text if author is not None else None)
