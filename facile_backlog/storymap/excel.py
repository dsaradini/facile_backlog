from django.http.response import HttpResponse

from xlwt import Workbook, easyxf, add_palette_colour
from palette import Color

from models import Story


def export_excel(story_map, file_name, title=None):
    colors = Story.objects.filter(
        theme__story_map=story_map
    ).order_by('color').values("color").distinct('color')
    color_list = [c['color'] for c in colors]

    file_name = u"{0}.xls".format(file_name)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = \
        'attachment; filename="{0}"'.format(file_name)
    book = Workbook()

    i = 0
    ix = 0x21
    for c in color_list:
        add_palette_colour("board_color_{0}".format(i), ix)
        color = Color(c)
        book.set_colour_RGB(ix,
                            int(color.r * 255),
                            int(color.g * 255),
                            int(color.b * 255))
        ix += 1
        i += 1

    header_style = easyxf(
        'font: name Arial, bold True, height 250;'
        'borders: bottom thin;'
        'alignment: horizontal center;'
        'pattern: pattern solid, fore_colour gray25;',
    )

    sheet1 = book.add_sheet('Board')

    row = 0
    row_head = sheet1.row(row)

    themes = story_map.themes.all()
    index = 1
    for theme in themes:
        row_head.write(index, theme.name, header_style)
        sheet1.col(index).width = 5000
        index += 1

    phase_style = easyxf(
        'alignment: horizontal center, vertical center;'
        'font:  bold True;'
        'border: right thin, top thin;'
        'pattern: pattern solid, fore_colour gray25;'
    )

    row += 1
    for phase in story_map.phases.all():
        max_stories = 1
        index = 1
        for theme in themes:
            stories = phase.stories.filter(theme=theme).all()
            row_index = row
            for story in stories:
                color = "board_color_{0}".format(color_list.index(story.color))
                print "COLOR", color
                style = easyxf(
                    'alignment: wrap True, horizontal center, vertical top;'
                    'border: left thin, top thin, right thin, bottom thin;'
                    'pattern: pattern solid, fore_colour {0};'.format(color)
                )
                sheet1.write(row_index, index, story.title, style)
                row_index += 1
            index += 1
            max_stories = max(max_stories, len(stories))
        index = 0
        # write theme name
        sheet1.write_merge(row, (row + max_stories - 1), index, index,
                           phase.name, phase_style)
        row += max_stories
    book.save(response)
    return response
