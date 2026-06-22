import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-live-events',
  standalone: true,
  imports: [CommonModule],
  template: `
  <div class="container">
    <h1>Live Event Feed</h1>
    <div class="card">
      <table>
        <tr><th>Event Time</th><th>Type</th><th>Order ID</th></tr>
        <tr *ngFor="let e of events">
          <td>{{e.event_time}}</td><td><span class="badge">{{e.event_type}}</span></td><td>{{e.order_id}}</td>
        </tr>
      </table>
    </div>
  </div>`
})
export class LiveEventsComponent implements OnInit {
  events: any[] = [];
  constructor(private api: ApiService) {}
  ngOnInit(): void { this.load(); setInterval(() => this.load(), 2000); }
  load(): void { this.api.getLiveEvents(80).subscribe(x => this.events = x || []); }
}
