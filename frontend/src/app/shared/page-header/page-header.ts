import { Component, inject, input } from '@angular/core';
import { I18nService } from '../../core/i18n/i18n.service';

/**
 * Header shared by every page: "Personal space / 01", a short tagline, the page title and,
 * on the right, whatever the page puts inside (its main buttons).
 */
@Component({
  selector: 'app-page-header',
  styleUrl: './page-header.css',
  templateUrl: './page-header.html',
})
export class PageHeader {
  protected readonly i18n = inject(I18nService);

  readonly number = input.required<string>();
  readonly tagline = input.required<string>();
  readonly heading = input.required<string>();
  readonly subtitle = input('');
}
