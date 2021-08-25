## Log

## tạo button
```xml

<xpath expr="//header" position="inside">
    <button type="action" name="request_rfq" string="Request" class="oe_highlight"/>
</xpath>
```

## Add fields to form view

```xml

<xpath expr="/form/sheet/notebook/page/field[@name='order_line']/tree/field[@name='x_campaign']" position="after">
    <field name="x_expected_delivery_date"/>
</xpath>
```

```xml

<xpath expr="//field[@name='validity_date']" position="before">
    <field name="x_sales_organization"/>
</xpath>
```

