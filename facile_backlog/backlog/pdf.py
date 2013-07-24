from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.units import cm
from reportlab.lib.colors import toColor
from reportlab.lib.pagesizes import A4, LETTER, landscape

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from django.http.response import HttpResponse
from django.template import Context, loader
from django.utils.translation import ugettext as _

from ..core.templatetags.markup import markdown

from xhtml2pdf.document import pisaStory

A4_FORMAT = "a4"
LETTER_FORMAT = "letter"

SHORT_SIDE = "short"
LONG_SIDE = "long"
FRONT_SIDE = "front"

BACK_ORDER_CHOICE = {
    SHORT_SIDE: (),
    LONG_SIDE: (),
}

PAGE_SIZES_CHOICE = {
    A4_FORMAT: landscape(A4),
    LETTER_FORMAT: landscape(LETTER),
}


def get_position(print_format, side):
    w, h = PAGE_SIZES_CHOICE[print_format]
    x1 = 1
    x2 = 0.5*(w/cm)+1
    y1 = 1.5
    y2 = 11.5

    if side == FRONT_SIDE:
        return (
            (x1, y2),
            (x2, y2),
            (x1, y1),
            (x2, y1)
        )
    elif side == LONG_SIDE:
        return (
            (x1, y1),
            (x2, y1),
            (x1, y2),
            (x2, y2)
        )
    elif side == SHORT_SIDE:
        return (
            (x2, y2),
            (x1, y2),
            (x2, y1),
            (x1, y1)
        )
    else:
        raise ValueError("Unknown back_side value {0}".format(side))


SIZE = (12.5, 8)
TOP_HEIGHT = 2


def draw_story_front(c, story, positions, position=0):
    c.saveState()
    pos = positions[position]
    size = SIZE
    c.translate(pos[0]*cm, pos[1]*cm)
    c.setStrokeColorRGB(0.2, 0.5, 0.3)
    c.rect(0, 0, size[0]*cm, size[1]*cm, fill=0)
    c.line(0, (SIZE[1]-TOP_HEIGHT)*cm, size[0]*cm, (SIZE[1]-TOP_HEIGHT)*cm)

    stylesheet = getSampleStyleSheet()
    normalStyle = stylesheet['Normal']
    # Color
    try:
        color = toColor(story.color)
    except ValueError:
        color = toColor("#ffffff")

    c.setFillColor(color)
    c.setStrokeColorRGB(0, 0, 0, alpha=0.1)
    c.rect(0.3*cm, (SIZE[1] - TOP_HEIGHT + 0.3)*cm, 15, (TOP_HEIGHT-0.6)*cm,
           fill=1)

    # theme
    p = Paragraph("<font color=gray size=15>{0}</font>".format(story.theme),
                  normalStyle)
    p.wrap(SIZE[0]*cm, 2*cm)
    p.drawOn(c, 1.1*cm, (SIZE[1]-TOP_HEIGHT+0.4)*cm)

    # Point
    if story.points >= 0:
        txt = "{0:.0f}".format(story.points)
        circle_color = toColor("#BBBBBB")
        txt_color = "white"
    else:
        txt = _("n/a")
        circle_color = toColor("#888888")
        txt_color = "black"
    c.setFillColor(circle_color)
    rad = 0.6
    c.setStrokeColorRGB(0, 0, 0, alpha=0.5)
    c.circle((SIZE[0]-rad - 0.3)*cm, (SIZE[1] - TOP_HEIGHT/2)*cm, rad*cm,
             fill=1)
    p = Paragraph(
        "<para fontSize=20 textColor={0} alignment=center>{1}</font>".format(
            txt_color, txt
        ), normalStyle)
    p.wrap(rad*2*cm, 2*cm)
    p.drawOn(c, (SIZE[0]-(rad*2)-0.29)*cm, (SIZE[1] - TOP_HEIGHT/2 + 0.05)*cm)
    c.setStrokeColorRGB(0, 0, 0, alpha=1.0)

    # Code
    p = Paragraph("<font size=25>{0}</font>".format(story.code), normalStyle)
    p.wrap(5*cm, 2*cm)
    p.drawOn(c, 1.1*cm, (SIZE[1]-TOP_HEIGHT+1.5)*cm)

    # Description
    found = False
    font_size = 15
    leading = 20
    while not found:
        style = ParagraphStyle(name='Custom',
                               parent=normalStyle,
                               fontSize=font_size,
                               leading=leading,
                               rightIndent=20,
                               leftIndent=10,
                               spaceBefore=0,
                               spaceAfter=0,
                               alignment=TA_JUSTIFY)
        # print the html version of the story text
        t = loader.get_template("backlog/user_story_text.html")
        text = t.render(Context({
            'story': story
        }))
        p = Paragraph(text, style)
        aW = SIZE[0]*cm
        aH = (SIZE[1]-TOP_HEIGHT)*cm
        w, h = p.wrap(aW, aH)  # find required space
        if w <= aW and h <= aH:
            p.drawOn(c, 0, (SIZE[1]-TOP_HEIGHT)*cm - h - 0.1*cm)
            found = True
        else:
            font_size -= 1
            leading -= 1
            # raise ValueError("Not enough room")
    # print order
    c.setStrokeColorRGB(0, 0, 0, alpha=0.2)
    p = Paragraph("<font size=8 color=#cccccc>{0}</font>".format(
        story.order+1), normalStyle)
    p.wrap(0.5*cm, 0.5*cm)
    p.drawOn(c, 0.2*cm, 0.1*cm)

    c.restoreState()


def draw_story_back(c, story, positions, position=0):
    c.saveState()
    pos = positions[position]
    size = SIZE
    c.translate(pos[0]*cm, pos[1]*cm)
    c.setStrokeColorRGB(0.2, 0.3, 0.5)
    c.rect(0, 0, size[0]*cm, size[1]*cm, fill=0)

    stylesheet = getSampleStyleSheet()
    normalStyle = stylesheet['Normal']

     # Code
    p = Paragraph("<font size=15>{0}</font>".format(story.code), normalStyle)
    p.wrap(5*cm, 2*cm)
    p.drawOn(c, 1.1*cm, (SIZE[1]-TOP_HEIGHT+1.5)*cm)

    # Draw acceptance criteria
    html = u"""
        <div style="font-size:13px">{0}</div>
    """.format(markdown(story.acceptances))
    context = pisaStory(html)
    f = Frame(0, 0, size[0]*cm, (size[1]-TOP_HEIGHT/2)*cm, showBoundary=1)
    f.addFromList(context.story, c)
    c.restoreState()


def generate_pdf(stories, file_name,
                 print_side=LONG_SIDE, print_format=A4_FORMAT):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = \
        'attachment; filename="{0}"'.format(file_name)

    # Create the PDF object, using the response object as its "file."
    c = canvas.Canvas(response, PAGE_SIZES_CHOICE[print_format])
    c.setAuthor("backlogman.com")
    c.setTitle("User story printing")
    c.setSubject("Stories")
    i = 0
    front = True
    front_positions = get_position(print_format, FRONT_SIDE)
    back_position = get_position(print_format, print_side)
    story_per_page = len(front_positions)
    while i < len(stories) or front:
        m = divmod(i, story_per_page)[1]
        if i < len(stories):
            story = stories[i]
            if front:
                draw_story_front(c, story, front_positions, m)
            else:
                draw_story_back(c, story, back_position, m)
        i += 1
        if m == story_per_page-1:
            if front:
                front = False
                i -= 4
            else:
                front = True
            if i < len(stories):
                c.showPage()

    c.showPage()
    c.save()
    return response
