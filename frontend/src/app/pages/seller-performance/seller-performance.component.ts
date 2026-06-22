import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-seller-performance',
  standalone: true,
  imports: [CommonModule],
  template: `
  <div class="container">
    <h1>Seller Performance</h1>
    <div class="card">
      <p>Run the Spark job to populate this table.</p>
      <table>
        <tr><th>Seller ID</th><th>Delivered</th><th>Late</th><th>Avg Delivery Days</th></tr>
        <tr *ngFor="let s of sellers">
          <td>{{s.seller_id}}</td><td>{{s.delivered_orders}}</td><td>{{s.late_deliveries}}</td><td>{{s.avg_delivery_days | number:'1.1-1'}}</td>
        </tr>
      </table>
    </div>
  </div>`
})
export class SellerPerformanceComponent implements OnInit {
  sellers: any[] = [];
  constructor(private api: ApiService) {}
  ngOnInit(): void { this.api.getSellers(50).subscribe(x => this.sellers = x || []); }
}
