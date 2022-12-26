# -*- coding: utf-8 -*-

from . import models
from odoo import api, fields, models, _
from odoo import SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    default_user = env.ref('base.default_user')

    # Remove from below group
    # default_user.write({'groups_id': [(3, env.ref('sales_team.group_sale_manager').id),
    #                                   (3, env.ref('sales_team.group_sale_salesman_all_leads').id),
    #                                   ]})

    # if this line doesn't work write like above
    default_user.groups_id = False
    # add default user to some group here
    default_user.write({'groups_id': [(4, env.ref('base.group_user').id),
                                      ]})

    default_user.groups_id._update_user_groups_view()
