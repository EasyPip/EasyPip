import urllib.request
import re
from exp.modules.package_modules import Package
from exp.modules.version_modules import Version
from exp.alg.common import *
from exp.alg.crawl_page import *
from functools import cmp_to_key
import operator


def write_cache(package_json):
    for key in package_json.keys():
        cache_path = BASE_PATH + "exp/cache/{}.json".format(key)
        with open(cache_path, 'w') as f:
            json.dump(package_json, f, indent=2)
    return


def time_cmp(t1, t2):
    if t1.upload_time < t2.upload_time:
        return 1
    else:
        return -1


def python_released_search_by_time(upload_time):
    package_release_time = upload_time.split("T")[0]
    if package_release_time > "2021-10-04":
        return "cp310"
    elif package_release_time > "2020-10-05":
        return "cp39"
    elif package_release_time > "2019-10-14":
        return "cp38"
    elif package_release_time > "2018-06-27":
        return "cp37"
    elif package_release_time > "2016-12-23":
        return "cp36"
    elif package_release_time > "2015-09-13":
        return "cp35"
    elif package_release_time > "2014-03-17":
        return "cp34"
    elif package_release_time > "2012-09-29":
        return "cp33"
    elif package_release_time > "2011-12-20":
        return "cp32"
    elif package_release_time > "2009-06-26":
        return "cp31"
    return "cp30"


def gen_package_json(package: Package):
    res = {
        package.name: {
            "summary": package.summary,
            "potential_require": package.potential_require,
            "version_list": [
                {
                    "version": package.version_list[i].version,
                    "upload_time": package.version_list[i].upload_time,
                    "python_require": package.version_list[i].python_require,
                    "requirement": [
                        {
                            "skip_list": package.version_list[i].requirement[j].skip_list,
                            "package_name": package.version_list[i].requirement[j].package_name,
                            "start_node": package.version_list[i].requirement[j].start_node,
                            "end_node": package.version_list[i].requirement[j].end_node,
                            "is_skip_start": package.version_list[i].requirement[j].is_skip_start,
                            "is_skip_end": package.version_list[i].requirement[j].is_skip_end,
                            "python_list": package.version_list[i].requirement[j].python_list
                        } for j in range(len(package.version_list[i].requirement))
                    ],
                    "combine": False
                } for i in range(len(package.version_list))
            ],
            "build_version": BUILD_VERSION
        }
    }
    # merge node
    for i in range(len(package.version_list)-1):
        content = res[package.name]["version_list"]
        if content[i]["python_require"] == content[i+1]["python_require"] and content[i]["requirement"] == content[i+1]["requirement"]:
            content[i+1]["combine"] = True

    return res


def request(url):
    retry = 5
    while retry>0:
        try:
            response = urllib.request.urlopen(url, timeout=30)
            return response
        except Exception as e:
            if hasattr(e, "code"):
                if e.code == 404:
                    return None
            print(e)
            retry -= 1
            time.sleep(5)
    raise ConnectionError("{} consecutive requests Failed, we had tried 5 times".format(url))


def get_package_info(package_name):
    """
    build package
    :param package_name:
    :return:
    """
    url = "https://pypi.org/pypi/{}/json".format(package_name)

    content = crawl_content(url)
    if not content:
        print("fail to enter: ", url)
        return None
    version_list = json.loads(content)["releases"]
    summary = json.loads(content)["info"]["summary"]
    return {"version_list": version_list,
            "summary": summary}


def parse_python_require(release_all):
    """
    release the depended Pyhton version
    :return:
    """
    python_require = set()
    contain_source = False
    if len(release_all) == 0:
        raise ValueError("release is null")
    python_require_ = list()
    for release_all_item in release_all:
        if release_all_item["requires_python"] is not None:
            require = release_all[0]["requires_python"].replace(" ", "")
            # deal abnormal requires_python
            total_python_version = []
            # print(require, "===require===", type(require)) # >="3.5" require <class 'str'>
            require = require.replace('\"', '')
            if require == "3" or require == ">=3":
                for i in range(0, 12, 1):
                    total_python_version.append("cp3{}".format(i))
                return total_python_version
            if require=="2":
                for i in range(4, 8, 1):
                    total_python_version.append("cp2{}".format(i))
                return total_python_version
            for i in range(4, 8, 1):
                total_python_version.append("cp2{}".format(i))
            for i in range(0, 12, 1):
                total_python_version.append("cp3{}".format(i))

            for condition in require.split(","):
                if len(condition) == 0:
                    continue
                for symbols in DEF_SYMBOLS:
                    try:
                        symbol = symbols
                        break
                    except ValueError:
                        continue
                matches = re.match(r'([<>!=~])=*(.*)', condition)
                version_base_split = matches.group(2).split(".") # [3.6]
                if len(version_base_split) == 1:  # urllib3 1.23版本 存在<4的情况
                    if version_base_split[0] == "2":
                        return total_python_version
                    version_name = "cp{}0".format(version_base_split[0])
                else:
                    version_name = "cp{}{}".format(version_base_split[0], version_base_split[1])
                if "dev" in version_name:
                    version_name = version_name.replace("dev", "")  # 存在 cp19dev的情况
                if version_base_split[0] >= '4':  # urllib3 1.23版本
                    continue
                if symbol == "=":
                    python_require.add(version_name)
                elif symbol == "!":
                    if version_name in total_python_version:
                        total_python_version.remove(version_name)
                elif symbol == ">=":
                    if version_name in total_python_version:
                        idx = total_python_version.index(version_name)
                        total_python_version = total_python_version[idx:]
                elif symbol == "<=":
                    if version_name in total_python_version:
                        idx = total_python_version.index(version_name)
                        total_python_version = total_python_version[:idx]
                elif symbol == "~=":
                    if version_name in total_python_version:
                    # split into two parts: >=,  the first part >=
                        idx = total_python_version.index(version_name)
                        total_python_version = total_python_version[idx:]
                    # the second <
                    second_python_v_int = int(version_base_split[1])
                    while second_python_v_int < 12:
                        second_python_v_int = second_python_v_int + 1
                        second_python_v = str(second_python_v_int)
                        version_name = "cp{}{}".format(version_base_split[0], second_python_v)
                        if version_name in total_python_version:
                            idx = total_python_version.index(version_name)
                            total_python_version = total_python_version[:idx]
                elif symbol == ">" :
                    if version_name in total_python_version:
                    #     second_python_v = str(int(version_base_split[1])-1)
                    #     version_name = "cp{}{}".format(version_base_split[0], second_python_v)
                        idx = total_python_version.index(version_name) + 1
                        total_python_version = total_python_version[idx:]
                    # print("symbol > ---", total_python_version, version_name)
                elif symbol == "<":

                    if version_name in total_python_version:
                        idx = total_python_version.index(version_name)
                        total_python_version = total_python_version[:idx]
                else:
                    raise ValueError("{}unrecognizable python require  symbol{}".format(condition, symbol))
            # print(list(set(python_require).union(set(total_python_version))))
            # return list(set(python_require).union(set(total_python_version)))
            python_require_ = list(set(python_require_).union(list(set(python_require).union(set(total_python_version)))))

    if len(python_require_):
        return python_require_

    for release in release_all:
        # print("release ", release)
        python_version_info = release["python_version"]
        # print("python_version_info", python_version_info)
        upload_time = release["upload_time"]
        if re.search("cp", python_version_info) is not None:
            python_require.add(python_version_info)
        elif "py" in python_version_info:
            if "py3" in python_version_info.split("."):
                latest_python_version = python_released_search_by_time(upload_time)
                # print("latest_python_version", latest_python_version)
                for i in range(0, 12, 1):
                    python_version = "cp3{}".format(i)
                    python_require.add(python_version)
                    if python_version == latest_python_version:
                        break
            if "py2" in python_version_info.split("."):
                python_require.add("cp27")
        elif re.search("\.", python_version_info) is not None:
            python_version = "cp" + python_version_info.replace(".", "")
            python_require.add(python_version)
        elif python_version_info == "any":
            contain_source = True
            continue
        elif python_version_info == "source":
            contain_source = True
            continue
        else:
            contain_source = True
            print("{}Unable to handle Pyhton version identification tasks in release, all handled by default".format(release))

    # print("python_require", python_require)
    if len(python_require) == 0 and contain_source:
        python_require = {"cp27"}
        for i in range(0, 12, 1):
            python_require.add("cp3{}".format(i))

    return list(python_require)


def build_version_node(package_name, version):
    """
    build package version node
    :param package_name:
    :param version:
    :return:
    """
    print("building {}-{}".format(package_name, version))
    url = "https://pypi.org/pypi/{}/{}/json".format(package_name, version)
    content = crawl_content(url)
    if not content:
        print("no content url", url)
    releases_all = json.loads(content)["urls"]
    python_require = parse_python_require(releases_all)
    require_dist = json.loads(content)["info"]["requires_dist"]
    # print(require_dist)
    upload_time = json.loads(content)["urls"][0]["upload_time"]

    # build version node object
    version_node = Version(version=version, python_require=python_require, upload_time=upload_time)
    # print("require_dist", require_dist)
    version_node.add_requirement(require_dist)

    return version_node

def compare_version(a, b):
    a =a.version
    b = b.version
    _a = a.split(".")
    _b = b.split(".")
    _a_size = len(_a)
    _b_size = len(_b)
    for i in range(min(_a_size, _b_size)):
        try:
            if int(_a[i]) > int(_b[i]):
                return -1
            elif int(_a[i]) < int(_b[i]):
                return 1
            else:
                continue
        except:
            if _a[i] > _b[i]:
                return -1
            elif _a[i] < _b[i]:
                return 1
            else:
                continue

    return 0


def build_package(package_name):
    # get all version
    package_info = get_package_info(package_name)

    version_node_list = []

    for version in package_info['version_list'].keys():

        if len(package_info['version_list'][version]) == 0:
            continue
        else:
            try:
                version_node = build_version_node(package_name, version)
            except Exception as e:
                print(e)
                print("build failed, package_name :", package_name, " version: ", version)
            version_node_list.append(version_node)

        # version_node_list = sorted(version_node_list, key=functools.cmp_to_key(time_cmp))
        version_node_list = sorted(version_node_list, key=cmp_to_key(compare_version))#

    potential_require = []
    for version_node in version_node_list:
        for require in version_node.requirement:
            if require.package_name in potential_require:
                continue
            else:
                potential_require.append(require.package_name)

    package = Package(name=package_name, summary=package_info["summary"],
                      version_list=version_node_list,
                      potential_require=potential_require)

    return package


def build(build_package_list, deep_build=True, build_update=True, visited_list=None):
    """
    :param visited_list:
    :param build_update:
    :param build_package_list:
    :param deep_build: can be used for future long dependency
    :return:
    """

    if visited_list is None:
        visited_list = list()
    # print(build_package_list)
    for package_name in build_package_list:
        package_name = package_name.replace(" ", "")
        package_name = package_name.lower()
        if "[" in package_name:
            package_name = package_name.split("[")[0]
        if package_name in visited_list:
            continue
        if "-nightly" in package_name:
            continue

        try:
            package_json = read_cache(package_name)
        except:
            raise ValueError(package_name)

        build_switch = False
        if package_json is not None:
            if build_update:
                if 'build_version' in package_json and package_json['build_version'] == BUILD_VERSION:
                    print("{}The cache of the same version already exists, skip  ".format(package_name))
                else:
                    print("{}The version is inconsistent. Update is started".format(package_name))
                    build_switch = True
            else:
                print("{} the cache exists, skip".format(package_name))
        elif package_name in white_list:
            print("{} exists in whitelist, skip it".format(package_name))   # 之后都不遍历了
            continue
        else:
            print("{} does not exists, tart building".format(package_name))
            build_switch = True

        if build_switch:
            if len(package_name.strip(" ")) == 0:
                continue
            if get_package_info(package_name) is None:
                print("{}Does not exist, 404 skipped".format(package_name))
                print("A missing third-party library is declared: ", package_name)
                log.info("A missing third-party library is declared: {}".format(package_name))
                exit()
            package = build_package(package_name)
            write_package_json = gen_package_json(package)
            write_cache(write_package_json)
            package_json = write_package_json[package_name]

        visited_list.append(package_name)

        if deep_build:
            potential_require = package_json["potential_require"]
            print("Start building transitive dependencies for{}, they are {}".format(package_name, potential_require))
            log.info("Start building transitive dependencies for{}, they are {}".format(package_name, potential_require))
            build(potential_require, deep_build=False, build_update=build_update, visited_list=visited_list)


def parsssse_expr(expr):
    if ";" in expr:
        expr = expr.split(";")[0]
    if "@" in expr:
        dep = expr
        return dep, ""  # git dependency, not consider now

    expr = expr.strip()
    condition_start = len(expr)
    condition_end = condition_start
    condi_flag = False
    try:
        condition_start = expr.index("(")
        condition_end = expr.index(")")
        condi_flag = True
    except:
        pass
    try:
        condition_start = expr.index("[")
        condition_end = expr.index("]")
        condi_flag = True
    except:
        pass
    split_groups = expr.split(" ")
    if (not condi_flag) and len(split_groups) > 1:
        # print("split_groups", split_groups )
        condition_start = len(split_groups[0])
        condi_flag = True

    lolis = []
    flag_symbol = ""
    for symbol in DEF_SYMBOLS:
        try:
            lolis.append(expr.index(symbol))
            flag_symbol = symbol
        except ValueError:
            continue
    lolis = list(sorted(set(lolis)))
    # print(lolis, expr)
    if condi_flag:
        if len(lolis)!=0:
            if condition_start > lolis[0]:
                condition_start = lolis[0]
        dep = expr[:condition_start].strip()
    else:
        if len(lolis) != 0:
            dep = expr[:lolis[0]].strip()
        else:
            dep = expr[:condition_start].strip()
    if len(lolis) == 0:
        return dep, flag_symbol

    return dep, flag_symbol

if __name__ == '__main__':
    build(["tensorflow-serving-api-gpu"])
