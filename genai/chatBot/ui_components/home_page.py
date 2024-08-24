from fasthtml.common import *

def main_template():
    """The part below the navbar for the main page"""

    return Div(
        "Hey this is the main page!",
        cls = 'h-[70vh] flex items-center justify-center text-xl',
        id = 'template'
    )


def get_navbar():
    """Returns the navigation bar"""

    return Div(
        Div(
            A(
                "Home", 
                cls = 'btn btn-ghost text-xl',
                # hx_get = '/',
                # # hx_target = '#template',
                # hx_swap = 'innerHTML'
            ),
            A(
                "Let's Chat", 
                cls = 'btn btn-ghost text-xl',
                hx_get = '/chat-window',
                hx_target = '#template',
                hx_swap = 'outerHTML'
            ),
            cls = 'flex-1',
        ),
        cls = 'navbar bg-base-100',
    )

def get_homepage():
    """Two partition screen, navbar & main screen"""
    navbar = get_navbar()
    main_div = main_template()

    return navbar, main_div