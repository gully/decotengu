import sys
import os.path

import decotengu

sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('doc'))

extensions = [
    'sphinx.ext.autodoc', 'sphinx.ext.autosummary', 'sphinx.ext.doctest',
    'sphinx.ext.todo', 'sphinx.ext.viewcode'
]
project = 'decotengu'
source_suffix = '.rst'
master_doc = 'index'

version = release = decotengu.__version__
copyright = 'DecoTengu Team'

epub_basename = 'decotengu - {}'.format(version)
epub_author = 'DecoTengu Team'

todo_include_todos = True

html_theme = 'agogo'
html_style = 'decotengu.css'
html_static_path = ['static']

# vim: sw=4:et:ai
