import sys
import logging
# print(os.path.dirname(sys.modules['__main__'].__file__))


logger = logging.getLogger()

logging.basicConfig(stream=sys.stdout, format='%(asctime)s %(levelname)-7s ' +
                                              '%(threadName)-15s %(message)s', level=logging.DEBUG)