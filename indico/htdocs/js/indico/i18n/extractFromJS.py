import sys, os, re, shutil


def searchFiles(dirPath):
    files = []
    for elem in os.listdir(dirPath):
        fullPath = os.path.join(dirPath, elem)

        if elem in ['pack', 'CVS', 'i18n']:
            pass
        elif elem[-3:] == '.js':
            files.append(fullPath)
        elif os.path.isdir(fullPath):
            files.extend(searchFiles(fullPath))

    return files


def findOccurrences(files):

    dollarT = re.compile('\$T\(["\'](.*?)[\'"]\)')
    first = True

    occur = {}

    for fname in files:
        lines = open(fname, 'r').readlines()
    
        lnumber = 1

        for l in lines:
            matches = dollarT.findall(l)
            if matches:
                for m in matches:
                    if occur.has_key(m):
                        occur[m].append((fname, lnumber))
                    else:
                        occur[m] = [(fname, lnumber)]
            lnumber += 1

    return occur

def preserveValues(dstFile):
    values = {}
    defline = re.compile('\s*"(.*?)"\s*:\s*"(.*?)"\s*,')
    
    f = open(dstFile, 'r')
    lines = f.readlines()

    for l in lines:
        m = defline.match(l)
        if m:
            values[m.group(1)] = m.group(2)

    f.close()
    return values

if __name__ == '__main__':

    if len(sys.argv) != 3:
        print "Usage: %s <source_dir> <language_code>" % sys.argv[0]
        sys.exit(0)
        
    fList = searchFiles(sys.argv[1])

    dstFile = '%s.js' % sys.argv[2]

    if os.path.isfile(dstFile):
        # try merging
        # but backup first
        shutil.copyfile(dstFile, dstFile+'.old')
        values = preserveValues(dstFile)
    else:
        values = {}

    outF = open(dstFile, 'w')
    occur = findOccurrences(fList)

    print >> outF, "dictionaries.%s = {\n" % sys.argv[2]

    first = True

    for occ, places in occur.iteritems():
        if not first:
            print >> outF, ",\n"
        else:
            first = False
        for (fname, lnumber) in places:
            print >> outF, '    //%s line %s' % (fname, lnumber)

        if values.has_key(occ):
            value = '"%s"' % values[occ]
        else:
            value = 'null'
            
        print >> outF, '    "%s": %s' % (occ, value), 


    print >> outF, '\n};\n'
