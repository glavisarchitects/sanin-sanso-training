# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json

from odoo import http
from odoo.http import request
from odoo.tools import misc
from odoo.addons.base_import.controllers.main import ImportController


class SSERPImportController(ImportController):

    @http.route('/base_import/set_file', methods=['POST'])
    def set_file(self, file, import_id, jsonp='callback'):
        import_id = int(import_id)

        # HuuPhong add 220322
        if file.filename.endswith('.csv') or file.filename.endswith('.CSV'):
            file_type = 'text/csv'
        else:
            file_type = file.content_type

        written = request.env['base_import.import'].browse(import_id).write({
            'file': file.read(),
            'file_name': file.filename,
            'file_type': file_type,
        })

        return 'window.top.%s(%s)' % (misc.html_escape(jsonp), json.dumps({'result': written}))
