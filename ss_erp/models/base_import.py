from odoo import _, fields, models
from odoo.exceptions import UserError


class Import(models.TransientModel):
    _inherit = "base_import.import"
    _description = "Base Import"

    import_file_header_model = fields.Char(
        string="Related File Header Model",
        readonly=True,
        index=True
    )
    import_file_header_id = fields.Many2oneReference(
        string="Related File Header Id",
        readonly=True,
        index=True,
        model_field="import_file_header_model"
    )

    def transform_autogas_file(self, options, parent_context={}):
        self.ensure_one()
        autogas_header = False
        if parent_context and not any([self.import_file_header_id, self.import_file_header_model]):
            self.import_file_header_model = parent_context["default_import_file_header_model"]
            self.import_file_header_id = parent_context["default_import_file_header_id"]
            autogas_header = self.env[self.import_file_header_model].browse(
                self.import_file_header_id
            )
        if not autogas_header:
            raise UserError(_("Missing File Header, please using `upload` option from file header!"))
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

    def transform_powernet_file(self, options, parent_context={}):
        self.ensure_one()
        powernet_header = False
        if parent_context and not any([self.import_file_header_id, self.import_file_header_model]):
            self.import_file_header_model = parent_context["default_import_file_header_model"]
            self.import_file_header_id = parent_context["default_import_file_header_id"]
            powernet_header = self.env[self.import_file_header_model].browse(
                self.import_file_header_id
            )
        if not powernet_header:
            raise UserError(_("Missing File Header, please using `upload` option from file header!"))
        data = self.file.split(b"\n")
        new_data = [
            b'"powernet_sales_header_id","customer_code","billing_summary_code","sales_date","slip_type","slip_no","data_types","cash_classification","product_code","product_code_2","product_name","product_remarks","sales_category","quantity","unit_code","unit_price","amount_of_money","consumption_tax","sales_amount","quantity_after_conversion","search_remarks_1","search_remarks_2","search_remarks_3","search_remarks_4","search_remarks_5","search_remarks_6","search_remarks_7","search_remarks_8","search_remarks_9","search_remarks_10","sales_classification_code_1","sales_classification_code_2","sales_classification_code_3","consumer_sales_classification_code_1","consumer_sales_classification_code_2","consumer_sales_classification_code_3","consumer_sales_classification_code_4","consumer_sales_classification_code_5","product_classification_code_1","product_classification_code_2","product_classification_code_3"'
        ]
        for line in data:
            if line == b"":
                continue
            new_line = b'"%s",' % (powernet_header.name.encode("utf-8")) + line
            new_data.append(new_line)
        self.file = b"\n".join(new_data)
