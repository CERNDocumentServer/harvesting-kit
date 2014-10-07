import sys

# Hack to activate UTF-8
reload(sys)
sys.setdefaultencoding("utf8")
assert sys.getdefaultencoding() == "utf8"
