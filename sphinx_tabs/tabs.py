""" Tabbed views for Sphinx, with HTML builder """

import os
import json
from docutils.parsers.rst import Directive
from docutils import nodes
from pygments.lexers import get_all_lexers
from sphinx.util.osutil import copyfile


DIR = os.path.dirname(os.path.abspath(__file__))

FILES = [
    'tabs.js',
    'tabs.css',
]

EXTERNAL_DEPENDENCIES = [
    'https://cdnjs.cloudflare.com/ajax/libs/'
    'semantic-ui/2.2.7/components/segment.css',

    'https://cdnjs.cloudflare.com/ajax/libs/'
    'semantic-ui/2.2.7/components/tab.css',

    'https://cdnjs.cloudflare.com/ajax/libs/'
    'semantic-ui/2.2.7/components/tab.js',

    'https://cdnjs.cloudflare.com/ajax/libs/'
    'semantic-ui/2.2.7/components/menu.css',
]


LEXER_MAP = {}
for lexer in get_all_lexers():
    for short_name in lexer[1]:
        LEXER_MAP[short_name] = lexer[0]


class TabsDirective(Directive):
    """ Top-level tabs directive """

    has_content = True

    def run(self):
        """ Parse a tabs directive """
        self.assert_has_content()
        env = self.state.document.settings.env

        node = nodes.container()
        node['classes'] = ['sphinx-tabs']

        tabs_node = nodes.container()
        tabs_node.tagname = 'div'

        classes = 'ui top attached tabular menu sphinx-menu'
        tabs_node['classes'] = classes.split(' ')

        env.temp_data['tab_titles'] = []
        env.temp_data['is_first_tab'] = True
        self.state.nested_parse(self.content, self.content_offset, node)

        tab_titles = env.temp_data['tab_titles']
        for idx, [data_tab, tab_name] in enumerate(tab_titles):
            tab = nodes.container()
            tab.tagname = 'a'
            tab['classes'] = ['item'] if idx > 0 else ['active', 'item']
            tab['classes'].append(data_tab)
            tab += nodes.Text(tab_name)
            tabs_node += tab

        node.children.insert(0, tabs_node)

        return [node]


class TabDirective(Directive):
    """ Tab directive, for adding a tab to a collection of tabs """

    has_content = True

    def run(self):
        """ Parse a tab directive """
        self.assert_has_content()
        env = self.state.document.settings.env

        args = self.content[0].strip()
        if len(args.split()) == 1:
            args = {'tab_name': args}
        else:
            args = json.loads(args)

        if 'tab_id' not in args:
            args['tab_id'] = env.new_serialno('tab_id')

        data_tab = "sphinx-data-tab-{}".format(args['tab_id'])

        env.temp_data['tab_titles'].append((data_tab, args['tab_name']))

        text = '\n'.join(self.content)
        node = nodes.container(text)

        classes = 'ui bottom attached sphinx-tab tab segment'
        node['classes'] = classes.split(' ')
        node['classes'].extend(args.get('classes', []))
        node['classes'].append(data_tab)

        if env.temp_data['is_first_tab']:
            node['classes'].append('active')
            env.temp_data['is_first_tab'] = False

        self.state.nested_parse(self.content[2:], self.content_offset, node)
        return [node]


class GroupTabDirective(Directive):
    """ Tab directive that toggles with same tab names across page"""

    has_content = True

    def run(self):
        """ Parse a tab directive """
        self.assert_has_content()

        group_name = self.content[0]
        self.content.trim_start(2)

        for idx, line in enumerate(self.content.data):
            self.content.data[idx] = '   ' + line

        tab_args = {
            'tab_id': '-'.join(group_name.lower().split()),
            'tab_name': group_name,
        }

        new_content = [
            '.. tab:: {}'.format(json.dumps(tab_args)),
            '',
        ]

        for idx, line in enumerate(new_content):
            self.content.data.insert(idx, line)
            self.content.items.insert(idx, (None, idx))

        node = nodes.container()
        self.state.nested_parse(self.content, self.content_offset, node)
        return node.children


class CodeTabDirective(Directive):
    """ Tab directive with a codeblock as its content"""

    has_content = True

    def run(self):
        """ Parse a tab directive """
        self.assert_has_content()

        args = self.content[0].strip().split()
        self.content.trim_start(2)

        lang = args[0]
        tab_name = ' '.join(args[1:]) if len(args) > 1 else LEXER_MAP[lang]

        for idx, line in enumerate(self.content.data):
            self.content.data[idx] = '      ' + line

        tab_args = {
            'tab_id': '-'.join(tab_name.lower().split()),
            'tab_name': tab_name,
            'classes': ['code-tab'],
        }

        new_content = [
            '.. tab:: {}'.format(json.dumps(tab_args)),
            '',
            '   .. code-block:: {}'.format(lang),
            '',
        ]

        for idx, line in enumerate(new_content):
            self.content.data.insert(idx, line)
            self.content.items.insert(idx, (None, idx))

        node = nodes.container()
        self.state.nested_parse(self.content, self.content_offset, node)
        return node.children


def add_assets(app):
    """ Add CSS and JS asset files """
    assets = EXTERNAL_DEPENDENCIES + ['sphinx_tabs/' + f for f in FILES]
    for path in assets:
        if path.endswith('.css'):
            app.add_stylesheet(path)
        elif path.endswith('.js'):
            app.add_javascript(path)


def copy_assets(app, exception):
    """ Copy asset files to the output """
    builders = ('html', 'readthedocs', 'readthedocssinglehtmllocalmedia')
    if app.builder.name not in builders:
        app.info('Not copying tabs assets! Not compatible with %s builder' %
                 app.builder.name)
        return
    if exception:
        app.info('Not copying tabs assets! Error occurred previously')
        return
    app.info('Copying tabs assets... ', nonl=True)

    installdir = os.path.join(app.builder.outdir, '_static', 'sphinx_tabs')
    if not os.path.exists(installdir):
        os.makedirs(installdir)

    for path in FILES:
        source = os.path.join(DIR, path)
        dest = os.path.join(installdir, path)
        copyfile(source, dest)
    app.info('done')


def setup(app):
    """ Set up the plugin """
    app.add_directive('tabs', TabsDirective)
    app.add_directive('tab', TabDirective)
    app.add_directive('group-tab', GroupTabDirective)
    app.add_directive('code-tab', CodeTabDirective)
    app.connect('builder-inited', add_assets)
    app.connect('build-finished', copy_assets)
