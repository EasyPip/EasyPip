from exp.alg.common import *
from exp.alg.build import *
import networkx as nx
import matplotlib.pyplot as plt

class DGraph(object):
    def __init__(self, level=DEFAULT_SEARCH_LEVEL):
        self.graph = dict()   # target_node:[source_node]  A->B == graph[B] = [A]
        self.source_graph = dict()   # target_node:[source_node]
        self.target_graph = dict()   # source_node:[target_node]
        self.init_package_list = list()
        self.node_set = set()
        self.conflict_node_set = set()
        self.package_list = []
        self.conflict_dict = dict()
        self.conflict_path = dict()
        self.conflict_graph = set()
        self.conflict_target_graph = dict()
        self.conflict_top_list = list()

        self.level = level
        self.visited = []
        self.trace = []
        self.has_circle = False
        self.trace_len = set()
        self.indegree = dict()
        self.lower_init_package_list = list()
        self.package_depedency = dict()

    def build(self, package_list):
        print("buiding... ", len(package_list), package_list)
        self.init_package_list = package_list
        self.lower_init_package_list =  list(map(lambda x: x.lower(), package_list ))
        self.node_set.update(package_list)
        # print("update...package_list ", len(package_list), package_list)
        self.build_graph(package_list, level=self.level)
        self.conflict_check()
        print("conflict checking, finished")
        log.info("conflict checking, finished")
        self.topological_sort()
        if self.has_circle:
            no_depens = list((self.trace_len).intersection(set(package_list)))
            print(self.trace_len, "they exist cycling")
            log.info(f"existing cycling, {self.trace_len}")

        print("topological_sort, finished")
        log.info("topological_sort, finished")

    def build_graph(self, package_list, level):
        # print("building graph", package_list)
        if len(package_list) == 0:
            return
        if level <= 0:
            return

        self.package_list = package_list
        for package in package_list:
            package = package.lower()
            package_json = read_cache(package)
            try:
                potential = package_json["potential_require"]
            except Exception as e:
                print("{}Read failed, start build".format(package))
                build([package])
                continue
            # print(level, "level building graph: ", package, "potential_conflict_package: ", potential)
            if package in self.lower_init_package_list:
                self.package_depedency[package] = potential
            self.build_graph(potential, level-1)
            # print("package, len(potential), potential", package, len(potential), potential)
            for potential_package in potential:
                if potential_package in white_list:
                    continue
                if potential_package not in self.graph.keys():
                    self.graph[potential_package] = []
                    self.source_graph[potential_package] = []
                if package not in self.target_graph.keys():
                    self.target_graph[package] = []
                if package not in self.graph[potential_package]:
                    self.graph[potential_package].append(package)
                    self.source_graph[potential_package].append(package)
                if potential_package not in self.target_graph[package]:
                    self.target_graph[package].append(potential_package)
                self.node_set.add(potential_package)
        return

    def conflict_check(self):
        #print("conflict checking")
        if len(self.node_set) == 0:
            raise ValueError("Conflict detection requires a package version diagram structure")

        # init
        self.conflict_dict = dict()
        self.conflict_path = dict()
        self.conflict_graph = set()

        package_dict = dict()
        for package in self.init_package_list:
            package_dict[package] = {package}
        print("conflict checking self.node_set", len(self.node_set), self.node_set)
        log.info("conflict checking lens of self.node_set：{}".format(len(self.node_set)))
        log.info("conflict checking self.node_set：{}".format(self.node_set))
        print("conflict checking self.target_graph.keys()",len(list( self.target_graph.keys())), self.target_graph.keys())
        log.info("conflict checking lens of self.target_graph.keys()：{}".format(len(list( self.target_graph.keys()))))
        log.info("conflict checking self.target_graph.keys()：{}".format(self.target_graph.keys()))
        print("conflict checking package_dict.keys()", len(list(package_dict.keys())), package_dict.keys())
        log.info("conflict checking lens of package_dict.keys()：{}".format(len(list(package_dict.keys()))))
        log.info("conflict checking package_dict.keys()：{}".format(package_dict.keys()))

        for package in self.node_set:
            if package in self.target_graph.keys():
                for require in self.target_graph[package]:
                    if require in package_dict.keys():
                        package_dict[require].add(package)
                    else:
                        package_dict[require] = {package}
        # print("conflict checking package_dict[require]", package_dict[require])
        print("conflict checking  lens  package_dict.keys() ",len(package_dict.keys()),  package_dict.keys())
        print("set   package_dict.keys() ",len(set(package_dict.keys())),  set(package_dict.keys()))
        for package in package_dict.keys():
            if len(package_dict[package]) >= 2:
                self.conflict_dict[package] = package_dict[package]
                self.conflict_path[package] = dict()
                for source in package_dict[package]:
                    path = self.find_path(source, package)
                    self.conflict_path[package][source] = path
                    print("potential conflicting path ", path)

                    for path_list in path:
                        for idx in range(len(path_list) - 1):
                            source = path_list[idx]
                            target = path_list[idx + 1]
                            self.conflict_graph.add((source, target))
                            if source not in self.conflict_target_graph.keys():
                                self.conflict_target_graph[source] = set()
                            self.conflict_target_graph[source].add(target)
                            self.conflict_node_set.add(source)
                            self.conflict_node_set.add(target)
        # print()
        print("conflict checking self.conflict_dict", self.conflict_dict)
        return self.conflict_dict

    def find_path(self, source, target):
        if source == target:
            return [[source]]
        path_list = []

        def dfs_search(path, visited, current_node):
            visited[current_node] = True
            if current_node == target:
                path_list.append(path)
                return
            if current_node not in self.target_graph.keys():
                return
            for next_node in self.target_graph[current_node]:
                if visited[next_node] is False:
                    dfs_search(path + [next_node], visited, next_node)
            return

        all_node_visit = dict()
        for node in self.node_set:
            all_node_visit[node] = False
        dfs_search([source], all_node_visit, source)
        return path_list

    def find_topo(self, res=[], in_degree=dict()):
        while len(res) != len(self.conflict_node_set):
            ano_res = res.copy()
            for node in self.conflict_node_set:
                if in_degree[node] == 0:
                    res.append(node)
                    in_degree[node] -= 1
                    if node in self.conflict_target_graph.keys():
                        for target in self.conflict_target_graph[node]:
                            if in_degree[target] == 0:
                                res.append(node)
                                continue
                            in_degree[target] -= 1
            ret = list(set(res) - set(ano_res))
            if len(ret)==0:
                break
        return res

    def del_in_dgree(self, visited_node, in_degree):
        if visited_node in self.conflict_target_graph.keys():
            # print("node  ", visited_node, conflict_target_graph[visited_node])
            for target in self.conflict_target_graph[visited_node]:
                # print(target, in_degree[target])
                if in_degree[target] == 0:
                    # print("indgree 0 ", target)
                    continue
                in_degree[target] -= 1
                in_degree = self.del_in_dgree(target, in_degree)
        return in_degree

    def topological_sort(self):
        res = []
        in_degree = dict()
        for node in self.conflict_node_set:  # init
            in_degree[node] = 0

        for pair in self.conflict_graph:
            in_degree[pair[1]] += 1

        print("lens of in_degree", len(in_degree))
        log.info(f"topo   lens of in_degre {len(in_degree)}")
        log.info(f"topo   in_degre {in_degree}")
        log.info(f"topo   self.conflict_node_set {self.conflict_node_set}")
        self.indegree = in_degree
        res = self.find_topo(res, in_degree)
        temp = list(set(self.conflict_node_set) - set(res))
        if len(temp) > 0 :
            for item_node in temp:
                self.cycle_dfs(item_node)
                if self.has_circle:
                    # print("Cycle.")
                    break

            for visited_node in self.trace_len:
                in_degree[visited_node] = 0
                in_degree = self.del_in_dgree(visited_node, in_degree)

            # del cycle, run again
            res = self.find_topo(res, in_degree)
            left_node = list(set(self.conflict_node_set) - set(res))


        self.conflict_top_list = res
        print("topo.....Supplementary sorting content ", len(res), self.conflict_top_list)
        log.info(f"topo sorting results, {self.conflict_top_list}")
        # return res

    def gen_version_tree_dict(self):
        if len(self.node_set) == 0:
            raise ValueError("Failed to generate package version diagram structure")
        res = []
        for package in self.conflict_node_set:
            package_json = read_cache(package)
            package_json.pop('potential_require')
            for version_info in package_json["version_list"]:
                requirements = []
                for require in version_info["requirement"]:
                    if require["package_name"] in self.conflict_node_set:
                        requirements.append(require)
                version_info["requirement"] = requirements
            res.append(package_json)
        return res


    def draw_package_graph(self):
        if len(self.node_set) == 0:
            raise ValueError("Failed to generate package version diagram structure")
        G = nx.DiGraph()
        for node in self.node_set:
            G.add_node(node, desc=node)
        for key in self.target_graph.keys():
            for target in self.target_graph[key]:
                G.add_edge(key, target)
        # pos = nx.spring_layout(G)
        pos = nx.circular_layout(G)
        node_labels = nx.get_node_attributes(G, 'desc')
        nx.draw_networkx_labels(G, pos, labels=node_labels)
        nx.draw_networkx_nodes(G, pos, node_size=0, node_color='Gray', node_shape='o')
        nx.draw_networkx_edges(G, pos)
        plt.show()
        # plt.savefig('./tu.pdf')

    def draw_conflict_graph(self):
        if len(self.node_set) == 0:
            raise ValueError("Conflict detection requires a package version diagram structure")
        G = nx.DiGraph()
        for node in self.conflict_node_set:
            G.add_node(node, desc=node)
        for key in self.conflict_target_graph.keys():
            for target in self.conflict_target_graph[key]:
                G.add_edge(key, target)
        # pos = nx.spring_layout(G)
        pos = nx.circular_layout(G)
        node_labels = nx.get_node_attributes(G, 'desc')
        nx.draw_networkx_labels(G, pos, labels=node_labels)
        nx.draw_networkx_nodes(G, pos, node_size=0, node_color='Gray', node_shape='o')
        nx.draw_networkx_edges(G, pos)
        # nx.draw(G, pos)
        plt.show()

    def cycle_dfs(self, node_index):
        global has_circle
        if (node_index in self.visited):
            if (node_index in self.trace):
                has_circle = True
                trace_index = self.trace.index(node_index)
                # print("there is cycling ")
                log.info(f"there is cycling {self.trace}")
                temp_trace = list()
                for i in range(trace_index, len(self.trace)):
                    print(self.trace[i] + ' ', end='')
                    temp_trace.append(self.trace[i])
                log.info(f"there is cycling {temp_trace}")
                # print('\n', end='')
                self.trace_len.update(self.trace)
                return
            return

        self.visited.append(node_index)
        self.trace.append(node_index)

        if node_index in self.conflict_target_graph:
            children = self.conflict_target_graph[node_index]
            for child in children:
                self.cycle_dfs(child)
        self.trace.pop()


extra_data = list()

if __name__ == '__main__':
    base_path = "./pyecs/"
    f = open(base_path + "data/filer_pull_issues_requ/80_code4romania_covid-19-ro-help.txt", encoding="utf-8")
    requirements = f.readlines()
    f.close()
    import re
    require_package = []
    for require in requirements:
        # deal with abnormal line
        expr = require.strip()
        if len(expr) == 0 or len(expr) == 1:
            continue
        if expr.lstrip()[0] == "#":
            continue
        if "@" in expr:
            extra_data.append(expr)
            continue
        package_name = re.match(r'(.*)[=!~<>]+=', require).group(1)
        require_package.append(package_name)

    # print(require_package)
    g = DGraph(level=1)
    # require_package.remove("beautifulsoup4")
    g.build(require_package)
    g.topological_sort()
    # print(a)
    g.draw_package_graph()
    g.draw_conflict_graph()
    # g.gen_version_tree_dict()
