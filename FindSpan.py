import codecs

filename = "./Tim-Round1/THYME-Analysis/ID001_path_002/ID001_path_002"
file = codecs.open(filename, "r", "utf-8")
content = file.read()

print (content[164:178])

