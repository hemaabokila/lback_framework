
project = 'lback'
copyright = '2025, Ibrahem abo kila'
author = 'Ibrahem abo kila'
release = '1.0.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.linkcode',
]

templates_path = ['_templates']
exclude_patterns = []

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

html_css_files = [
    'custom.css',
]

html_codeblock_linenos_style = 'table'
html_baseurl = 'https://hemaabokila.github.io/lback-docs/'

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# Configuration for sphinx.ext.linkcode
# This generates links to source code on GitHub.
def linkcode_resolve(domain, info):
    if domain != 'py':
        return None
    if not info['module']:
        return None
    filename = info['module'].replace('.', '/')
    # Assuming your main lback source code is in a repo like 'hemaabokila/lback_framework'
    # Adjust 'master' to your default branch name if it's 'main'
    return "https://github.com/hemaabokila/lback_framework/blob/main/%s.py" % filename