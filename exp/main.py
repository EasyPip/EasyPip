from exp.alg.PVL import *
from exp.alg.build import *
from exp.alg.dependency_graph import DGraph
from exp.alg.common import DEF_FILENAME
import re
from func_timeout import func_set_timeout, FunctionTimedOut


extra_data = list()
weight_dict = dict()
weight_res = dict()
final_res = dict()
python_res = dict()
file_name = BASE_PATH + "exp/recom_confi_file/" + DEF_FILENAME + ".txt"

def parse_expr(expr):
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


def pack_ver_list(package):
    req = read_cache(package)
    try:
        version_list = req["version_list"]
    except Exception as e:
        print("=============================error cooured=======")
        print(package, "Determine if the version is real")
        print(e)
    # version = version_list[idx]["version"]
    return version_list


# Candidate package
class CPAC(object):

    def __init__(self,candidate, i,try_count,try_init_package,pvl_try):
        self.candidata_name = candidate
        self.dir_flag = i
        self.pos = try_count
        self.init_packs = try_init_package
        self.pack_ver_link = pvl_try



def supos_ver(package, idx, dir_flag = "left"):
    ver_lists = pack_ver_list(package)
    p_version = ver_lists[idx]["version"]
    # print(p_version)
    _versions = p_version.split('.')
    max_p_version = ""
    if dir_flag == "left":
        flag_index = len(_versions) - 2
        for index, ve in enumerate(_versions):
            if index == flag_index:
                if ve.isdigit():
                    ve = int(ve) + 1
                    ve = str(ve)
                else:
                    ve = "9999"
            if index > 0:
                max_p_version = max_p_version + "." + ve
            else:
                max_p_version = ve
        # print(max_p_version)
        cons = package + "<=" + max_p_version + ",>="+p_version
        left_idx,version_flag = find_version_idx(package, max_p_version)
        sub_idx = idx - left_idx + 1
        # print(cons)
        return cons, sub_idx
    else:
        ana_versions = _versions.copy()
        flag_index = 1

        if len(ana_versions)==1:
            cons = package + "<=" + p_version
            right_idx = len(ver_lists)-1
        # print(_versions[flag_index], type(_versions[flag_index]))
        else:
            if _versions[flag_index] == "0":
                ana_versions[0] = str(int(_versions[0])-1)
            else:
                if _versions[flag_index].isdigit():
                    ana_versions[flag_index] = str(int(_versions[flag_index]) - 1)
                else:
                    ana_versions[flag_index] = "0"
            min_p_version = ".".join(ana_versions)
            cons = package + "<=" + p_version + ",>="+min_p_version
            right_idx,version_flag = find_version_idx(package, min_p_version)
        sub_idx = right_idx - idx + 1
        # print(cons)
        return cons, sub_idx


@func_set_timeout(260)
def fix_config(pvl, g, cd_flag = None, init_packs = list()):#
    candidata_node =list()
    candidata_node.append(pvl.tran_con_pack)
    candidata_node.append(pvl.conflict_root_node)


    for item in candidata_node:
        if g.conflict_dict.get(item) is None:
            weight_dict[item] = 1
        else:
            weight_dict[item] = len(g.conflict_dict[item]) + 1
    print("The library causing the dependency conflict may be：", candidata_node, weight_dict)
    # print("g.conflict_dict", g.conflict_dict)
    log.info(f"The library causing the dependency conflict may be {candidata_node, weight_dict}")
    log.info(f"：There is a dependency conflict problem and there is no feasible solution {g.conflict_dict}")

    left_idxs = pvl.left_idx.copy()
    right_idxs = pvl.right_idx.copy()
    confli_nodes_lis = set()

    for candidate in candidata_node:
        try_init_package = init_package.copy()
        ori_con_left_idxs = left_idxs[candidate]
        ori_con_right_idxs = right_idxs[candidate]
        for item in try_init_package:
            if candidate in item:
                try_init_package.remove(item)
                break

        root_left_idx = left_idxs[candidate]
        root_right_idx = right_idxs[candidate]
        print("========candidate=============")
        print( candidate, "original constraints of conflicting library", root_left_idx, root_right_idx)
        log.info(f"{candidate}original constraints of conflicting library {root_left_idx, root_right_idx}")
        try_count = 1
        left_try_count = 1
        right_try_count = 1
        ver_lists = pack_ver_list(candidate)
        res_flag = False
        left_flag = False
        right_flag = False
        while try_count:

            for i in range(2):
                print(i, "---------------", try_count)
                if cd_flag is None:
                    try_each_init = try_init_package.copy()
                else:
                    try_each_init = init_packs.copy()

                if i == 0:  # try left
                    # if ori_con_left_idxs - try_count < 0:
                    if ori_con_left_idxs - left_try_count < 0:
                        left_flag = True
                        print("left_flag is True")
                        continue
                    try_idx = max(0, ori_con_left_idxs - left_try_count)
                    constraint, sub_idx = supos_ver(candidate, try_idx, "left")
                    left_try_count = left_try_count + sub_idx
                if i == 1:
                    if (ori_con_right_idxs + right_try_count) >= (len(ver_lists) - 1):
                        # res_flag = True
                        right_flag = True
                        print("right_flag is True")
                        continue
                    try_idx = min((len(ver_lists) - 1), ori_con_right_idxs + right_try_count)

                    constraint, sub_idx = supos_ver(candidate, try_idx, "right")
                    if sub_idx ==0:
                        sub_idx = sub_idx+1
                    right_try_count = right_try_count + sub_idx
                    print(try_idx, "try_idx", sub_idx, "sub_idx", right_try_count)
                try_each_init.append(constraint)
                # try_each_init.append(candidate)
                print("temp：{}, candidate,; {}, left_righte_flag:{}, try_count{}".format(constraint, candidate, i, try_count))
                print("supposeing,    ：{}".format(try_each_init))
                log.info(f"supposeing,    ： {try_each_init}")
                print("g.target_graph.keys()", g.target_graph.keys())
                pvl_try = PVL(g, try_each_init)
                res_try = pvl_try.package_reco()
                print("pvl.reco_idx ", pvl.reco_idx)
                if res_try is not None: #
                    print("candidate_res", res_try)
                    conflict_idx = pvl_try.reco_idx[candidate]
                    dist = min((abs(ori_con_left_idxs - conflict_idx)), abs(ori_con_right_idxs - conflict_idx))
                    if cd_flag is None:
                        weight_res[candidate] = dist * weight_dict[candidate]
                        final_res[candidate] = [res_try]
                        python_res[candidate] = pvl_try.reco_python
                        res_flag = True
                        print("conflict_idx: ", conflict_idx, "ori_con_left_idxs: ", ori_con_left_idxs,
                              "ori_con_right_idxs:", ori_con_right_idxs, "dist:", dist, "weighted_dis:",
                              weight_res[candidate])
                        break
                    else:
                        cd_flag_dist = min((abs(glori_left_idxs[cd_flag] - pvl_try.reco_idx[cd_flag])), abs(glori_right_idxs[cd_flag] - pvl_try.reco_idx[cd_flag]))
                        can_flag_item = cd_flag + "+" + candidate
                        weight_res[can_flag_item] = cd_flag_dist * weight_dict[cd_flag] + dist * weight_dict[candidate]
                        final_res[can_flag_item] = [res_try]
                        python_res[can_flag_item] = pvl_try.reco_python
                        res_flag = True
                        print("cd_flag is", cd_flag, " conflict_idx: ", conflict_idx, "ori_con_left_idxs: ", ori_con_left_idxs,
                              "ori_con_right_idxs:", ori_con_right_idxs, "dist:", dist, "weighted_dis:",
                              weight_res[can_flag_item])
                        print("_________________________________find result______________________________")
                        break
                        # return 1

                else:
                    print("failed , trying ", pvl_try.conflict_root_node, "candidata_node", candidata_node, weight_dict)
                    temp_node = pvl_try.conflict_root_node
                    if len(temp_node) != 0 :
                        if (temp_node not in candidata_node) and (temp_node not in weight_dict):
                            print("===========================================================", )
                            print("candidat   conflict node", pvl_try.conflict_root_node, pvl_try.tran_con_pack)
                            print()
                            ano_flag = fix_config(pvl_try, g, candidate, try_each_init)
                            if ano_flag != None:
                                break
                print("left_flag, right_flag", left_flag, right_flag)

            try_count = try_count + 1
            if res_flag:
                break
            if left_flag==True and right_flag==True:
                # if cd_flag is not None:
                break
    if len(weight_res):
        print("weight_res", weight_res)
        print("final_res", final_res)
        log.info(f"weight_res {weight_res}")
        sort_res = dict(sorted(weight_res.items(), key=operator.itemgetter(1)))
        final_recommended = list(sort_res.keys())[0]
        python_reco = python_res[final_recommended]
        write_config(python_reco, final_res[final_recommended][0], final_recommended)
        return None
    else:
        print("cannot generate solution due to some reasons")
        # if len(extra_candi_node):
        #     try_multi_fix()
        #     print("try fix by multiple  ")
        # if cd_flag is not None:
        #     for i in candidata_node:
        #         weight_dict.pop(i)
        # else:
            # print("cannot fix due to some reason  ")
    return None
    # log.info(f"final_res {final_res}")





def runPyECS(filename, level=DEFAULT_SEARCH_LEVEL):
    f = open(filename, encoding="utf-8")
    requirements = f.readlines()
    f.close()
    print("开始执行")
    global require_package
    global init_package
    require_package = []
    init_package = []
    global constraints_lis
    constraints_lis = list()
    for require in requirements:
        expr = require.strip()
        if len(expr) == 0 or len(expr) == 1:
            continue
        if expr.lstrip()[0] == "#":
            continue
        if "#" in expr:
            _end_index = expr.index("#")
            expr = expr[:_end_index]
        if "-f" in expr:
            if expr.index("-f")==0:
                continue
        if "@" in expr:
            if "git" in expr:
                extra_data.append(expr)
                continue
            be_index = expr.index("@")
            expr = expr[:be_index].strip()
        if "git" in expr:
            continue
        if ";" in expr:
            be_index = expr.index(";")
            expr = expr[:be_index].strip()

        if len(expr) == 0 or len(expr) == 1:
            continue
        constraints_lis.append(expr)
        package_name, symbol = parse_expr(expr)
        if symbol != "":
            init_package.append(expr)
        require_package.append(package_name.lower())
    log.info(require_package)
    log.info(init_package)
    print("开始构建version tree")
    build(require_package, deep_build=True)
    # Step1 建立DAG结构
    print("开始构建冲突图")
    global g
    g = DGraph(level=level)
    print("init  Dgraph")
    g.build(require_package)
    # print("g.conflict path", g.conflict_path)
    # print(g.conflict_dict['tensorflow-gpu'])
    require_package = [s.lower() for s in require_package]
    redunt_res_init = list(set(g.conflict_node_set) - set(require_package))
    global  redunt_init_res
    redunt_init_res = list(set(require_package) - set(g.conflict_node_set))
    print("require_package", len(require_package), require_package)
    log.info(f"require_package:-{require_package}-{len(require_package)}")
    print("g.conflict_node_set", len(g.conflict_node_set), g.conflict_node_set)
    log.info(f"g.conflict_node_set:-{g.conflict_node_set}-{len(g.conflict_node_set)}")
    print("redunt_res_init", len(redunt_res_init), redunt_res_init)
    print("redunt_init_res", len(redunt_init_res), redunt_init_res)
    # print(g.target_graph)
    # print(g.source_graph)
    print("开始版本推荐运算")
    pvl = PVL(g, init_package)
    print("------------------")
    print(pvl.left_idx)
    print(pvl.right_idx)
    print("=======!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    res = pvl.package_reco() #
    if res is None:

        print("存在依赖冲突问题，无可行解", pvl.conflict_root_node)
        log.info(f"存在依赖冲突问题，无可行解 {pvl.conflict_root_node}")
        # conflict_root_cause
        if pvl.conflict_root_node=="":
            print("python版本存在冲突")
            log.info(f"python版本存在冲突，无可行解")
            exit(0)
        global glori_left_idxs
        global glori_right_idxs
        glori_left_idxs = pvl.left_idx.copy()
        glori_right_idxs = pvl.right_idx.copy()
        try:
            fix_config(pvl, g)
        except FunctionTimedOut as e:
            print('function timeout + msg = ', e.msg)
            if len(weight_res): # 迭代找到了结果
                print("weight_res", weight_res)
                print("final_res", final_res)
                log.info(f"weight_res {weight_res}")
                sort_res = dict(sorted(weight_res.items(), key=operator.itemgetter(1)))  # 按照value值升序
                final_recommended = list(sort_res.keys())[0]
                python_reco = python_res[final_recommended]
                write_config(python_reco, final_res[final_recommended][0], final_recommended)
            else:
                pass
    else:
        write_config(pvl.reco_python, res)


def write_config(reco_python, res, final_recommended=None):
    res_visited = list()
    with open(file_name, 'w') as f:
        if final_recommended is not None:
            if "+" in final_recommended:
                temp_name = final_recommended.replace("+", "  ")
                print("final recommended result generated by removing ", temp_name)
                log.info(f'final recommended result generated by removing  {temp_name}')
                f.writelines("# final recommended result generated by removing: ")
                f.writelines(temp_name)
                f.write('\n')
                for item in temp_name:
                    if item in g.conflict_path.keys():
                        print("# conflict_path", g.conflict_path[item])
                        f.writelines("# conflicting path :")
                        f.writelines(g.conflict_path[item])
                f.write('\n')
            else:
                print("# final recommended result generated by removing ", final_recommended)
                f.writelines("# final recommended result generated by removing: ")
                f.writelines(final_recommended)
                f.write('\n')
                if final_recommended in g.conflict_path.keys():
                    print("# conflict_path", g.conflict_path[final_recommended])
                # print("all conflict path", g.conflict_path)
                    f.writelines("# conflicting path :")
                    f.writelines(g.conflict_path[final_recommended])
                    f.write('\n')
        print(res)
        print(redunt_init_res)

        print("The recommended results are：")
        print("# python version：", reco_python)
        log.info(f"# python version：  {reco_python}")
        recommand_python = "# " + reco_python
        f.writelines(recommand_python)
        f.write('\n')
        dir_depend = dict()
        for item in require_package:
            for k, v in res.items():
                if k in item:
                    res_visited.append(k)
                    print(k, "==", v)
                    log.info(f"{k}=={v}")
                    line_mo = k + "==" + v
                    f.writelines(line_mo)
                    f.write('\n')
                    dir_depend[k] = v
                    break
        # 没有依赖冲突的点
        for item in redunt_init_res:
            # print("redunt_init_res==========", item )
            if item in res:
                continue
            for cons_item in constraints_lis:
                # print("cons_item---", cons_item)
                if item in cons_item.lower() and item not in res_visited:
                    print("extra: ", cons_item)
                    log.info(f"{cons_item}")
                    f.writelines(cons_item)
                    f.write('\n')
                    break

        trans_depend = dict(res.items() - dir_depend.items())
        print("# the followings is transitive dependency ")
        f.writelines("# the followings is transitive dependency")
        f.write('\n')
        for k, v in trans_depend.items():
            print(k, "==", v)
            log.info(f"# {k}=={v}")
            line_mo = "# " + k + "==" + v
            f.writelines(line_mo)
            f.write('\n')

        print(len(res), "done")


def single_file():
    fpath = BASE_PATH + "data/dependency_declaration_files/" + DEF_FILENAME + ".txt"
    # requ_repair
    time_begin = time.time()
    runPyECS(fpath, level=2)
    time_end = time.time()
    times = time_end - time_begin
    print('time:', times)
    log.info(f"running time: {times}")

if __name__ == '__main__':
    single_file()

