import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = environment.apiUrl;
  constructor(private http: HttpClient) {}

  getSummary(): Observable<any> { return this.http.get(`${this.base}/kpis/summary`); }
  getDailyKpi(): Observable<any[]> { return this.http.get<any[]>(`${this.base}/kpis/daily`); }
  getLiveEvents(limit = 50): Observable<any[]> { return this.http.get<any[]>(`${this.base}/events/live?limit=${limit}`); }
  getRecentOrders(limit = 50): Observable<any[]> { return this.http.get<any[]>(`${this.base}/orders/recent?limit=${limit}`); }
  getOrder(orderId: string): Observable<any> { return this.http.get(`${this.base}/orders/${orderId}`); }
  getSellers(limit = 20): Observable<any[]> { return this.http.get<any[]>(`${this.base}/analytics/sellers?limit=${limit}`); }
}
