import sys, re, os, glob, os.path


f = file("language_list.py", 'a')
f.write("\n")
pwd = os.getcwd()
for nomfichier in glob.glob(os.path.join(pwd,"locale","*")):
    deb, fin = nomfichier.split("locale%s"%os.sep,1)
    if fin=="CVS":
        continue
    fin= "_(\""+fin+"\")"
    print fin
    f.write(fin+"\n")
f.close()

