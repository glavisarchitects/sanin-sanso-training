from odoo import _, fields, models
from odoo.exceptions import UserError


class Import(models.TransientModel):
    _inherit = "base_import.import"
    _description = "Base Import"

    def transform_autogas_file(self, options, **kwargs):
        self.ensure_one()
        if self.file_type != "text/csv":
            raise UserError(_("Autogas File Transform only takes `.csv` as file extension!"))
        autogas_header = self.env["ss_erp.ifdb.autogas.file.header"].create({
            "name": self.file_name,
            "upload_date": fields.Datetime.now(),
            "user_id": self.env.user.id,
            "branch_id": self.env.user.organization_id.id
        })
        data = self.file.decode("utf-8").split("\r\n")
        # remove the first and last line
        data = data[1:-2]
        new_data = [
            '"card_classification","processing_division","unused","group_division","actual_car_number","card_number","product_code","data_no","quantity_1","unit_price","amount_of_money","staff_code","processing_time","quantity_2","autogas_file_header_id"'
        ]
        for line in data:
            line_data, quantity_2 = line.split()
            card_classification = line_data[0]
            processing_division = line_data[1:3]
            unused = line_data[3:5]
            group_division = line_data[5:6]
            actual_car_number = line_data[6:10]
            card_number = line_data[10:25]
            product_code = line_data[25:30]
            data_no = line_data[30:34]
            quantity_1 = line_data[34:40]
            unit_price = line_data[40:48]
            amount_of_money = line_data[48:55]
            staff_code = line_data[55:57]
            processing_time = line_data[57:63]
            new_line_data = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
                card_classification,
                processing_division,
                unused,
                group_division,
                actual_car_number,
                card_number,
                product_code,
                data_no,
                quantity_1,
                unit_price,
                amount_of_money,
                staff_code,
                processing_time,
                quantity_2,
                autogas_header.name,
            )
            new_data.append(new_line_data)
        self.file = "\n".join(new_data).encode("utf-8")
