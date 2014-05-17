import sys
import os.path
import sphinx_rtd_theme

import decotengu

sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('doc'))

extensions = [
    'sphinx.ext.autodoc', 'sphinx.ext.autosummary', 'sphinx.ext.doctest',
    'sphinx.ext.todo', 'sphinx.ext.viewcode', 'sphinx.ext.mathjax'
]
project = 'decotengu'
source_suffix = '.rst'
master_doc = 'index'

version = release = decotengu.__version__
copyright = 'DecoTengu Team'

epub_basename = 'decotengu - {}'.format(version)
epub_author = 'DecoTengu Team'

todo_include_todos = True

html_theme = 'sphinx_rtd_theme'
html_static_path = ['static']
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_style = 'decotengu.css'


# vim: sw=4:et:ai
