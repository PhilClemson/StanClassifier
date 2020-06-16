import sys
import os.path
from make_json import make_outfile
from fnmatch import fnmatch
from difflib import SequenceMatcher

# Get the arguments specified on the command line when the function was called
#
# Inputs:
#       args - string containing the command line arguments
#       flag - string corresponding to a required argument
#
# Outputs:
#       arg.split(flag)[1] - string holding the value of the argument
def get_arg(args, flag):
    found = False
    for arg in args:
            if(arg.find(flag) >= 0):
                    found = True
                    return arg.split(flag)[1]
    if(found == False):
            raise Exception('Required argument {} was not found' .format(flag))

def find_files(pattern, dirs):
    res = []
    for pd in dirs:
        for d, _, flist in os.walk(pd):
            for f in flist:
                if fnmatch(f, pattern):
                    res.append(os.path.join(d, f))
    return res

def str_dist(target):
    def str_dist_internal(candidate):
        return SequenceMatcher(None, candidate, target).ratio()
    return str_dist_internal

def closest_string(target, candidates):
    if candidates:
        return max(candidates, key=str_dist(target))

def find_data_for_model(model):
    d = os.path.dirname(model)
    data_files = find_files("*.data.R", [d])
    if len(data_files) == 1:
        return data_files[0]
    else:
        return closest_string(model, data_files)

dirs=[]

args = sys.argv

author = get_arg(args, '--author=')

dirs.append(get_arg(args, '--directory='))
models = find_files("*.stan", dirs)

for model in models:
    make_outfile(model, find_data_for_model(model), author)
