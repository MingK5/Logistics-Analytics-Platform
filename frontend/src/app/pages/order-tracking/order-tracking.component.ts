import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-order-tracking',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
  <div class="container">
    <h1>Employee Order Tracking</h1>
    <div class="card">
      <input [(ngModel)]="orderId" placeholder="Paste order_id" />
      <button (click)="search()">Search</button>
    </div>
    <div class="card" *ngIf="selected">
      <h2>{{selected.order.order_id}}</h2>
      <p>Status: <strong>{{selected.order.status}}</strong></p>
      <p>Last Event: {{selected.order.last_event_time}}</p>
      <h3>Timeline</h3>
      <table>
        <tr><th>Time</th><th>Event</th></tr>
        <tr *ngFor="let e of selected.timeline.events">
          <td>{{e.event_time}}</td><td>{{e.event_type}}</td>
        </tr>
      </table>
    </div>
    <div class="card">
      <h2>Recent Orders</h2>
      <table>
        <tr><th>Order ID</th><th>Status</th><th>Last Event</th></tr>
        <tr *ngFor="let o of orders" (click)="orderId=o.order_id; search()">
          <td>{{o.order_id}}</td><td>{{o.status}}</td><td>{{o.last_event_time}}</td>
        </tr>
      </table>
    </div>
  </div>`
})
export class OrderTrackingComponent implements OnInit {
  orderId = '';
  orders: any[] = [];
  selected: any;
  constructor(private api: ApiService) {}
  ngOnInit(): void { this.load(); setInterval(() => this.load(), 5000); }
  load(): void { this.api.getRecentOrders(40).subscribe(x => this.orders = x || []); }
  search(): void { if (this.orderId.trim()) this.api.getOrder(this.orderId.trim()).subscribe(x => this.selected = x); }
}
