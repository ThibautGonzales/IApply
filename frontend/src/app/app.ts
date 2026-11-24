import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { I18nService } from './core/i18n/i18n.service';
import { Health, HealthService } from './health.service';
import { Jobs } from './jobs/jobs';

@Component({
  imports: [RouterOutlet, Jobs],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App implements OnInit {
  private readonly healthService = inject(HealthService);
  protected readonly i18n = inject(I18nService);

  // Raw state only: the template turns it into text, so it follows language changes.
  protected readonly health = signal<Health | null>(null);
  protected readonly unreachable = signal(false);

  ngOnInit(): void {
    this.healthService.getHealth().subscribe({
      next: (health) => this.health.set(health),
      error: () => this.unreachable.set(true),
    });
  }
}
