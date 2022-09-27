# -*- coding: utf-8 -*-

import babel.messages.pofile
import base64
import copy
import datetime
import functools
import glob
import hashlib
import io
import itertools
import jinja2
import json
import logging
import operator
import os
import re
import sys
import tempfile

import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
from collections import OrderedDict, defaultdict, Counter
from werkzeug.urls import url_encode, url_decode, iri_to_uri
from lxml import etree
import unicodedata


import odoo
import odoo.modules.registry
from odoo.api import call_kw, Environment
from odoo.modules import get_module_path, get_resource_path
from odoo.tools import image_process, topological_sort, html_escape, pycompat, ustr, apply_inheritance_specs, lazy_property, float_repr
from odoo.tools.mimetypes import guess_mimetype
from odoo.tools.translate import _
from odoo.tools.misc import str2bool, xlsxwriter, file_open
from odoo.tools.safe_eval import safe_eval, time
from odoo import http, tools
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception, Response
from odoo.exceptions import AccessError, UserError, AccessDenied
from odoo.models import check_method_name
from odoo.service import db, security


class Binary(http.Controller):

    @http.route(['/web/content',
        '/web/content/<string:xmlid>',
        '/web/content/<string:xmlid>/<string:filename>',
        '/web/content/<int:id>',
        '/web/content/<int:id>/<string:filename>',
        '/web/content/<int:id>-<string:unique>',
        '/web/content/<int:id>-<string:unique>/<string:filename>',
        '/web/content/<int:id>-<string:unique>/<path:extra>/<string:filename>',
        '/web/content/<string:model>/<int:id>/<string:field>',
        '/web/content/<string:model>/<int:id>/<string:field>/<string:filename>'], type='http', auth="public")
    def content_common(self, xmlid=None, model='ir.attachment', id=None, field='datas',
                       filename=None, filename_field='name', unique=None, mimetype=None,
                       download=None, data=None, token=None, access_token=None, **kw):

        status, headers, content = request.env['ir.http'].binary_content(
            xmlid=xmlid, model=model, id=id, field=field, unique=unique, filename=filename,
            filename_field=filename_field, download=download, mimetype=mimetype, access_token=access_token)

        if status != 200:
            return request.env['ir.http']._response_by_status(status, headers, content)
        else:
            # delete ir.attachment no need to save, eg svf pdf
            attachment_rec = request.env['ir.attachment'].sudo().browse(id)
            if attachment_rec.x_no_need_save:
                attachment_rec.sudo().unlink()

            content_base64 = base64.b64decode(content)
            headers.append(('Content-Length', len(content_base64)))
            response = request.make_response(content_base64, headers)
        if token:
            response.set_cookie('fileToken', token)
        return response