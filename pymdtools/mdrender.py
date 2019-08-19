﻿# coding: utf-8
"""
    Markdown renderer
    ~~~~~~~~~~~~~~~~~

    This class renders parsed markdown back to markdown.
    It is useful for automatic modifications of the md contents.

    :copyright: (c) 2015 by Jaroslav Kysela
    :licence: WTFPL 2
"""

if (__package__ in [None, '']) and ('.' not in __name__):
    import mistunege as mistune
else:
    from . import mistunege as mistune

class MdRenderer(mistune.Renderer):

    def get_block(text):
        type = text[0]
        p = text.find(':')
        if p <= 0:
            return ('', '', '')
        l = int(text[1:p])
        t = text[p + 1:p + 1 + l]
        return (text[p + 1 + l:], type, t)

    def newline(self):
        return '\n'

    def text(self, text):
        return text

    def linebreak(self):
        return '\n'

    def hrule(self):
        return '---\n'

    def header(self, text, level, raw=None):
        if level == 1:
            return text + '\n' + '=' * len(text) + '\n\n'
        if level == 2:
            return text + '\n' + '-' * len(text) + '\n\n'
        return '#' * (level) + ' ' + text + '\n\n'

    def paragraph(self, text):
        return text.rstrip() + '\n\n'

    def list(self, text, ordered=True):
        r = ''
        while text:
            text, type, t = MdRenderer.get_block(text)
            if type == 'l':
                t = t.strip()
                t = t.replace('\n  + ', '\n    * ')
                t = t.replace('\n- ', '\n  + ')
                r += (ordered and ('# ' + t) or ('- ' + t))
                if r[-1] != '\n':
                    r += '\n'
            else:
                r += '\n'
        if len(r) > 1 and r[1] == '\n':
            r = r[1:]
        return r + '\n'

    def list_item(self, text):
        return 'l' + str(len(text)) + ':' + text

    def block_code(self, code, lang=None):
        return '```\n' + code + '\n```\n'

    def block_quote(self, text):
        r = ''
        for line in text.splitlines():
            r += (line and '> ' or '') + line + '\n'
        return r

    def _emphasis(self, text, pref):
        return pref + text + pref  # + ' '

    def emphasis(self, text):
        return self._emphasis(text, '*')

    def double_emphasis(self, text):
        return self._emphasis(text, '**')

    def strikethrough(self, text):
        return self._emphasis(text, '~~')

    def codespan(self, text):
        return '`' + text + '`'

    def autolink(self, link, is_email=False):
        return '<' + link + '>'

    def link(self, link, title, text, image=False):
        r = (image and '!' or '') + '[' + text + '](' + link + ')'
        if title:
            r += '"' + title + '"'
        return r

    def image(self, src, title, text):
        self.link(src, title, text, image=True)

    def table(self, header, body):
        hrows = []
        while header:
            header, type, t = MdRenderer.get_block(header)
            if type == 'r':
                flags = {}
                cols = []
                while t:
                    t, type2, t2 = MdRenderer.get_block(t)
                    if type2 == 'f':
                        fl, v = t2.split('=')
                        flags[fl] = v
                    elif type2 == 'c':
                        cols.append({'type': type, 'flags': flags, 'text': t2})
                hrows.append(cols)
        brows = []
        while body:
            body, type, t = MdRenderer.get_block(body)
            if type == 'r':
                flags = {}
                cols = []
                while t:
                    t, type2, t2 = MdRenderer.get_block(t)
                    if type2 == 'f':
                        fl, v = t2.split('=')
                        flags[fl] = v
                    elif type2 == 'c':
                        cols.append({'type': type, 'flags': flags, 'text': t2})
                brows.append(cols)
        colscount = 0
        colmax = [0] * 100
        align = [''] * 100
        for row in hrows + brows:
            colscount = max(len(row), colscount)
            i = 0
            for col in row:
                colmax[i] = max(len(col['text']), colmax[i], 3)
                if 'align' in col['flags']:
                    align[i] = col['flags']['align'][0]
                i += 1
        r = ''
        for row in hrows:
            i = 0
            for col in row:
                if i == 0:
                    r += '| '
                if i > 0:
                    r += ' | '
                r += col['text'].ljust(colmax[i])
                i += 1
            r += ' |\n'
        for i in range(colscount):
            if i == 0:
                r += '|'
            if i > 0:
                r += '|'
            if align[i] == 'c':
                r += ':' + '-'.ljust(colmax[i], '-') + ':'
            elif align[i] == 'l':
                r += ':' + '-'.ljust(colmax[i] + 1, '-')
            elif align[i] == 'r':
                r += '-'.ljust(colmax[i] + 1, '-') + ':'
            else:
                r += '-'.ljust(colmax[i] + 2, '-')
        r += '|\n'
        for row in brows:
            i = 0
            for col in row:
                if i == 0:
                    r += '| '
                if i > 0:
                    r += ' | '
                r += col['text'].ljust(colmax[i])
                i += 1
            r += ' |\n'
        r += '\n'
        return r

    def table_row(self, content):
        return 'r' + str(len(content)) + ':' + content

    def table_cell(self, content, **flags):
        content = content.replace('\n', ' ')
        r = ''
        for fl in flags:
            v = flags[fl]
            if type(v) == type(True):
                v = v and 1 or 0
            v = str(v) and str(v) or ''
            r += 'f' + str(len(fl) + 1 + len(v)) + ':' + fl + '=' + v
        return r + 'c' + str(len(content)) + ':' + content

    def footnote_ref(self, key, index):
        return '[^' + str(index) + ']'

    def footnote_item(self, key, text):
        r = '[^' + str(index) + ']:\n'
        for l in text.split('\n'):
            r += '  ' + l.lstrip().rstrip() + '\n'
        return r

    def footnotes(self, text):
        return text
