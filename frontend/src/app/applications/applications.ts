import { Component, inject } from '@angular/core';
import { I18nService } from '../core/i18n/i18n.service';

/** Tracking page: the offers the user applied to, with their status. */
@Component({
  selector: 'app-applications',
  templateUrl: './applications.html',
})
export class Applications {
  protected readonly i18n = inject(I18nService);
}
