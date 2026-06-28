import logging

from .meta import __version__
from .cpt import CPT
from .cptu import CPTu
from .reader import read_cpt

logging.getLogger('cptpy').addHandler(logging.NullHandler())