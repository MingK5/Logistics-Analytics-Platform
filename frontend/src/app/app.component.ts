import { Component } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink],
  template: `
    <nav class="nav">
      <strong>Logistics Analytics</strong>
      <a routerLink="/dashboard">Manager Dashboard</a>
      <a routerLink="/live-events">Live Events</a>
      <a routerLink="/orders">Order Tracking</a>
      <a routerLink="/sellers">Seller Performance</a>
    </nav>
    <router-outlet></router-outlet>
  `,
  styles: [`
    .nav { height: 58px; display: flex; align-items: center; gap: 24px; padding: 0 24px; background: #111827; color: white; }
    .nav a { opacity: .9; }
    .nav a:hover { opacity: 1; text-decoration: underline; }
  `]
})
export class AppComponent {}
