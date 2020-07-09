import os, sys, re, codecs, shutil, markdown

TARGET_DIR = "/home/burak/Documents/dersblog/sk"

if __name__ == "__main__": 
 
    if len(sys.argv) == 1: exit()

    if sys.argv[1] == 'html':
        
        fr = os.getcwd()
        cmd = "python /home/burak/Documents/kod/rsync.py '%s' '%s' --ignore-list=.md,.git,.zip,.pdf" % (fr, TARGET_DIR)
        print (cmd)
        os.system(cmd)
