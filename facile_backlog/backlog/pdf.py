from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.units import cm
from reportlab.lib.colors import toColor
from reportlab.lib.pagesizes import A4, landscape

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from django.http.response import HttpResponse
from django.template import Context, loader
from django.utils.translation import ugettext as _

from ..core.templatetags.markup import markdown

from xhtml2pdf.document import pisaStory


POSITIONS = (
    (1.5, 1.5),
    (15, 1.5),
    (1.5, 11),
    (15, 11)
)

SIZE = (12.5, 8)
TOP_HEIGHT = 2


def draw_story_front(c, story, position=0):
    c.saveState()
    pos = POSITIONS[position]
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
        txt = "{0}".format(story.points)
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
    style = ParagraphStyle(name='Custom',
                           parent=normalStyle,
                           fontSize=15,
                           leading=20,
                           rightIndent=6,
                           leftIndent=6,
                           spaceBefore=0,
                           spaceAfter=0)
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
    else:
        raise ValueError("Not enough room")
    c.restoreState()


def draw_story_back(c, story, position=0):
    c.saveState()
    pos = POSITIONS[position]
    size = SIZE
    c.translate(pos[0]*cm, pos[1]*cm)
    c.setStrokeColorRGB(0.2, 0.3, 0.5)
    c.rect(0, 0, size[0]*cm, size[1]*cm, fill=0)
    html = u"""
        <div style="font-size:15px">{0}</div>
    """.format(markdown(story.acceptances))
    context = pisaStory(html)
    f = Frame(0, 0, size[0]*cm, size[1]*cm, showBoundary=0)
    f.addFromList(context.story, c)
    c.restoreState()


def generate_pdf(stories, file_name):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = \
        'attachment; filename="{0}"'.format(file_name)

    # Create the PDF object, using the response object as its "file."
    c = canvas.Canvas(response, pagesize=landscape(A4))

    i = 0
    front = True
    story_per_page = len(POSITIONS)
    while i < max(4, len(stories)):
        m = divmod(i, story_per_page)[1]
        if i < len(stories):
            story = stories[i]
            if front:
                draw_story_front(c, story, m)
            else:
                draw_story_back(c, story, m)
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
