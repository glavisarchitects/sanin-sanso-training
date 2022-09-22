# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import format_date

import re
from psycopg2 import sql


class SequenceMixin(models.AbstractModel):

    _inherit = 'sequence.mixin'

    def _constrains_date_sequence(self):
        # Make it possible to bypass the constraint to allow edition of already messed up documents.
        # /!\ Do not use this to completely disable the constraint as it will make this mixin unreliable.
        constraint_date = fields.Date.to_date(self.env['ir.config_parameter'].sudo().get_param(
            'sequence.mixin.constraint_start_date',
            '1970-01-01'
        ))
        for record in self:
            date = fields.Date.to_date(record[record._sequence_date_field])
            sequence = record[record._sequence_field]
            if sequence and date and date > constraint_date:
                format_values = record._get_sequence_format_param(sequence)[1]
                if (format_values['year'] and format_values['year'] != date.year % 10 ** len(
                        str(format_values['year']))):
                    raise ValidationError(_(
                        "The %(date_field)s (%(date)s) doesn't match the %(sequence_field)s (%(sequence)s).\n"
                        "You might want to clear the field %(sequence_field)s before proceeding with the change of the date.",
                        date=format_date(self.env, date),
                        sequence=sequence,
                        date_field=record._fields[record._sequence_date_field]._description_string(self.env),
                        sequence_field=record._fields[record._sequence_field]._description_string(self.env),
                    ))


    def _set_next_sequence(self):
        if self._context.get('pypass_confirm'):
            return super(SequenceMixin,self)._set_next_sequence()
        payment = self.env['account.move'].search([('move_type','=','entry')],order='id desc')

        if payment:
            highest_name = payment[1].name
            last_sequence = highest_name
            new = not last_sequence
            if new:
                last_sequence = highest_name
            format, format_values = self._get_sequence_format_param(last_sequence)
            if new:
                format_values['seq'] = 0
                format_values['year'] = self[self._sequence_date_field].year % (10 ** format_values['year_length'])
                format_values['month'] = self[self._sequence_date_field].month
            format_values['seq'] = format_values['seq'] + 1

        self[self._sequence_field] = format.format(**format_values)
        self._compute_split_sequence()


