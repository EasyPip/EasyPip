from typing import List
from .version_modules import Version

class Package(object):
    def __init__(self, name, summary, version_list: List[Version], potential_require=None):
        self.name = name
        self.summary = summary
        if potential_require is None:
            potential_require = []
        self.potential_require = potential_require
        if version_list is None:
            version_list = []
        self.version_list = version_list


