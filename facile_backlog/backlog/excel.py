from django.http.response import HttpResponse
from django.utils.translation import ugettext as _, activate

from xlwt import Workbook, XFStyle, Borders, Pattern, Font


def export_excel(stories, file_name):
    file_name = u"{0}.xls".format(file_name)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = \
        'attachment; filename="{0}"'.format(file_name)
    book = Workbook()

    fnt = Font()
    fnt.name = 'Arial'
    fnt.bold = True

    fnt2 = Font()
    fnt2.name = 'Arial'
    fnt2.bold = True
    fnt2.height = 400

    borders = Borders()
    borders.bottom = Borders.THICK

    pattern = Pattern()
    pattern.pattern = Pattern.SOLID_PATTERN
    pattern.pattern_fore_colour = 0x01

    style = XFStyle()
    style.font = fnt
    style.borders = borders
    style.pattern = pattern

    style2 = XFStyle()
    style2.font = fnt2

    sheet1 = book.add_sheet('Sheet 1')
    sheet1.write(0, 0, "Backlogman stories export", style2)
    row_head = sheet1.row(1)

    row_head.write(0, _("Code"), style)
    row_head.write(1, _("Description"), style)
    row_head.write(2, _("Theme"), style)
    row_head.write(3, _("Points"), style)
    row_head.write(4, _("Status"), style)

    row = 2
    for story in stories:
        if story.project.lang:
            activate(story.project.lang)

        if story.points >= 0:
            points_str = story.points
        else:
            points_str = ""
        r = sheet1.row(row)
        r.write(0, story.code)
        r.write(1, story.text)
        r.write(2, story.theme)
        r.write(3, points_str)
        r.write(4, story.get_status_display())
        row += 1

    sheet1.col(1).width = 10000

    book.save(response)
    return response
