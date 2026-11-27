import { Component, computed, inject, input } from '@angular/core';
import { I18nService } from '../../core/i18n/i18n.service';
import { JobOffer } from '../../jobs/jobs.service';

/** From this score on, an offer matches the profile (the same limit as the profile page help). */
const GOOD_SCORE = 50;

/** The score of an offer in a coloured square: a pencil if added by hand, a dash if not scored yet. */
@Component({
  selector: 'app-score-badge',
  template: `
    @switch (kind()) {
      @case ('manual') {
        <span class="score-badge manual" [title]="i18n.t('table.manual')">✎</span>
      }
      @case ('none') {
        <span class="score-badge none" [title]="i18n.t('table.notScored')">–</span>
      }
      @default {
        <span class="score-badge" [class]="kind()">{{ job().score }}</span>
      }
    }
  `,
})
export class ScoreBadge {
  protected readonly i18n = inject(I18nService);

  readonly job = input.required<JobOffer>();

  protected readonly kind = computed(() => {
    const job = this.job();
    if (job.source === 'manual') {
      return 'manual';
    }
    if (job.score === null) {
      return 'none';
    }
    return job.score >= GOOD_SCORE ? 'good' : 'low';
  });
}
