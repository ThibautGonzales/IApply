import { Component, OnInit, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter, map } from 'rxjs';
import { I18nService } from './core/i18n/i18n.service';
import { TranslationKey } from './core/i18n/translations';
import { Health, HealthService } from './health.service';
import { JobsService } from './jobs/jobs.service';

/** A link of the side menu. */
interface MenuItem {
  path: string;
  label: TranslationKey;
}

/** The app layout: side menu, top bar (current page, backend status, language) and the page. */
@Component({
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App implements OnInit {
  private readonly healthService = inject(HealthService);
  private readonly router = inject(Router);
  protected readonly i18n = inject(I18nService);
  // Number of offers shown next to "Offers" in the menu, once the offers page has loaded them.
  protected readonly offerCount = inject(JobsService).count;

  protected readonly menu: MenuItem[] = [
    { path: '/', label: 'nav.jobs' },
    { path: '/rejected', label: 'nav.rejected' },
    { path: '/applications', label: 'nav.applications' },
    { path: '/profile', label: 'nav.profile' },
    { path: '/letter-examples', label: 'nav.letterExamples' },
    { path: '/llm', label: 'nav.llm' },
  ];

  // Raw state only: the template turns it into text, so it follows language changes.
  protected readonly health = signal<Health | null>(null);
  protected readonly unreachable = signal(false);

  // The `label` of the current route (see app.routes.ts), updated after each navigation.
  protected readonly pageLabel = toSignal(
    this.router.events.pipe(
      filter((event) => event instanceof NavigationEnd),
      map(() => this.currentLabel()),
    ),
    { initialValue: null },
  );

  ngOnInit(): void {
    this.healthService.getHealth().subscribe({
      next: (health) => this.health.set(health),
      error: () => this.unreachable.set(true),
    });
  }

  private currentLabel(): TranslationKey | null {
    let route = this.router.routerState.snapshot.root;
    while (route.firstChild) {
      route = route.firstChild;
    }
    return route.data['label'] ?? null;
  }
}
