from django.http.response import HttpResponse
from django.utils.translation import ugettext as _, activate

from xlwt import Workbook, easyxf

INDEXES = ('code', 'text', 'theme', 'points', 'status', 'backlog', 'criteria',
           'comments', 'archived')


def export_excel(stories, file_name, title=None):
    file_name = u"{0}.xls".format(file_name)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = \
        'attachment; filename="{0}"'.format(file_name)
    book = Workbook()

    header_style = easyxf(
        'font: name Arial, bold True;'
        'borders: bottom thin;'
        'pattern: pattern solid, fore_colour gray25;',
    )

    title_style = easyxf(
        'font: name Arial, height 400, bold True;'
    )

    sheet1 = book.add_sheet('Sheet 1')
    if not title:
        title = _("Backlogman stories export")
    sheet1.write(0, 0, title, title_style)
    row_head = sheet1.row(1)

    row_head.write(INDEXES.index('code'), _("Code"), header_style)
    row_head.write(INDEXES.index('text'), _("Description"), header_style)
    row_head.write(INDEXES.index('theme'), _("Theme"), header_style)
    row_head.write(INDEXES.index('points'), _("Points"), header_style)
    row_head.write(INDEXES.index('status'), _("Status"), header_style)
    row_head.write(INDEXES.index('backlog'), _("Backlog"), header_style)
    row_head.write(INDEXES.index('criteria'), _("acceptances"), header_style)
    row_head.write(INDEXES.index('comments'), _("Comments"), header_style)
    row_head.write(INDEXES.index('archived'), _("Archived"), header_style)

    wrap_style = easyxf(
        'alignment: wrap True;'
    )
    code_style = easyxf(
        'font:  bold True;'
    )
    row = 2
    for story in stories:
        if story.project.lang:
            activate(story.project.lang)

        if story.points >= 0:
            points_str = story.points
        else:
            points_str = ""
        r = sheet1.row(row)
        r.write(INDEXES.index('code'), story.code, code_style)
        r.write(INDEXES.index('text'), story.text, wrap_style)
        r.write(INDEXES.index('theme'), story.theme)
        r.write(INDEXES.index('points'), points_str)
        r.write(INDEXES.index('status'), story.get_status_display())
        r.write(INDEXES.index('backlog'), story.backlog.name)
        r.write(INDEXES.index('criteria'), story.acceptances, wrap_style)
        r.write(INDEXES.index('comments'), story.comments, wrap_style)
        r.write(
            INDEXES.index('archived'),
            (_("Archived") if story.backlog.is_archive else "")
        )
        row += 1

    sheet1.col(INDEXES.index('text')).width = 10000
    sheet1.col(INDEXES.index('criteria')).width = 10000
    sheet1.col(INDEXES.index('comments')).width = 10000
    book.save(response)
    return response
