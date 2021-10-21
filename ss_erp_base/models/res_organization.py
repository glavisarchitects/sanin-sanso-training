# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class Organization(models.Model):
    _inherit = "ss_erp.organization"

    @api.model
    def _get_default_address_format(self):
        return "%(state_name)s %(city)s %(zip)s %(street)s %(street2)s %(country_name)s"

    def _display_address(self, without_company=False):

        address_format = self._get_default_address_format()
        args = {
            'street': self.organization_street or '',
            'street2': self.organization_street2 or '',
            'city': self.organization_city or '',
            'zip': self.organization_zip or '',
            'state_code': self.organization_state_id and self.organization_state_id.code or '',
            'state_name': self.organization_state_id and self.organization_state_id.name or '',
            'country_code': self.organization_country_id and self.organization_country_id.code or '',
            'country_name': self.organization_country_id and self.organization_country_id.name or '',
        }

        address_format = '' + address_format
        return address_format % args
