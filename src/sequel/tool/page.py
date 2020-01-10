"""
Page class
"""

import abc
import collections
import enum
import itertools
import os
import re
import textwrap
import types

import termcolor

from .display import Printer


__all__ = [
    'Element',
    'Title',
    'Separator',
    'Break',
    'Paragraph',
    'Quotation',
    'WrappedParagraph',
    'Page',
]


class NavigationStatus(enum.Enum):
    SUCCESS = 0
    FAILURE = 1


class NavigationAction(enum.Enum):
    QUIT = 0
    HOME = 1
    BACK = 2
    LINK = 3


Link = collections.namedtuple(
    "Link", "text action data")


LinkResult = collections.namedtuple(
    "LinkResult", "status link page")


def wrap(text):
    return textwrap.fill(text, break_on_hyphens=False)


def transform_link(text):
    return text.upper().replace(" ", "-")


class Element(abc.ABC):
    def render(self, printer, interactive=True):
        return self.get_text()

    @abc.abstractmethod
    def get_text(self):
        raise NotImplementedError()


class Title(Element):
    def __init__(self, title, level):
        self._title = title
        self._level = level

    def get_text(self):
        text = "━━━┫ " + self._title + " ┣"
        text += "━" * (70 - len(text))
        return text

    def render(self, printer, interactive=True):
        return printer.color(self.get_text(), "bold", "blue")


class Break(Element):
    def get_text(self):
        return None

    def render(self, printer, interactive=True):
        # print(":::", interactive)
        # input("--------------------")
        if interactive:
            printer.pager().interrupt()
        return self.get_text()
        # input(printer.red(text))
        # return '\r' + ' ' * len(text) + '\r'


class Separator(Element):
    def __init__(self, ch="━"):
        self.ch = ch

    def get_text(self):
        return self.ch * 70


class Paragraph(Element):
    def __init__(self, text):
        self.set_text(text)

    def set_text(self, text):
        self._text = text

    def get_text(self):
        return self._text


class Quotation(Paragraph):
    pass


class NavigatorParagraphMixin(object):
    def __init__(self, navigator, interactive=False):
        self._navigator = navigator
        self.interactive = interactive
        super().__init__(None)

    def get_text(self):
        if self._text is None:
            self.set_text(self._create_text())
        return super().get_text()


class WrappedParagraph(Paragraph):
    def __init__(self, text):
        self._text = text

    def get_text(self):
        return wrap(self._text)


class IndexParagraph(NavigatorParagraphMixin, Paragraph):
    def _create_text(self):
        lst = []
        navigator = self._navigator
        for page_name in navigator.ordered_pages():
            page = navigator.get_page(page_name)
            if page.level == 0:
                #bullet = "●"
                bullet = "▸"
            else:
                #bullet = "○"
                bullet = "▹"
            lst.append(
                " {}{} {}".format("  " * page.level, bullet, transform_link(page.name)),
            )
        return '\n'.join(lst)


class MenuParagraph(NavigatorParagraphMixin, WrappedParagraph):
    def _create_text(self):
        links = self._navigator.links()
        lines = [
            "─── navigation ───────────────────────────────────────────────────────",
            " | ".join("{}".format(transform_link(link)) for link in links),
            "──────────────────────────────────────────────────────────────────────",
        ]
        return '\n'.join(lines)


def split_text(text):
    for paragraph in text.split('\n\n'):
        yield WrappedParagraph(paragraph)


class Page(object):
    __re_split__ = re.compile(r'\n\n+')

    def __init__(self, name, elements, title=None, parent=None):
        self._parent = parent
        if parent is None:
            level = 0
        else:
            level = self._parent.level + 1
        self._level = level
        self._name = name
        if title is None:
            title = name.title()
        self._title = title
        self._elements = []
        self.add_element(Title(title, level=0))
        for element in elements:
            self.add_element(element)

    @property
    def parent(self):
        return self._parent

    @property
    def level(self):
        return self._level

    def add_element(self, element):
        if isinstance(element, str):
            self._elements.extend(split_text(element))
        elif isinstance(element, Element):
            self._elements.append(element)
        else:
            raise TypeError("{!r} is not a Paragraph".format(element))

    @property
    def name(self):
        return self._name

    @property
    def title(self):
        return self._title

    @property
    def elements(self):
        yield from self._elements

    def __repr__(self):
        return "{}({!r})".format(type(self).__name__, self._name)


class IndexPage(Page):
    def __init__(self, name, navigator):
        super().__init__(name=name, elements=[IndexParagraph(navigator)])


class Navigator(collections.abc.Mapping):
    def __init__(self, *pages, index_name='index', printer=None):
        if printer is None:
            printer = Printer()
        self.printer = printer
        self._pages = collections.OrderedDict()
        self._links = collections.OrderedDict()
        self._links_proxy = types.MappingProxyType(self._links)
        self.home_name = None
        self.index_name = index_name
        for page in pages:
            self.add_page(page)
        self._add_link(Link(text='quit', action=NavigationAction.QUIT, data={}))
        self._add_link(Link(text='home', action=NavigationAction.HOME, data={}))
        self._add_link(Link(text='back', action=NavigationAction.BACK, data={}))
        self._crono = []

    def __getitem__(self, name):
        return self._pages[name]

    def __iter__(self):
        yield from self._pages

    def __len__(self):
        return len(self._pages)

    def links(self):
        return self._links_proxy

    def home_page(self):
        if not self._pages:
            return
        home_name = self.home_name
        if home_name is None:
            home_name = tuple(self._pages)[0]
        home_page = self[home_name]
        return home_page
        
    def get_page(self, page_name):
        return self._pages[page_name]

    def _add_link(self, link):
        self._links[transform_link(link.text)] = link

    ### actions:
    def do_quit(self, link):
        return LinkResult(status=NavigationStatus.SUCCESS, link=link, page=None)

    def do_home(self, link):
        home_page = self.home_page()
        return LinkResult(status=NavigationStatus.SUCCESS, link=link, page=home_page)

    def do_back(self, link):
        if self._crono:
            page = self._crono.pop()
        else:
            page = None
        return LinkResult(status=NavigationStatus.SUCCESS, link=link, page=page)

    def do_link(self, link):
        page = link.data['page']
        return LinkResult(status=NavigationStatus.SUCCESS, link=link, page=page)

    def add_page(self, page, is_home=False):
        if page.name in self._pages:
            raise ValueError("page {!r} already inserted".format(page.name))
        self._pages[page.name] = page
        if is_home:
            self.home_name = page.name
        link_text = page.name
        link = Link(
            text=link_text,
            action=NavigationAction.LINK,
            data={'page': page})
        self._add_link(link)

    def new_page(self, name, elements=(), title=None, parent=None, is_home=False):
        if isinstance(parent, str):
            parent = self._pages[parent]
        page = Page(name=name, elements=elements, title=title, parent=parent)
        self.add_page(page, is_home=is_home)
        return page

    def _execute_link(self, link):
        if link.action is NavigationAction.QUIT:
            do_function = self.do_quit
        elif link.action is NavigationAction.BACK:
            do_function = self.do_back
        elif link.action is NavigationAction.HOME:
            do_function = self.do_home
        elif link.action is NavigationAction.LINK:
            do_function = self.do_link
        else:
            raise ValueError("{!r} is not a NavigationAction".format(link.action))
        return do_function(link)

    def follow_link(self, text):
        link = self._links.get(text, None)
        if link is None:
            # start
            matching_links = [link for link in self._links.values() if link.text.startswith(text)]
            if len(matching_links) == 1:
                link = matching_links[0]
            elif len(matching_links) > 1:
                matches = []
                for matching_link in matching_links:
                    matches.append(self.printer.red(text) + matching_link.text[len(text):])
                self.printer("Multiple matches: " + " | " .join(matches))
                link = None
        if link:
            return self._execute_link(link)
        else:
            return LinkResult(status=NavigationStatus.FAILURE, link=None, page=None)

    def add_index(self):
        if self.index_name is not None:
            root_pages = set(self.root_pages())
            if self.index_name not in root_pages:
                self.add_page(IndexPage(self.index_name, self))
                
    def pages(self, condition=lambda page: True):
        page_names = []
        for page in self._pages.values():
            if condition(page):
                page_names.append(page.name)
        return page_names

    def root_pages(self):
        return self.pages(condition=lambda page: page.parent is None)

    def ordered_pages(self):
        def order(page_names, dct, lst):
            for page_name in page_names:
                lst.append(page_name)
                if page_name in dct:
                    order(dct[page_name], dct, lst)
            return lst

        dct = collections.defaultdict(list)
        l0 = []
        for page in self._pages.values():
            if page.parent is not None:
                dct[page.parent.name].append(page.name)
            else:
                l0.append(page.name)
        
        olist = []
        order(l0, dct, olist)
        return olist

    def navigate(self, start_links=(), interactive=None):
        start_links = list(start_links)
        if interactive is None:
            interactive = not bool(start_links)

        if interactive:
            menu = MenuParagraph(self)
        else:
            menu = None
        self.add_index()

        printer = self.printer
        self._crono.clear()
       
        if start_links:
            page = None
        else:
            page = self.home_page()
        while True:
            if page is not None:
                renderer = Renderer(self, printer, current_page_name=page.name, interactive=interactive)
                renderer(page)
                # text = page.render(printer)
                if interactive:
                    renderer(menu)
            while True:
                try:
                    if start_links:
                        link_text = start_links.pop(0)
                    else:
                        if interactive:
                            link_text = input(self.printer.color("HELP", "bold") + "> ")
                        else:
                            link_text = 'quit'
                except (KeyboardInterrupt, EOFError):
                    return
                if not link_text:
                    continue
                link_result = self.follow_link(link_text)
                if link_result.status == NavigationStatus.FAILURE:
                    self.printer(self.printer.red("ERR: no such page: {!r}".format(link_text)))
                else:
                    if link_result.link.action is NavigationAction.QUIT:
                        return
                    next_page = link_result.page
                    if next_page is None:
                        next_page = page
                    if link_result.link.action is not NavigationAction.BACK:
                        self._crono.append(page)
                    page = next_page
                    break


class Renderer(object):
    def __init__(self, navigator, printer, current_page_name=None, interactive=True):
        self.printer = printer
        self.interactive = interactive
        self.pager = self.printer.pager(interactive=self.interactive)
        opages = navigator.ordered_pages()
        olink_pages = [transform_link(page_name) for page_name in opages]
        olinks = [link for link in navigator.links() if link not in set(olink_pages)] + olink_pages
        nmin = {olink: 1 for olink in olinks}
        for ol0, ol1 in itertools.combinations(olinks, 2):
            for num, (ch0, ch1) in enumerate(itertools.zip_longest(ol0, ol1)):
                if ch0 != ch1:
                    break
            nmin[ol0] = max(nmin[ol0], num + 1)
            nmin[ol1] = max(nmin[ol1], num + 1)

        lsub = []
        for transformed_link_text, link in navigator.links().items():
            text = link.text
            if link.text == current_page_name:
                color = "blue"
                attrs = ["bold", "underline"]
            else:
                color = "blue"
                attrs = ["underline"]
            # print(link.text, current_page_name, color, attrs)
            # rendered_link_text = termcolor.colored(text, color, attrs=attrs)
            rendered_link_text = termcolor.colored(text[:nmin[transformed_link_text]], color, attrs=attrs + ["reverse"]) + \
                                 termcolor.colored(text[nmin[transformed_link_text]:], color, attrs=attrs)

            link_re = re.compile(r'\b(?<!-){}\b'.format(re.escape(transformed_link_text)))
            lsub.append((link_re, rendered_link_text))
        self._lsub = lsub

    def __call__(self, obj):
       if isinstance(obj, Page):
           for element in obj.elements:
               self(element)
       elif isinstance(obj, Element):
           self.render(obj.render(self.printer, interactive=self.interactive))
       else:
           self.render(obj, interactive=self.interactive)

    def render(self, text):
       if text is not None:
           rendered_text = text
           for link_re, rendered_link_text in self._lsub:
               rendered_text = link_re.sub(rendered_link_text, rendered_text)
           self.pager(rendered_text)
