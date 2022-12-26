# -*- coding: utf-8 -*-

from . import models


def post_init_hook(cr, registry):
    cr.execute(
                """
        ALTER TABLE
            ss_erp_res_partner_form
        DROP CONSTRAINT IF EXISTS 
            res_partner_bank_unique_number;
                """
            )