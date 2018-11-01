import sys,os,shutil

output_filename = sys.argv[1]

for line in open(output_filename, "r").readlines():
    if line.startswith("CSVDIFF"):
        _, test_dir, l = line.split("\t")
        l = eval(l)
        for i in l:
            orig = os.path.join(test_dir,i)
            gold = os.path.join(test_dir,"gold",i)
            print(orig,gold)
            if os.path.exists(orig):
                shutil.copyfile(orig,gold)
            else:
                print("NOT FOUND",orig)

