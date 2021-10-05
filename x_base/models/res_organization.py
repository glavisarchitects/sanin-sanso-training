# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class ResOrganization(models.Model):
    _inherit = "x.x_company_organization.res_org"

    @api.model
    def _get_default_address_format(self):
        return "%(street)s\n%(street2)s\n%(city)s %(state_name)s %(zip)s\n\
        %(country_name)s"

    def _display_address(self, without_company=False):

        address_format = self._get_default_address_format()
        args = {
            'street': self.street or '',
            'street2': self.street2 or '',
            'city': self.city or '',
            'zip': self.zip or '',
            'state_code': self.state_id.code or '',
            'state_name': self.state_id.name or '',
            'country_code': self.country_id.code or '',
            'country_name': self.country_id.name or '',
        }

        address_format = '' + address_format
        return address_format % args
