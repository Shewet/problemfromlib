""" Google Document XBlock implementation """
# -*- coding: utf-8 -*-
#

# Imports ###########################################################
import logging
import textwrap
import requests
from copy import copy
from xblock.core import XBlock
from xblock.fields import Scope, String, List
from xblock.fragment import Fragment
from xmodule.x_module import STUDENT_VIEW,XModule
from xblockutils.publish_event import PublishEventMixin
from xblockutils.resources import ResourceLoader
from six import text_type
from opaque_keys.edx.locator import LibraryLocator
LOG = logging.getLogger(__name__)
RESOURCE_LOADER = ResourceLoader(__name__)

# Constants ###########################################################
DEFAULT_DOCUMENT_URL = (
    'https://docs.google.com/presentation/d/1x2ZuzqHsMoh1epK8VsGAlanSo7r9z55ualwQlj-ofBQ/embed?'
    'start=true&loop=true&delayms=10000'
)
DEFAULT_EMBED_CODE = textwrap.dedent("""
    <iframe
        src="{}"
        frameborder="0"
        width="960"
        height="569"
        allowfullscreen="true"
        mozallowfullscreen="true"
        webkitallowfullscreen="true">
    </iframe>
""") .format(DEFAULT_DOCUMENT_URL)
DOCUMENT_TEMPLATE = "/templates/html/google_docs.html"
DOCUMENT_EDIT_TEMPLATE = "/templates/html/google_docs_edit.html"


def _(text):
    """
    Dummy ugettext.
    """
    return text


# Classes ###########################################################
@XBlock.needs("i18n")  # pylint: disable=too-many-ancestors
@XBlock.wants('library_tools')
@XBlock.wants('studio_user_permissions')
@XBlock.wants('user')
@XBlock.wants('library_content_module')
@XBlock.wants('library_root_xblock')
@XBlock.needs("i18n")  # pylint: disable=too-many-ancestors
class GoogleDocumentBlock(XBlock, PublishEventMixin):
    """
    XBlock providing a google document embed link
    """

    @XBlock.json_handler
    def source_library_values(self, data, suffix=""):
        """
        Return a list of possible values for self.source_library_id
        """
        """
        Return a list of possible values for self.source_library_id
        """
        lib_tools = self.runtime.service(self, 'library_tools')
        user_perms = self.runtime.service(self, 'studio_user_permissions')
        all_libraries = [
            (key, name) for key, name in lib_tools.list_available_libraries()
            if user_perms.can_read(key) or self.source_library_id == unicode(key)
        ]
        all_libraries.sort(key=lambda entry: entry[1])  # Sort by name
        if self.source_library_id and self.source_library_key not in [entry[0] for entry in all_libraries]:
            all_libraries.append((self.source_library_id, _(u"Invalid Library")))
        all_libraries = [(u"", _("No Library Selected"))] + all_libraries
        values = [{"display_name": name, "value": unicode(key)} for key, name in all_libraries]
        return values

    @XBlock.json_handler
    def source_problem_values(self, data, suffix=""):
        """
        Return list of possible problems for self.select_problems
        """
        library_selected = data['source_library_id']
        lib_tools = self.runtime.service(self, 'library_tools')
        user_perms = self.runtime.service(self, 'studio_user_permissions')
        lib_root = self.runtime.service(self, 'library_root_xblock')
        blk_list = []
        all_problems = lib_tools.list_available_problems(library_selected)
        # blk_list= [(c.block_type, c.block_id) for c in all_problems]
        # values = [{"display_name": name, "value": name} for key,name in blk_list]
        # test=[]
        # for problem in all_problems:
        #    test.extend( [{"display_name": problem, "value": problem} ])
        return all_problems  # all_problems #values

    display_name = String(
        display_name=_("Display Name"),
        help=_("This name appears in the horizontal navigation at the top of the page."),
        scope=Scope.settings,
        default="Problem from Library"
    )
    embed_code = String(
        display_name=_("Embed Code"),
        help=_(
            "Google provides an embed code for Drive documents. In the Google Drive document, "
            "from the File menu, select Publish to the Web. Modify settings as needed, click "
            "Publish, and copy the embed code into this field."
        ),
        scope=Scope.settings,
        default=DEFAULT_EMBED_CODE
    )
    alt_text = String(
        display_name=_("Alternative Text"),
        help=_("Alternative text describes an image and appears if the image is unavailable."),
        scope=Scope.settings,
        default=""
    )

    source_library_id = String(
        display_name=_("Library"),
        help=_("Select the library from which you want to draw content."),
        scope=Scope.settings,
        values_provider=lambda instance: instance.source_library_values(),
    )
    source_library_version = String(
        # This is a hidden field that stores the version of source_library when we last pulled content from it
        display_name=_("Library Version"),
        scope=Scope.settings,
    )
    mode = String(
        display_name=_("Mode"),
        help=_("Determines how content is drawn from the library"),
        default="random",
        values=[
            {"display_name": _("Choose n at random"), "value": "random"}
            # Future addition: Choose a new random set of n every time the student refreshes the block, for self tests
            # Future addition: manually selected blocks
        ],
        scope=Scope.settings,
    )

    source_problem_id = String(
        display_name=_("Problem"),
        help=_("Select the library from which you want to draw content."),
        scope=Scope.settings,
        values_provider=lambda instance: instance.source_problem_values(),
    )

    selected = List(
        # This is a list of (block_type, block_id) tuples used to record
        # which random/first set of matching blocks was selected per user
        default=[],
        scope=Scope.user_state,
    )
    has_children = True


    @property
    def source_library_key(self):
        """
        Convenience method to get the library ID as a LibraryLocator and not just a string
        """
        return LibraryLocator.from_string(self.source_library_id)

    def _get_selected_child_blocks(self):
        """
        Generator returning XBlock instances of the children selected for the
        current user.
        """
        selected = set([(c.block_type, c.block_id) for c in self.children])
        for block_type, block_id in selected:
            yield self.runtime.get_block(self.location.course_key.make_usage_key(block_type, block_id))
            pass

    def get_user_id(self):
        user_service = self.runtime.service(self, 'user')
        if user_service:
            # May be None when creating bok choy test fixtures
            user_id = user_service.get_current_user().opt_attrs.get('edx-platform.user_id', None)
        else:
            user_id = None
        return user_id

    # Context argument is specified for xblocks, but we are not using herein

    # Context argument is specified for xblocks, but we are not using herein
    def studio_view(self, context):  # pylint: disable=unused-argument
        """
        Editing view in Studio
        """
        from xmodule.x_module import STUDENT_VIEW ,XModule
        fragment = Fragment()
        # Need to access protected members of fields to get their default value
        default_name = self.fields['display_name']._default  # pylint: disable=protected-access,unsubscriptable-object
        fragment.add_content(RESOURCE_LOADER.render_template(DOCUMENT_EDIT_TEMPLATE, {
            'self': self,
            'defaultName': default_name,
        }))
        fragment.add_javascript(RESOURCE_LOADER.load_unicode('public/js/google_docs_edit.js'))
        fragment.add_css(RESOURCE_LOADER.load_unicode('public/css/google_edit.css'))

        fragment.initialize_js('GoogleDocumentEditBlock')

        return fragment

    # suffix argument is specified for xblocks, but we are not using herein
    @XBlock.json_handler
    def studio_submit(self, submissions, suffix=''):  # pylint: disable=unused-argument
        """
        Change the settings for this XBlock given by the Studio user
        """

        if not isinstance(submissions, dict):
            LOG.error("submissions object from Studio is not a dict - %r", submissions)
            return {
                'result': 'error'
            }

        if 'display_name' in submissions:
            self.display_name = submissions['display_name']
        if 'library' in submissions:
            self.source_library_id = submissions['library']
        if 'problem' in submissions:
            self.source_problem_id = submissions['problem']
        self.children = []
        value="test"


        self.source_library_version = None

        lib_tools = self.runtime.service(self, 'library_tools')
        # format_block_keys = lambda keys: lib_tools.create_block_analytics_summary(self.location.course_key, [self.source_problem_id])
        # library_content=self.runtime.service(self, 'library_content_module')
        user_id = self.get_user_id()
        # locator =
        lib_tools.librarydetail(self, self.source_library_id, self.source_problem_id, user_id, )
        # if locator:
        #    for child_key in locator.children:
        #         child = self.runtime.get_block(child_key)
        # child_view_name = StudioEditableModule.get_preview_view_name(child)
        # for  block_id in format_block_keys :
        #    yield self.runtime.get_block(self.location.course_key.make_usage_key('problem', block_id))
        # value= lib_tools.create_block_analytics_summary(self.location.course_key, [self.source_problem_id])
        # self.children.append(format_block_keys)
        value = "test"
        return {
            'result': 'success',
            'value': value,
        }

    def student_view(self, context):  # pylint: disable=unused-argument
        """
        Player view, displayed to the student
        """

        fragment = Fragment()
        contents = []
        child_context = {} if not context else copy(context)

        for child in self._get_selected_child_blocks():
            for displayable in child.displayable_items():
                rendered_child = displayable.render(STUDENT_VIEW, child_context)
                fragment.add_fragment_resources(rendered_child)
                contents.append({
                    'id': text_type(displayable.location),
                    'content': rendered_child.content,
                })

        fragment.add_content(self.system.render_template('vert_module.html', {
            'items': contents,
            'xblock_context': context,
            'show_bookmark_button': False,
            'watched_completable_blocks': set(),
            'completion_        delay_ms': None,
        }))

        # str(contents[0].content)
        '''
        fragment.add_content(RESOURCE_LOADER.render_django_template(
            DOCUMENT_TEMPLATE,
            context={"self": self, "contents": contents},
            i18n_service=self.runtime.service(self, 'i18n'),
        ))
        fragment.add_css(RESOURCE_LOADER.load_unicode('public/css/google_docs.css'))
        fragment.add_javascript(RESOURCE_LOADER.load_unicode('public/js/google_docs.js'))

        fragment.initialize_js('GoogleDocumentBlock')
        '''
        return fragment

    # suffix argument is specified for xblocks, but we are not using herein
    @XBlock.json_handler
    def check_url(self, data, suffix=''):  # pylint: disable=unused-argument,no-self-use
        """
        Checks that the given document url is accessible, and therefore assumed to be valid
        """
        try:
            test_url = data['url']
        except KeyError as ex:
            LOG.debug("URL not provided - %s", unicode(ex))
            return {
                'status_code': 400,
            }

        try:
            url_response = requests.head(test_url)
        # Catch wide range of request exceptions
        except requests.exceptions.RequestException as ex:
            LOG.debug("Unable to connect to %s - %s", test_url, unicode(ex))
            return {
                'status_code': 400,
            }

        return {
            'status_code': url_response.status_code,
        }

    @staticmethod
    def workbench_scenarios():
        """
        A canned scenario for display in the workbench.
        """
        return [("Google Docs scenario", "<vertical_demo><google-document/></vertical_demo>")]
