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

import termcolor

from .display import Printer


__all__ = [
    'Paragraph',
    'RawParagraph',
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
    def render(self, printer):
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

    def render(self, printer):
        return printer.color(self.get_text(), "bold", "blue")


class Separator(Element):
    def __init__(self, ch="━"):
        self.ch = ch

    def get_text(self):
        return self.ch * 70


class Paragraph(Element):
    def __init__(self, text):
        self._text = text

    def get_text(self):
        return self._text


class WrappedParagraph(Paragraph):
    def __init__(self, text):
        self._text = text

    def get_text(self):
        return wrap(self._text)


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

    def render(self, printer):
        # header = "━━━┫ " + printer.color(self._name, "blue", "bold") + " ┣"
        # header += "━" * (70 - len(header))
        # self.printer(header)
        # #menu = "navigation: " + " | ".join("{}".format(transform_link(link)) for link in self._links)
        lst = []
        for element in self._elements:
            lst.append(element.render(printer))
        text = '\n\n'.join(lst)
        return text

    def __repr__(self):
        return "{}({!r})".format(type(self).__name__, self._name)


class Navigator(collections.abc.Mapping):
    def __init__(self, *pages, index_name='index', printer=None):
        if printer is None:
            printer = Printer()
        self.printer = printer
        self._pages = collections.OrderedDict()
        self._links = collections.OrderedDict()
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

    def home_page(self):
        if not self._pages:
            return
        home_name = self.home_name
        if home_name is None:
            home_name = tuple(self._pages)[0]
        home_page = self[home_name]
        return home_page
        
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

    def navigate(self):
        printer = self.printer
        page = self.home_page()
        self._crono.clear()
        opages = self.ordered_pages()
        if self.index_name is not None and self.index_name not in opages:
            #self.index_page = self.new_page(self.index_name)
            index_page = self.new_page(self.index_name)
            opages.append(index_page.name)
            lst = []
            for page_name in opages:
                page = self._pages[page_name]
                if page.level == 0:
                    #bullet = "●"
                    bullet = "▸"
                else:
                    #bullet = "○"
                    bullet = "▹"
                lst.append(
                    " {}{} {}".format("  " * page.level, bullet, transform_link(page.name)),
                )
            index_page.add_element(Paragraph("\n".join(lst)))
        olink_pages = [transform_link(page_name) for page_name in opages]
        olinks = [link for link in self._links if link not in set(olink_pages)] + olink_pages
        menu = " | ".join("{}".format(transform_link(link)) for link in olinks)
        menu = wrap(menu)
        nmin = {olink: 1 for olink in olinks}
        for ol0, ol1 in itertools.combinations(olinks, 2):
            for num, (ch0, ch1) in enumerate(itertools.zip_longest(ol0, ol1)):
                if ch0 != ch1:
                    break
            nmin[ol0] = max(nmin[ol0], num + 1)
            nmin[ol1] = max(nmin[ol1], num + 1)
       
        while page is not None:
            lsub = []
            for transformed_link_text, link in self._links.items():
                text = link.text
                rendered_link_text = termcolor.colored(text, "blue", attrs=["underline"])
                if link.text == page.name:
                    color = "red"
                    attrs = ["underline"]
                else:
                    color = "blue"
                    attrs = ["underline"]
                menu_rendered_link_text = termcolor.colored(text[:nmin[transformed_link_text]], color, attrs=attrs + ["reverse"]) + \
                                          termcolor.colored(text[nmin[transformed_link_text]:], color, attrs=attrs)
                link_re = re.compile(r'\b(?<!-){}\b'.format(re.escape(transformed_link_text)))
                lsub.append((link_re, rendered_link_text, menu_rendered_link_text))
            
            text = page.render(printer)
            rendered_text = text
            rendered_menu = menu
            for link_re, rendered_link_text, menu_rendered_link_text in lsub:
                rendered_text = link_re.sub(rendered_link_text, rendered_text)
                rendered_menu = link_re.sub(menu_rendered_link_text, rendered_menu)
            printer(rendered_text)
            printer("─" * 70)
            printer(rendered_menu)
            printer("─" * 70)
            while True:
                try:
                    link_text = input(self.printer.color("HELP", "bold") + "> ")
                except (KeyboardInterrupt, EOFError):
                    return
                if not link_text:
                    continue
                link_result = self.follow_link(link_text)
                if link_result.status == NavigationStatus.FAILURE:
                    self.printer(self.printer.red("ERR: invalid choice {!r}".format(link_text)))
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

