import os
import json
import logging


BASE_PATH = "F:\\3th_year\\dc_code/EasyPip/"

LOG_PATH = BASE_PATH + 'exp/log/'


# Version ID. When the cache JSON structure changes or the JSON content assignment logic changes,
# the version number needs to be changed. The full cache will be refreshed next build
BUILD_VERSION = "0.0.3"
DEFAULT_SEARCH_LEVEL = 1  # prepare for long dependency
DEF_SYMBOLS = [">=", "<=", ">", "<", "==", "!=", "~="]
DEF_FILENAME = "spcl_serverless-benchmarks_a"


def read_cache(package_name, dir="cache"):
    """
    read cached data
    :return:
    """
    package_name = package_name.lower().strip()
    cache_path = BASE_PATH + "exp/{}/{}.json".format(dir, package_name)
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            saved_require = json.load(f)
            return saved_require[package_name]
    else:
        return None


class Log(object):
    def __init__(self):
        self.log = logging.getLogger("EasyPip")
        self.log.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter("[%(asctime)s]-[%(name)s]-[%(levelname)s]-%(message)s")
        self.fh = logging.FileHandler(filename="{}/{}.txt".format(LOG_PATH, DEF_FILENAME), mode='a+',
                                      encoding="utf-8")
        self.fh.setLevel(logging.INFO)
        self.fh.setFormatter(self.formatter)
        # self.log.addHandler(self.sh)
        self.log.addHandler(self.fh)

    def getlog(self):
        return self.log

    def monitor(self, msg):
        '''
        :param msg:
        :return:
        '''
        return self.log.info("[monitor package]-{}".format(msg))

    def skip(self, package, msg):
        '''
        :param package:
        :param msg:
        :return:
        '''
        return self.log.info("[skip]-[{}]-{}".format(package, msg))

    def stop(self, package, msg):
        '''
        :param package:
        :param msg:
        :return:
        '''
        return self.log.info("[stop]-[{}]-{}".format(package, msg))

    def state(self, msg):
        '''
        :param package_idx:
        :param msg:
        :return:
        '''
        return self.log.info("[{}]".format(msg))

    def info(self, msg):
        '''
        exit searching
        :param package_idx:
        :param msg:
        :return:
        '''
        return self.log.info("{}".format(msg))

    def shutdown(self):
        '''
                exit log
                :param package_idx:
                :param msg:
                :return:
                '''
        logging.shutdown()



log = Log()
white_list = read_cache("white-list", "config").keys()

