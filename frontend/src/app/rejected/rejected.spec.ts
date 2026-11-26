import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { JobOffer } from '../jobs/jobs.service';
import { Rejected } from './rejected';

const lowScore: JobOffer = {
  id: 1,
  source: 'jooble',
  external_id: '42',
  title: 'Java developer',
  company: 'ACME',
  location: 'Lyon',
  salary: null,
  contract_type: 'CDI',
  description: null,
  url: 'https://fr.jooble.org/desc/42',
  remote: false,
  hidden: false,
  restored: false,
  score: 20,
  published_at: '2026-11-23T09:00:00Z',
  collected_at: '2026-11-24T09:00:00Z',
};
const hidden: JobOffer = { ...lowScore, id: 2, external_id: '43', score: 80, hidden: true };

describe('Rejected', () => {
  let httpTesting: HttpTestingController;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [Rejected],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpTesting = TestBed.inject(HttpTestingController);
  });

  async function render(jobs: JobOffer[]) {
    const fixture = TestBed.createComponent(Rejected);
    fixture.detectChanges();
    httpTesting.expectOne('/api/jobs/rejected').flush(jobs);
    await fixture.whenStable();
    return { fixture, compiled: fixture.nativeElement as HTMLElement };
  }

  it('lists the rejected offers with the reason', async () => {
    const { compiled } = await render([hidden, lowScore]);

    const reasons = [...compiled.querySelectorAll('.reason')].map((cell) =>
      cell.textContent?.trim(),
    );
    expect(reasons).toEqual(['Hidden', 'Score too low']);
    expect(compiled.querySelector('tbody a')?.getAttribute('href')).toBe(
      'https://fr.jooble.org/desc/42',
    );
  });

  it('restores an offer and removes it from the page', async () => {
    const { fixture, compiled } = await render([lowScore]);

    compiled.querySelector<HTMLButtonElement>('.restore')?.click();
    httpTesting.expectOne({ method: 'POST', url: '/api/jobs/1/restore' }).flush(null);
    await fixture.whenStable();

    expect(compiled.textContent).toContain('No rejected offers in the last 7 days.');
  });
});
