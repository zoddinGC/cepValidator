error_color_css = 'background-color: lightcoral; color: white; text-align: center;'

def highlight_headers():
    return error_color_css

# def highlight_rows(row, error):
#     colors = []
#     for val in row:
#         if  val == error:
#             colors.append(error_color_css)
#         elif error in row.values:
#             colors.append('background-color: #FF9F9F; color: black;')
#         else:
#             colors.append('')

#     return colors