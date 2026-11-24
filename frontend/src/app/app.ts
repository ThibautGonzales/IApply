import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { HealthService } from './health.service';
import { Jobs } from './jobs/jobs';

@Component({
  imports: [RouterOutlet, Jobs],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App implements OnInit {
  private readonly healthService = inject(HealthService);

  protected readonly apiStatus = signal($localize`:@@backendStatusChecking:checking...`);

  ngOnInit(): void {
    this.healthService.getHealth().subscribe({
      next: (health) =>
        this.apiStatus.set(
          $localize`:@@backendStatusOk:API ${health.status}:apiStatus:, database ${health.database}:databaseStatus:`,
        ),
      error: () => this.apiStatus.set($localize`:@@backendStatusUnreachable:API unreachable`),
    });
  }
}
