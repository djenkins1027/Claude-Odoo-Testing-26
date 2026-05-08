from odoo import api, fields, models


class CapacityPlan(models.Model):
    _name = 'capacity.plan'
    _description = 'Capacity Plan'
    _inherit = ['mail.thread']
    _order = 'date_start desc'

    name = fields.Char(required=True, tracking=True)
    date_start = fields.Date(required=True, tracking=True)
    date_end = fields.Date(required=True, tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('done', 'Done')],
        default='draft',
        required=True,
        tracking=True,
    )
    notes = fields.Text()

    line_ids = fields.One2many('capacity.plan.line', 'plan_id', string='Workstation Lines')
    work_order_ids = fields.One2many('capacity.work.order', 'plan_id', string='Work Orders')

    total_planned_hours = fields.Float(compute='_compute_totals', store=True)
    total_available_hours = fields.Float(compute='_compute_totals', store=True)
    overall_utilization = fields.Float(
        compute='_compute_totals',
        store=True,
        string='Overall Utilization (%)',
    )

    @api.depends('line_ids.planned_hours', 'line_ids.available_hours')
    def _compute_totals(self):
        for plan in self:
            planned = sum(plan.line_ids.mapped('planned_hours'))
            available = sum(plan.line_ids.mapped('available_hours'))
            plan.total_planned_hours = planned
            plan.total_available_hours = available
            plan.overall_utilization = (planned / available * 100) if available else 0.0

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._generate_lines()
        return record

    def _generate_lines(self):
        for plan in self:
            if not plan.line_ids:
                workstations = self.env['capacity.workstation'].search([('active', '=', True)])
                lines = []
                for ws in workstations:
                    days = (plan.date_end - plan.date_start).days + 1
                    working_days = min(days, ws.working_days_week)
                    lines.append({
                        'plan_id': plan.id,
                        'workstation_id': ws.id,
                        'available_hours': ws.available_hours_day * working_days,
                    })
                self.env['capacity.plan.line'].create(lines)


class CapacityPlanLine(models.Model):
    _name = 'capacity.plan.line'
    _description = 'Capacity Plan Line'
    _order = 'workstation_id'

    plan_id = fields.Many2one('capacity.plan', required=True, ondelete='cascade')
    workstation_id = fields.Many2one('capacity.workstation', required=True, ondelete='restrict')

    available_hours = fields.Float(string='Available Hours', required=True)
    planned_hours = fields.Float(
        string='Planned Hours',
        compute='_compute_planned_hours',
        store=True,
    )
    actual_hours = fields.Float(
        string='Actual Hours',
        compute='_compute_actual_hours',
        store=True,
    )

    utilization_rate = fields.Float(
        compute='_compute_utilization_rate',
        store=True,
        string='Utilization (%)',
    )
    efficiency = fields.Float(
        compute='_compute_efficiency',
        store=True,
        string='Efficiency (%)',
    )
    remaining_hours = fields.Float(compute='_compute_utilization_rate', store=True)
    over_capacity = fields.Boolean(compute='_compute_utilization_rate', store=True)

    notes = fields.Text()

    @api.depends(
        'plan_id.work_order_ids.estimated_hours',
        'plan_id.work_order_ids.workstation_id',
        'plan_id.work_order_ids.state',
    )
    def _compute_planned_hours(self):
        for line in self:
            orders = line.plan_id.work_order_ids.filtered(
                lambda o: o.workstation_id == line.workstation_id
                and o.state != 'cancelled'
            )
            line.planned_hours = sum(orders.mapped('estimated_hours'))

    @api.depends(
        'plan_id.work_order_ids.actual_hours',
        'plan_id.work_order_ids.workstation_id',
        'plan_id.work_order_ids.state',
    )
    def _compute_actual_hours(self):
        for line in self:
            orders = line.plan_id.work_order_ids.filtered(
                lambda o: o.workstation_id == line.workstation_id
                and o.state == 'done'
            )
            line.actual_hours = sum(orders.mapped('actual_hours'))

    @api.depends('planned_hours', 'available_hours')
    def _compute_utilization_rate(self):
        for line in self:
            if line.available_hours:
                line.utilization_rate = (line.planned_hours / line.available_hours) * 100
            else:
                line.utilization_rate = 0.0
            line.remaining_hours = line.available_hours - line.planned_hours
            line.over_capacity = line.planned_hours > line.available_hours

    @api.depends('planned_hours', 'actual_hours')
    def _compute_efficiency(self):
        for line in self:
            if line.actual_hours > 0:
                line.efficiency = (line.planned_hours / line.actual_hours) * 100
            else:
                line.efficiency = 0.0
