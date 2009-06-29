import sys
try:
    from MaKaC.common.timerExec import toExec
except ImportError, e:
    print "ImportError:%s"%e
    sys.exit(0)
            
### MAIN
if __name__ == "__main__":
    log=""
    if len(sys.argv) == 2:
        log = sys.argv[1]
    te = toExec(log)
    te.execute()
    



