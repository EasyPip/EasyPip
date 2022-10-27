import re
from typing import List
import time
from exp.alg.common import DEF_SYMBOLS


def flag_transfer(flag):
    if flag == ">":
        return 1
    elif flag == ">=":
        return 2
    elif flag == "==":
        return 3
    elif flag == "<":
        return 4
    elif flag == "<=":
        return 5
    elif flag == "!=":
        return 6
    elif flag == "~=":
        return 7
    else:
        return -1


def python_version_format(version):
    stage = len(re.findall("\.", version))
    if stage == 0:
        if version == "3":
            return "cp30"
        elif version == "2":
            return "cp27"
        else:
            return "cp{}0".format(version)
    if stage == 1:
        return "cp{}".format(version.replace(".", ""))
    if stage == 2:
        return "cp{}{}".format(version.split(".")[0], version.split(".")[1])


def version_compare(a, b):
    print("version_compare:  ", a, "   ", b)
    _a = int(a[2:])
    _b = int(b[2:])
    if _a>_b:
        return -1
    elif _a<_b:
        return 1
    else:
        return 0


class Link(object):
    def __init__(self, skip_list, package_name, start_node, end_node, is_skip_start, is_skip_end, python_list):
        self.skip_list = skip_list
        self.package_name = package_name
        self.start_node = start_node
        self.end_node = end_node
        self.is_skip_start = is_skip_start
        self.is_skip_end = is_skip_end
        self.python_list = python_list


class Version(object):
    def __init__(self, version, upload_time, python_require, requirement:List[Link]=None):
        self.version = version
        self.upload_time = upload_time
        self.python_require = python_require
        if requirement is None:
            self.requirement = []
        else:
            self.requirement = requirement

    def add_requirement(self, condition_list):
        # print("condition_list-----", condition_list)
        if condition_list == None:
            return
        # print("condition_list", condition_list)
        for condition in condition_list:
            if condition is None:
                continue
            else:
                #  eg. "PySocks (!=1.5.7,>=1.5.6) ; extra == 'socks'",
                # todo fix bug networkx 2.8.3: pandas extra == 'default'"
                # fix bug  "win-inet-pton ; (sys_platform == \"win32\" and python_version == \"2.7\") and extra == 'socks'" [requests]
                extra = False
                if re.search(r'extra == \'(.*)\'', condition) is not None:
                    extra = True
                    function_name = re.search(r'extra == \'(.*)\'', condition).group(1)
                    #
                    continue

                package_name, package_version_condition = split_dep_expr(condition)
                # print("condition-----", condition, package_name, package_version_condition, "all flg", end=" ")
                # print("package_name", package_name, "package_version_condition", package_version_condition)
                skip_version_list = []
                end_version = "END"
                start_version = "START"
                is_skip_start = False
                is_skip_end = True

                for single_pkg_con in package_version_condition:

                    # print(single_pkg_con.split(","), "------------")
                    for relate in single_pkg_con.split(","):
                        if relate == "":
                            continue
                        m = re.match(r'([<>=~!]+)(.*)', relate)
                        version_flag = flag_transfer(m.group(1))
                        version_base = m.group(2)
                        # print("version_flag, version_base", version_flag, version_base)
                        if version_flag == 6:  # !=
                            skip_version_list.append(version_base)
                        elif version_flag == 4: # <
                            start_version = version_base
                            is_skip_start = True
                        elif version_flag == 5: # <=
                            start_version = version_base
                            is_skip_start = False
                        elif version_flag == 2 or version_flag == 7: # >= || ~=
                            end_version = version_base
                            is_skip_end = False
                        elif version_flag == 1:  # >
                            end_version = version_base
                            is_skip_end = True
                        elif version_flag == 3: # ==
                            start_version = version_base
                            end_version = version_base
                            is_skip_start = False
                            is_skip_end = False
                        else:
                            raise ValueError("{}symbol recognition error".format(relate))

                condition = judge_con(condition)
                # print("condition:", condition)
                python_require_list = []
                python_require_potential_list = self.python_require

                final_conditiona = judge_conditions(condition)
                for cond in final_conditiona:
                    # print(cond)
                    # pickleshare 0.7.3: "pathlib2; python_version in \"2.6 2.7 3.2 3.3\""
                    python_condition = re.search(r'python_version in [\'\"](.*)[\'\"]', cond)
                    if python_condition is not None:
                        python_condition_list = python_condition.group(1).split(" ")
                        temp_python_require_potential_list = []
                        for python_version in python_condition_list:
                            python_version = "cp{}".format(python_version.replace(".", ""))
                            if python_version != " " and python_version in python_require_potential_list:
                                temp_python_require_potential_list.append(python_version)
                        python_require_potential_list = temp_python_require_potential_list.copy()
                        continue
                    # e.g. zipfile36 (>=0.1.0.0,<0.2.0.0); python_version >= "3.4.0.0" and python_version < "3.6.0.0"
                    # python_version appears twice
                    times_pyversion = cond.count("python_version", 0, len(cond))
                    # python_condition = re.search(r'python_version (.*)[\'\"](.*)[\'\"]', cond)
                    if python_condition is not None:
                        if times_pyversion ==1:
                            python_require_list, python_require_potential_list = self.pyver_condition(cond, python_require_potential_list, python_require_list)
                        else:
                            py_con_1 = re.search(r'python_version (.){0,3}(\'|\")(.*?)(\'|\")', cond).group(0)
                            # py_con_1 = re.search(r'python_version (.*)[\'\"](.*)[\'\"]', cond)
                            python_require_list1, python_require_potential_list1 = self.pyver_condition(py_con_1,
                                                                                                      python_require_potential_list,
                                                                                                      python_require_list)
                            py_con_2 = cond.replace(py_con_1, "")
                            # py_con_2 = re.search(r'python_version (.*)[\'\"](.*)[\'\"]', py_con_2)
                            python_require_list2, python_require_potential_list2 = self.pyver_condition(py_con_2,
                                                                                                        python_require_potential_list,
                                                                                                        python_require_list)
                            python_require_list = list(set(python_require_list1).union(set(python_require_list1)))
                            python_require_potential_list = list(set(python_require_potential_list1).union(set(python_require_potential_list2)))

                python_require_list = list(set(python_require_list).union(set(python_require_potential_list)))
                # print(python_require_list)
                link = Link(skip_list=skip_version_list, package_name=package_name, start_node=start_version,
                            end_node=end_version, is_skip_start=is_skip_start, is_skip_end=is_skip_end,
                            python_list=python_require_list)

                self.requirement.append(link)


    def pyver_condition(self, cond, python_require_potential_list, python_require_list):
        python_condition = re.search(r'python_version (.*)[\'\"](.*)[\'\"]', cond)
        python_condition_flag = flag_transfer(python_condition.group(1).replace(" ", ""))
        python_version = python_version_format(python_condition.group(2).replace(" ", ""))

        if python_condition_flag == 4:  # <
            python_require_potential_list = [py_version for py_version in python_require_potential_list
                                             if version_compare(py_version, python_version) == 1]
        elif python_condition_flag == 2:  # >=
            python_require_potential_list = [py_version for py_version in python_require_potential_list
                                             if version_compare(py_version, python_version) <= 0]
        elif python_condition_flag == 1:  # >
            python_require_potential_list = [py_version for py_version in python_require_potential_list
                                             if version_compare(py_version, python_version) < 0]
        elif python_condition_flag == 3:  # ==
            python_require_list.append(python_version)
        elif python_condition_flag == 6:  # !=
            python_require_potential_list.remove(python_version)
        elif python_condition_flag == 5:  # <=
            python_require_potential_list = [py_version for py_version in python_require_potential_list
                                             if version_compare(py_version, python_version) == 1]
            python_require_potential_list.append(python_version)
        else:
            raise ValueError("{},This expression is not supported".format(python_condition))
        return  python_require_list, python_require_potential_list


def split_dep_expr(expr):
    if ";" in expr:
        expr = expr.split(";")[0]
    if "@" in expr:
        cons = []
        dep = expr
        return dep, cons  # git dependency, not consider now
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
    if (not condi_flag) and len(split_groups)>1:
        # print("split_groups", split_groups )
        condition_start = len(split_groups[0])
        condi_flag = True

    cons = list()
    lolis = []

    for symbol in DEF_SYMBOLS:
        try:
            lolis.append(expr.index(symbol))
        except ValueError:
            continue
    lolis = list(sorted(set(lolis)))
    # print(lolis)

    if condi_flag:
        dep = expr[:condition_start].strip()
    else:
        if len(lolis) != 0:
            dep = expr[:lolis[0]].strip()
        else:
            dep = expr[:condition_start].strip()

    if len(lolis)==0:
        condition = expr[condition_start + 1:condition_end].strip()
        # print("ddddddddddddddd1", expr, dep, cons)
        return dep, cons

    condition = expr[lolis[0] :condition_end].strip()
    # print("expr", expr,"condition", condition , end= " ")
    if len(lolis)==2:
        con1 = expr[lolis[0]:lolis[1]]
        con1 = con1.replace(",", "").replace(" ", "")
        cons.append(con1)
        con2 = expr[lolis[1]:condition_end]
        con2 = con2.replace(",", "").replace(" ", "")
        cons.append(con2)
        return dep, cons
    cons.append(condition.replace(",", "").replace(" ", ""))
    # print("ddddddddddddddd3", expr, dep, cons)
    return dep, cons


def judge_con(condition):
    if " or " in condition:
        condition = condition.split("or")
    elif " and " in condition:
        condition = condition.split("and")
    else:
        condition = [condition]
    return condition


def judge_conditions(condition=list()):
    final_conditiona = list()
    for cond in condition:
        second_judge_con = judge_con(cond)
        if len(second_judge_con) > 1:
            cons = judge_con(cond)
            final_conditiona.extend(cons)
        else:
            final_conditiona.extend(second_judge_con)
    return final_conditiona




def test_one_packgev():
    import urllib.request
    import json
    from exp.alg.build import parse_python_require
    version = "1.0.2"
    url = "https://pypi.org/pypi/{}/{}/json".format("tomli", version)
    response = urllib.request.urlopen(url)
    content = response.read()
    # releases_all = json.loads(content)["releases"][version]
    releases_all = json.loads(content)["urls"]
    python_require = parse_python_require(releases_all)
    require_dist = json.loads(content)["info"]["requires_dist"]
    upload_time = json.loads(content)["urls"][0]["upload_time"]

    # build version node object
    version_node = Version(version=version, python_require=python_require, upload_time=upload_time)
    version_node.add_requirement(require_dist)




if __name__ == '__main__':
    # test_one_packgev()
    # package = "pytest-cov>=2.12.1"
    # package2 = "pytest-randomly"
    # re_package = re.search(r'([a-z]*[A-Z]*)([<>=~!]+.*)', package)
    # re_package2 = re.search(r'([a-z]*[A-Z]*)([<>=~!]+.*)', package2)
    # print(re_package)
    # aaaa = "debugpy >= 1.0"
    # s_groups = aaaa.split(" ")
    # print(s_groups, type(s_groups), s_groups[0])
    dep_pack, cons =split_dep_expr("chardet (<5,>=3.0.2)")
    # dep_pack, cons = sr("debugpy >= 1.0")
    print("dep_pack, cons:  ",dep_pack, cons )
    dep_pack, cons = split_dep_expr("debugpy >= 1.0")
    print("dep_pack, cons:  ", dep_pack, cons)
    dep_pack, cons = split_dep_expr("numpy")
    print("dep_pack, cons:  ", dep_pack, cons)
    dep_pack, cons = split_dep_expr("numpy>=2")
    print("dep_pack, cons:  ", dep_pack, cons)
    dep_pack, cons = split_dep_expr("chardet <5,>=3.0.2")
    print("dep_pack, cons:  ", dep_pack, cons)