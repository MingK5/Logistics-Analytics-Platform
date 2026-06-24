import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
  <div class="container">
    <h1>Overview Dashboard</h1>
    <div class="grid" *ngIf="summary">
      <div class="card"><h3>Total Orders</h3><h2>{{summary.total_orders || 0}}</h2></div>
      <div class="card"><h3>Delivered</h3><h2>{{summary.delivered_orders || 0}}</h2></div>
      <div class="card"><h3>Late Deliveries</h3><h2>{{summary.late_deliveries || 0}}</h2></div>
      <div class="card"><h3>Avg Delivery Days</h3><h2>{{summary.avg_delivery_days | number:'1.1-1'}}</h2></div>
    </div>
    <div class="card">
      <h2>Daily KPI</h2>
      <table>
        <tr><th>Date</th><th>Orders Created</th><th>Orders Delivered</th><th>Late</th></tr>
        <tr *ngFor="let r of daily">
          <td>{{r.event_date}}</td><td>{{r.orders_created}}</td><td>{{r.orders_delivered}}</td><td>{{r.late_deliveries}}</td>
        </tr>
      </table>
    </div>
  </div>`
})
export class DashboardComponent implements OnInit {
  summary: any;
  daily: any[] = [];
  constructor(private api: ApiService) {}
  ngOnInit(): void {
    this.load();
    setInterval(() => this.load(), 5000);
  }
  load(): void {
    this.api.getSummary().subscribe(x => this.summary = x || {});
    this.api.getDailyKpi().subscribe(x => this.daily = x || []);
  }
}
