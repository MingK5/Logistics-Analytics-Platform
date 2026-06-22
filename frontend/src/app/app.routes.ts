import { Routes } from '@angular/router';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { LiveEventsComponent } from './pages/live-events/live-events.component';
import { OrderTrackingComponent } from './pages/order-tracking/order-tracking.component';
import { SellerPerformanceComponent } from './pages/seller-performance/seller-performance.component';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'live-events', component: LiveEventsComponent },
  { path: 'orders', component: OrderTrackingComponent },
  { path: 'sellers', component: SellerPerformanceComponent },
];
