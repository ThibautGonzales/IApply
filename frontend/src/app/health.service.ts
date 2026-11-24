import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface Health {
  status: string;
  database: string;
}

/** Talks to the backend `/health` route. */
@Injectable({ providedIn: 'root' })
export class HealthService {
  private readonly http = inject(HttpClient);

  // `/api` is forwarded to the backend by the dev proxy (proxy.conf.json) and by nginx in Docker.
  getHealth(): Observable<Health> {
    return this.http.get<Health>('/api/health');
  }
}
