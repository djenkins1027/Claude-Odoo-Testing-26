from odoo import api, fields, models


class CapacityWorkstation(models.Model):
    _name = 'capacity.workstation'
    _description = 'Shop Workstation'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    color = fields.Integer()

    machine_count = fields.Integer(string='Machines', default=1)
    operator_count = fields.Float(string='Operators', default=1.0)
    available_hours_day = fields.Float(
        string='Available Hours/Day',
        default=8.0,
        help='Total available production hours per day across all machines/operators',
    )
    working_days_week = fields.Integer(string='Working Days/Week', default=5)
    efficiency_target = fields.Float(
        string='Target Efficiency (%)',
        default=85.0,
        help='Target utilization percentage for this workstation',
    )

    notes = fields.Text()

    work_order_ids = fields.One2many('capacity.work.order', 'workstation_id', string='Work Orders')
    work_order_count = fields.Integer(compute='_compute_work_order_count')

    weekly_available_hours = fields.Float(
        compute='_compute_weekly_available_hours',
        string='Weekly Available Hours',
        store=True,
    )

    @api.depends('available_hours_day', 'working_days_week')
    def _compute_weekly_available_hours(self):
        for rec in self:
            rec.weekly_available_hours = rec.available_hours_day * rec.working_days_week

    def _compute_work_order_count(self):
        counts = self.env['capacity.work.order'].read_group(
            [('workstation_id', 'in', self.ids), ('state', '!=', 'cancelled')],
            ['workstation_id'],
            ['workstation_id'],
        )
        count_map = {r['workstation_id'][0]: r['workstation_id_count'] for r in counts}
        for rec in self:
            rec.work_order_count = count_map.get(rec.id, 0)

    def action_view_work_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'{self.name} – Work Orders',
            'res_model': 'capacity.work.order',
            'view_mode': 'list,kanban,form',
            'domain': [('workstation_id', '=', self.id)],
            'context': {'default_workstation_id': self.id},
        }
