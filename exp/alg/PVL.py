from exp.alg.common import *
import re
from collections import Counter

def version_compare(a, b):
    _a = a.split(".")
    _b = b.split(".")
    _a_size = len(_a)
    _b_size = len(_b)
    min_lens = min(_a_size, _b_size)
    max_lens = max(_a_size, _b_size)
    for i in range(min_lens):
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
    # lens_diff = max_lens - min_lens
    if _a_size > _b_size:
        if _a[i] > '0':
            return -1
        if _a[i] == '0':
            return -1
    else:
        if _b[i] > '0':
            return 1
        if _b[i] == '0':
            return 1
    return 0


# Determine if the version is real
def is_real_version(package, version):
    version = version.strip()
    package = package.strip()
    req = read_cache(package)
    try:
        version_list = req["version_list"]
    except Exception as e:
        print("=============================error cooured=======")
        print(package, "Determine if the version is real")
        print(e)
    ver_list = list()
    for _version in version_list:
        ver_list.append(_version["version"])
    if version in ver_list:
        return True
    return False


def find_version_idx(package, version):
    version = version.strip()
    package = package.strip()
    req = read_cache(package)
    if version == 'START':
        return 0, "null"
    if version == 'END':
        return len(req["version_list"]) - 1, "null"
    try:
        version_list = req["version_list"]
    except Exception as e:
        print("=============================error cooured=======")
        print(package, version)
        print(e)
        # exit()
        return package, version
    p = 0
    # print("63version: ", version)
    for _version in version_list:

        if version_compare(_version["version"], version) == 1:
            break
        if _version["version"] == version:
            # print("=====version", p)
            break
        p += 1

    if p>=len(version_list):
        p = len(version_list)-1
    return p, _version["version"]


def parse_requirement(require):
    left_idx = 0
    right_idx = 0

    require = require.replace("\n", "")
    # print("require______", require)
    package_name = re.match(r'([^><=!~]*)([><=!~]+)([^><=!~]*)', require).group(1)
    package_name = package_name.lower()
    try:
        extra_name = "[" + re.findall(r'\[(.*?)\]', package_name)[0] + "]"
        package_name = package_name.replace(extra_name, '')
        package_name = package_name.strip()
        # print("package name with extra file", package_name, extra_name)
    except:
        pass
    require_list = require.split(",")
    # print("package_name: 56  ", package_name)
    # print("require_list: 93", require_list, end=" ")
    left_idx_lis = list()
    right_idx_lis = list()

    for _require in require_list:
        # if "python_version"in _require:
        # print("_require: 96", _require)
        re_res = re.match(r'([^><=!~]*)([><=!~]+)([^><=!~]*)', _require)
        # print("re_res", re_res)
        p_symbol = re_res.group(2)
        p_version = re_res.group(3)
        version_idx,version_flag = find_version_idx(package_name, p_version)

        # print("version_idx, p_version, p_symbol, version_flag",  version_idx, p_version, p_symbol, version_flag)
        if p_symbol == "==":
            if "*" in p_version:
                left_idx, left_version_flag = find_version_idx(package_name, p_version.replace("*", "9999"))
                left_idx_lis.append(left_idx)
                right_idx, right_version_flag = find_version_idx(package_name, p_version.replace("*", ""))
                right_idx_lis.append(right_idx)
            else:
                left_idx = version_idx
                left_idx_lis.append(left_idx)
                right_idx = version_idx
                right_idx_lis.append(right_idx)
        elif p_symbol == ">=":
            right_idx = version_idx
            right_idx_lis.append(right_idx)
        elif p_symbol == "<=":
            left_idx = version_idx
            left_idx_lis.append(left_idx)
            right_idx, right_version_flag = find_version_idx(package_name, '0.0.0')
            right_idx_lis.append(right_idx)
        elif p_symbol == ">":
            if p_version != version_flag:
                right_idx = version_idx
            else:
                right_idx = version_idx - 1
            right_idx_lis.append(right_idx)
        elif p_symbol == "<":
            # print(">>>>>>>package_name, p_version", package_name, p_version)
            if p_version != version_flag:
                left_idx = version_idx
            else:
                left_idx = version_idx + 1
            # print(">>>>>>>package_name, left_idx, version_idx", left_idx, version_idx)
            left_idx_lis.append(left_idx)
            right_idx, right_version_flag = find_version_idx(package_name, '0.0.0')
            right_idx_lis.append(right_idx)
        elif p_symbol =="~=":
            # print("~==", _require)
            _versions = p_version.split('.')
            # print(_versions)
            max_p_version = ""
            flag_index = len(_versions)-2
            for index, ve in enumerate(_versions):
                if index == flag_index:
                    ve = int(ve)+1
                    ve = str(ve)
                if index>0:
                    max_p_version = max_p_version + "." + ve
                else:
                    max_p_version = ve
            # print(max_p_version)
            left_idx, left_version_flag = find_version_idx(package_name, max_p_version)
            left_idx_lis.append(left_idx)
            # if p_version!= left_version_flag:

            right_idx = version_idx + 1
            right_idx_lis.append(right_idx)
            # print("left_idx, left_version_flag, right_idx", left_idx, left_version_flag, right_idx)
            # print(_require, "p_version ,max_p_version", p_version ,max_p_version)
        else:
            log.info("{}the current symbol is not supported".format(p_symbol))
        # print("package_name, left_idx, right_idx", package_name, left_idx, right_idx)
        # print("left_idx_lis", left_idx_lis, "right_idx_lis", right_idx_lis)
    # if package_name == "numpy":
    #     print(package_name, left_idx, right_idx)
    if len(left_idx_lis):
        # print("left_idx_lis", left_idx_lis)
        left_idx = max(left_idx_lis)
    if len(right_idx_lis):
        # print("right_idx_lis", right_idx_lis)
        right_idx = min(right_idx_lis)
    return package_name, left_idx, right_idx


class PVL(object):
    '''
    PVL: package version link (temp name)
    '''

    def __init__(self, graph, init_package):
        self.monitor_package = None
        self.g = graph
        self.require = init_package
        self.init_left_idx = dict()
        self.init_right_idx = dict()
        self.left_idx = dict()
        self.right_idx = dict()
        self.python_require = set()
        self.init_pkg_name = set()
        self.init()
        log.info("initial package information：{}".format(init_package))
        self.conflict_root_node = ""
        self.reco_idx = {}
        self.tran_con_pack = ""
        self.reco_python = ""


    def init(self):

        for _require in self.require:
            # print("_require::::")
            package, left_idx, right_idx = parse_requirement(_require)
            # print(f"{_require}, left_idx:, {left_idx}, right_idx: {right_idx}",)
            self.init_pkg_name.add(package)
            # print("PVL  initing: ", package, left_idx, right_idx )
            log.info("name: {} left_idx:{} right_idx: {}".format(package, left_idx, right_idx))
            package = package.strip()
            self.init_left_idx[package] = left_idx
            self.init_right_idx[package] = right_idx

        for package in self.g.conflict_top_list:
            package = package.strip()
            self.left_idx[package] = -1
            self.right_idx[package] = -1

        temp_node_list = []
        for node in self.g.conflict_top_list:
            node = node.strip()
            if node not in self.g.source_graph.keys():
                node = node.strip()
                self.left_idx[node] = 0
                self.right_idx[node] = len(read_cache(node)['version_list']) - 1


        # print("self.init_left", self.init_left_idx)
        for node in self.init_left_idx.keys():
            node = node.strip()

            self.left_idx[node] = self.init_left_idx[node]
            self.right_idx[node] = self.init_right_idx[node]


        python_require_total_list = ["cp27"]
        for i in range(3, 12):
            python_require_total_list.append("cp3{}".format(i))

        python_require_set = set(python_require_total_list)
        for node in self.init_left_idx.keys():
            node_python_require = set()

            for node_idx in range(self.init_left_idx[node], self.init_right_idx[node]+1):
                try:
                    node_python_require = node_python_require.union(read_cache(node)['version_list'][node_idx]['python_require'])
                except:
                    print(node, node_idx)
                    print("==========================error occured===========")
                    print(read_cache(node)['version_list'])
                    print(read_cache(node)['version_list'][node_idx])
                    print(read_cache(node)['version_list'][node_idx]['python_require'])

            python_require_set = python_require_set.intersection(node_python_require)
            if len(python_require_set):
                print("python_require_set", node, python_require_set, node_python_require)
            else:
                print("000000000000:", node, node_python_require, python_require_set)


        python_require_list = list(python_require_set)

        # print(node, "python_require_set", python_require_set,node_python_require )
        #
        python_require_list.sort(key=lambda x:int(x[2:]), reverse=True)
        self.python_require = python_require_list
        # print("=======================PVL=======================")
        # print(self.require )
        # print(self.init_left_idx)
        # print(self.init_right_idx)
        # print(self.left_idx )
        # print(self.right_idx )
        # print(self.python_require)
        # print(self.init_pkg_name )
        # print("self.g.conflict_top_list", self.g.conflict_top_list)
        # print("self.g.conflict_top_list:",  self.g.conflict_top_list)
        # print("self.g.source_graph.keys()", self.g.source_graph.keys())
        # print("====================PVL init=====================")


    def package_conflict_check(self, monitor_package=None, python_limit=None):
        # print("python_limit : ", python_limit)
        left_idx = self.left_idx.copy()
        right_idx = self.right_idx.copy()
        self.monitor_package = monitor_package
        if len(self.python_require) == 0:
            log.info("The default package could not find a Python version that meets the criteria")
            return None

        if python_limit is not None:
            search_python_list = list(set(python_limit).intersection(set(self.python_require)))
        else:
            search_python_list = self.python_require
        print("search_python_list", search_python_list, "python_require", self.python_require)

        for python_version in search_python_list:
            # print("checking conflict left_idx", left_idx)
            # print("checking conflict right_idx", right_idx)
            # print("checking conflict python_version ", python_version)
            wanted = {}
            for i in right_idx:
                wanted.update({i: right_idx.get(i)+1 - left_idx.get(i)})
            sum_val = 1
            # for key, item in wanted.items():
            #     if item>1:
            #         print("(", key, item, ")", end="  ")
            # print()
            # #     sum_val = sum_val* item
            # print(len(wanted), wanted)
            print("len(left_idx), len(right_idx)", len(left_idx), len(right_idx))
            print("left_idx", left_idx)
            print("right_idx", right_idx)
            print("python_version", python_version)
            res = self.package_conflict_dfs(0, left_idx, right_idx, dict(), python_version)
            # if self.res_all is None:
            if res is None:
                self.reco_idx = dict()
                log.info(" If the Python version is set to {}, no solution is available".format(python_version))
            else:
                self.reco_python = python_version
                log.info("If the Python version is set to {},the recommended result is {}".format(python_version, res))
                return res
        return None

    def package_reco(self, monitor_package=None, python_limit=None): # ['cp37']):
        """
        recommends a reasonable set of packages given the constraints
        :return:
        """
        log.state("Staarting ")
        # print("monitor_package", monitor_package)
        res = self.package_conflict_check(monitor_package=monitor_package, python_limit=python_limit)
        if res is not None:
            redunt_res = list(self.init_pkg_name - set(self.g.conflict_node_set))
            # print("self.init_pkg_name", self.init_pkg_name) # 初始化的包
            # print("self.g.conflict_node_set", self.g.conflict_node_set)  # 排序后的结果
            log.info("Recommended package version：{}".format(res))
            print("res:::", res, "redunt_res", redunt_res)

        else:
            print("Failed to find a result", self.conflict_root_node)
            log.info("Failed to find a result")
        return res

    def package_conflict_dfs(self, package_idx, left_idx, right_idx, reco_dict, python_version):
        # print("package_idx:", package_idx, ": left_idx:", left_idx, "right_idx: ",  right_idx, "reco_dict: ", reco_dict, ":python_version:", python_version)
        """
        :param python_version:  traversal version of Python
        :param package_idx: The Nth packet in the topological sort
        :param left_idx:
        :param right_idx:
        :return:
        """
        if package_idx >= len(self.g.conflict_top_list):
            log.info("the search ends when a feasible solution is found")
            # self.res_all.append(reco_dict)
            # print("self.res_all", len(self.res_all), self.res_all[-1])
            return reco_dict

        package = self.g.conflict_top_list[package_idx]  # 当前package name

        if left_idx[package] == -1:

            if package in self.g.init_package_list:
                r = read_cache(package)
                for current_idx in range(len(r["version_list"])):
                    node = r["version_list"][current_idx]
                    if python_version in node["python_require"]:
                        self.reco_idx[package] = current_idx
                        reco_dict[package] = node['version']
                        break
                if package not in reco_dict.keys():
                    log.stop(package, "The current package cannot find a version that meets python requirements:{}".format(python_version))
                    return None
            else:
                log.skip(package, "This node does not have upper-layer dependencies. Skip it")
                self.reco_idx[package] = left_idx[package]
            return self.package_conflict_dfs(package_idx + 1, left_idx, right_idx, reco_dict, python_version)

        if package not in self.g.target_graph.keys():
            log.skip(package, "This node is a leaf node")
            r = read_cache(package)
            if package in self.init_left_idx.keys():
                node = r["version_list"][left_idx[package]]
                reco_dict[package] = node['version']
                # print("node['version']", package, package_idx, node['version'],  r["version_list"][right_idx[package]]['version'])
                self.reco_idx[package] = left_idx[package]
                if python_version not in node["python_require"]:
                    log.stop(package, "The python version is conflict, need:{}, actual:{}".format(node["python_require"], python_version))
                    return None
            else:
                for current_idx in range(left_idx[package], right_idx[package] + 1):
                    self.reco_idx[package] = current_idx
                    node = r["version_list"][current_idx]
                    if python_version in node["python_require"]:
                        reco_dict[package] = node['version']
                        break
                if package not in reco_dict.keys():
                    log.stop(package, "the current package version range {}-{} does not meet the python version{}".format(left_idx[package], right_idx[package],
                                                                                 python_version))
                    return None
            return self.package_conflict_dfs(package_idx + 1, left_idx, right_idx, reco_dict, python_version)

        if package in self.init_left_idx.keys():

            if self.init_left_idx[package] <= right_idx[package] and self.init_right_idx[package] >= left_idx[package]:
                left_idx[package] = max(self.init_left_idx[package], left_idx[package])
                right_idx[package] = min(self.init_right_idx[package], right_idx[package])
            else:
                log.stop(package, "Conflict with initialization scope，init为{}-{}，actual{}-{}".format(self.init_left_idx[package],
                                                                       self.init_right_idx[package],
                                                                       left_idx[package], right_idx[package]))
                return None

        combine_switch = False
        pre = None  # exp combine

        for current_idx in range(left_idx[package], right_idx[package] + 1):
            left_idx_temp = left_idx.copy()
            right_idx_temp = right_idx.copy()
            r = read_cache(package)
            node = r["version_list"][current_idx]
            self.reco_idx[package] = current_idx
            # print("node version_list", node, "left_idx_temp", left_idx_temp, "right_idx_temp", right_idx_temp)
            version_check_state = True  #

            if python_version not in node["python_require"]:
                # print(python_version, package, 'if python_version not in node  python require', node)
                continue

            if pre is None:
                pass
            else:
                pass
            # exp end
            if node["combine"] and combine_switch:  #speed up the search
                continue
            combine_switch = True
            for requirements in node['requirement']:
                if version_check_state is False:
                    continue
                req_package = requirements['package_name']
                if len(req_package.strip())==0:
                    print(requirements)
                    print(node['requirement'])
                    print(req_package, "error occured")
                    continue
                if req_package not in self.g.conflict_top_list:
                    continue

                # parse_requirement
                if requirements['is_skip_start']: start_sym = "<"
                else: start_sym = "<="
                if requirements['is_skip_end']: end_sym = ">"
                else: end_sym = ">="
                temp_requir = req_package + start_sym+requirements['start_node'] + "," + end_sym+requirements['end_node']
                # req_left, lef_version_flag = find_version_idx(req_package, requirements['start_node'])
                # if lef_version_flag: req_left = req_left + 1
                # req_right, right_version_flag = find_version_idx(req_package, requirements['end_node'])
                package_name, req_left, req_right = parse_requirement(temp_requir)
                # print("=======================req_right=======================")
                # print("node", node, "requirements", requirements)
                # print(req_package, req_left, req_right)


                if self.monitor_package == req_package:
                    log.monitor("Package {} V{} depends on package {} form {}-{}".format(package, current_idx, req_package, req_left, req_right))

                if req_package in self.init_left_idx.keys():
                    # print("self.init_left_idx[req_package]",  self.init_left_idx[req_package],self.init_right_idx[req_package], req_left, req_right)
                    start_flag = requirements['is_skip_start'] # true < false <=
                    end_flag = requirements['is_skip_end'] # true e.g. >2.3.1 false >=
                    candidate_pack_lis = [x for x in range(req_left, req_right+1)] # list()
                    if start_flag: # >=
                        if is_real_version(package, requirements['start_node']):
                            candidate_pack_lis.remove(req_left)
                    if end_flag:
                        if is_real_version(package, requirements['end_node']):
                            candidate_pack_lis.remove(req_right)
                    # print(req_package, "candidate_pack_lis", candidate_pack_lis)
                    for item in requirements['skip_list']:
                        temp_idx,temp_version_flag = find_version_idx(req_package, item)
                        if temp_idx in candidate_pack_lis:
                            candidate_pack_lis.remove(temp_idx)
                    init_pack_lis = [x for x in range(self.init_left_idx[req_package], self.init_right_idx[req_package]+1)]
                    # print(req_package, "init_pack_lis",init_pack_lis)
                    satis_pack_lis = list(set(init_pack_lis).intersection(set(candidate_pack_lis)))
                    # print(req_package, "satis_pack_lis", satis_pack_lis)
                    if len(satis_pack_lis)>0:
                        left_idx_temp[req_package] = max(self.init_left_idx[req_package],req_left)
                        right_idx_temp[req_package] = min(self.init_right_idx[req_package], req_right)
                    # if self.init_left_idx[req_package] <= req_right and self.init_right_idx[req_package] >= req_left:
                    else:
                        log.stop(req_package, "There is a conflict, init为{}-{}, actual{}-{}, start_flag-{},end_flag-{} "
                                 .format(self.init_left_idx[req_package], self.init_right_idx[req_package], req_left, req_right, start_flag, end_flag))
                        version_check_state = False
                        tran_con_pack = req_package
                        break

                if left_idx[req_package] == -1 or left_idx[req_package] <= req_left:
                    left_idx_temp[req_package] = req_left
                elif right_idx[req_package] < req_left:
                    log.info("the transitive dependency {}of package {} conflits  {}  {}".format(package, req_package, right_idx[req_package],
                                                                req_left))
                    version_check_state = False
                    break

                if right_idx[req_package] == -1 or right_idx[req_package] >= req_right:
                    right_idx_temp[req_package] = req_right
                elif left_idx[req_package] > req_right:
                    log.info("the transitive dependency {}of package {} conflits  {}  {}".format(package, req_package, left_idx[req_package],
                                                                req_right))
                    version_check_state = False
                    break

            if not version_check_state:
                log.info("{}-{}  Transitive dependency conflict exists, skip".format(package, current_idx))
                self.tran_con_pack = tran_con_pack
                self.conflict_root_node = package
                continue

            log.info("{}-{}searching down".format(package, current_idx))
            reco_dict[package] = node['version']
            self.reco_idx[package] = current_idx
            # print("reco_dict  ", reco_dict, "package, and idx", package, current_idx)
            # print("self.reco_idx ", self.reco_idx)
            # print(left_idx_temp, right_idx_temp, python_version)
            res = self.package_conflict_dfs(package_idx + 1, left_idx_temp, right_idx_temp, reco_dict, python_version)

            # if (res is not None) and self.monitor_conflict_pack == package:
            #     continue
            if res is not None:
                return res
        return None


def parse_package_constraints(expr):
    if ";" in expr:
        expr = expr.split(";")[0]
    if "@" in expr:
        cons = []
        dep = expr
        return dep, cons  # git dependency, not consider now

    try:
        condition_start = expr.index("(")
        condition_end = expr.index(")")
    except ValueError:
        condition_start = len(expr)
        condition_end = condition_start
    dep = expr[:condition_start].strip()
    dep = dep.split()[0]
    try:
        option_start = dep.index("[")
        dep = dep[:option_start].strip()
    except ValueError:
        pass
    condition = expr[condition_start:condition_end].strip()
    # condition = condition.removeprefix("(").removesuffix(")")
    condition = condition[1:-1]
    cons = list()
    lolis = []
    # print("expr", expr,condition , end= " ")
    for symbol in DEF_SYMBOLS:
        try:
            lolis.append(dep.index(symbol))
        except ValueError:
            continue
    lolis = list(sorted(set(lolis)))
    if len(lolis)==0:
        # print("ddddddddddddddd1", expr, dep, cons)
        return dep, cons
    dep_pack = dep[:lolis[0]]
    # print("dep_pack", dep_pack, end=" ")
    dep_pack = dep_pack.replace(" ", "")
    # print("dep_pack", dep_pack, end=" ")
    if len(lolis)==2:
        con1 = dep[lolis[0]:lolis[1]]
        con1 = con1.replace(",", "").replace(" ", "")
        cons.append(con1)
        con2 = dep[lolis[1]:]
        con2 = con2.replace(",", "").replace(" ", "")
        cons.append(con2)
        # print("ddddddddddddddd2", expr, dep, cons)
        return dep_pack, cons
    cons.append(dep[lolis[0]:].replace(",", "").replace(" ", ""))
    return dep_pack, cons


if __name__ == '__main__':
    # parse_requirement("six~=1.12.0")
    find_version_idx("cvxpy", " 1.1.3")