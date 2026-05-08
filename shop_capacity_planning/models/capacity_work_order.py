from odoo import api, fields, models


class CapacityWorkOrder(models.Model):
    _name = 'capacity.work.order'
    _description = 'Capacity Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_scheduled, name'

    name = fields.Char(required=True, tracking=True)
    reference = fields.Char(string='Job Reference', tracking=True)
    workstation_id = fields.Many2one(
        'capacity.workstation',
        required=True,
        tracking=True,
        ondelete='restrict',
    )
    plan_id = fields.Many2one('capacity.plan', string='Capacity Plan', ondelete='set null')

    date_scheduled = fields.Date(required=True, default=fields.Date.today, tracking=True)
    date_completed = fields.Date(tracking=True)

    estimated_hours = fields.Float(string='Estimated Hours', required=True, tracking=True)
    actual_hours = fields.Float(string='Actual Hours', tracking=True)

    priority = fields.Selection(
        [('0', 'Normal'), ('1', 'High'), ('2', 'Very High'), ('3', 'Critical')],
        default='0',
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('scheduled', 'Scheduled'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        default='draft',
        required=True,
        tracking=True,
    )

    efficiency = fields.Float(
        compute='_compute_efficiency',
        string='Efficiency (%)',
        store=True,
        help='Estimated hours / Actual hours x 100',
    )
    notes = fields.Text()
    color = fields.Integer(compute='_compute_color')

    @api.depends('estimated_hours', 'actual_hours')
    def _compute_efficiency(self):
        for rec in self:
            if rec.actual_hours > 0:
                rec.efficiency = (rec.estimated_hours / rec.actual_hours) * 100
            else:
                rec.efficiency = 0.0

    @api.depends('state', 'priority')
    def _compute_color(self):
        state_color = {'draft': 0, 'scheduled': 4, 'in_progress': 2, 'done': 10, 'cancelled': 9}
        for rec in self:
            rec.color = state_color.get(rec.state, 0)

    def action_schedule(self):
        self.write({'state': 'scheduled'})

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_done(self):
        self.write({'state': 'done', 'date_completed': fields.Date.today()})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
