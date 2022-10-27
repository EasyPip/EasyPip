import os
import json
from exp.main import *

# key = "cov", "theme"  "rediraffe", "client"
key = "pandas"
#

def search_in_file(file_name, name):
    try:
        with open(file_name, 'r', encoding='UTF-8') as f:
            content = json.load(f)
            # name = name.strip(".json")
            if content[name]["potential_require"].count(key):
                print(name)

    except Exception as e :
        print("reading error: ", file_name, e)


def filter_cache():
    cache_path = "./EasyPip/exp/cache"
    pkg_name = list()
    _files = os.listdir(cache_path)
    # os.chdir(requfile_path)
    for name in _files:
        filename = cache_path + "/" + str(name)
        suf_name = os.path.splitext(name)[0]
        # print(suf_name)
        search_in_file(filename, suf_name)



def filesList():
    cache_path = "./EasyPip/exp/cache"
    pkg_name = list()
    _files = os.listdir(cache_path)
    # os.chdir(requfile_path)
    for name in _files:
        filename = cache_path + "/" + str(name)
        suf_name = os.path.splitext(name)[0]
        # print(filename, suf_name)
        searchKeyInRequ(filename)


def searchKeyInRequ(filename):
    with open(filename, 'r', encoding='UTF-8') as f:
        line = f.readline()
        while line:
            if key in line.strip():
                print(filename)
                print(line)
                return
            line = f.readline()


def re_wri(cache_path, name):
    with open(cache_path, 'r') as fs:
        package_json = json.load(fs)
    # version_node_list = sorted(version_node_list, key=cmp_to_key(compare_version))
    ver_list = package_json[name]["version_list"]
    ver_list = sorted(ver_list, key=cmp_to_key(compare_version))


if __name__ == '__main__':
    # filesList()
    # allReFile(i = 5)
    cache_path = "./EasyPip/exp/cache/google-auth.json"
    with open(cache_path, 'r') as fs:
        package_json = json.load(fs)

    with open(cache_path, 'w') as f:
        json.dump(package_json, f, indent=2)

