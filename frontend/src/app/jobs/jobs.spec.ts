import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Jobs } from './jobs';
import { JobOffer } from './jobs.service';

const offer: JobOffer = {
  id: 1,
  source: 'jooble',
  external_id: '42',
  title: 'Full stack developer',
  company: 'ACME',
  location: 'Clermont-Ferrand',
  salary: null,
  contract_type: 'CDI',
  description: null,
  url: 'https://fr.jooble.org/desc/42',
  remote: false,
  score: 72,
  published_at: '2026-11-23T09:00:00Z',
  collected_at: '2026-11-24T09:00:00Z',
};

describe('Jobs', () => {
  let httpTesting: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Jobs],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpTesting = TestBed.inject(HttpTestingController);
  });

  it('lists the saved offers with a link to each posting', async () => {
    const fixture = TestBed.createComponent(Jobs);
    fixture.detectChanges();

    httpTesting.expectOne('/api/jobs').flush([offer]);
    await fixture.whenStable();

    const link = (fixture.nativeElement as HTMLElement).querySelector('.on-site tbody a');
    expect(link?.textContent).toBe('Full stack developer');
    expect(link?.getAttribute('href')).toBe('https://fr.jooble.org/desc/42');
  });

  it('collects, shows the summary and reloads the list', async () => {
    const fixture = TestBed.createComponent(Jobs);
    fixture.detectChanges();
    httpTesting.expectOne('/api/jobs').flush([]);

    (fixture.nativeElement as HTMLElement).querySelector('button')?.click();
    httpTesting
      .expectOne({ method: 'POST', url: '/api/jobs/collect' })
      .flush({ fetched: 3, added: 1, errors: [], scored: 1, scoring_error: null });
    httpTesting.expectOne('/api/jobs').flush([offer]);
    await fixture.whenStable();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.message')?.textContent).toBe(
      '1 new offers (3 found). 1 offers scored.',
    );
    expect(compiled.querySelectorAll('tbody tr').length).toBe(1);
  });

  it('hides an offer and removes it from the list', async () => {
    const fixture = TestBed.createComponent(Jobs);
    fixture.detectChanges();
    httpTesting.expectOne('/api/jobs').flush([offer]);
    await fixture.whenStable();

    const compiled = fixture.nativeElement as HTMLElement;
    compiled.querySelector<HTMLButtonElement>('tbody .hide')?.click();
    httpTesting.expectOne({ method: 'POST', url: '/api/jobs/1/hide' }).flush(null);
    await fixture.whenStable();

    expect(compiled.querySelectorAll('tbody tr').length).toBe(0);
  });

  it('marks an offer as applied and removes it from the list', async () => {
    const fixture = TestBed.createComponent(Jobs);
    fixture.detectChanges();
    httpTesting.expectOne('/api/jobs').flush([offer]);
    await fixture.whenStable();

    const compiled = fixture.nativeElement as HTMLElement;
    compiled.querySelector<HTMLButtonElement>('tbody .apply')?.click();
    httpTesting
      .expectOne({ method: 'POST', url: '/api/jobs/1/apply' })
      .flush({ id: 1, job_offer_id: 1, status: 'waiting' });
    await fixture.whenStable();

    expect(compiled.querySelectorAll('tbody tr').length).toBe(0);
  });

  it('shows remote offers in their own table', async () => {
    const fixture = TestBed.createComponent(Jobs);
    fixture.detectChanges();

    httpTesting
      .expectOne('/api/jobs')
      .flush([offer, { ...offer, id: 2, external_id: '43', remote: true }]);
    await fixture.whenStable();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelectorAll('.on-site tbody tr').length).toBe(1);
    expect(compiled.querySelectorAll('.remote tbody tr').length).toBe(1);
  });

  it('pastes the full text of an offer before applying', async () => {
    const fixture = TestBed.createComponent(Jobs);
    fixture.detectChanges();
    httpTesting.expectOne('/api/jobs').flush([offer]);
    await fixture.whenStable();

    const compiled = fixture.nativeElement as HTMLElement;
    compiled.querySelector<HTMLButtonElement>('tbody .view')?.click();
    await fixture.whenStable();
    expect(compiled.querySelector('.offer .description')?.textContent).toContain(
      'No description yet',
    );
    expect(compiled.querySelector('.offer .edit')?.textContent?.trim()).toBe('Paste the offer');

    compiled.querySelector<HTMLButtonElement>('.offer .edit')?.click();
    await fixture.whenStable();
    compiled.querySelector('textarea')!.value = 'The full offer.';
    compiled.querySelector<HTMLButtonElement>('.offer .save')?.click();
    httpTesting
      .expectOne({ method: 'PUT', url: '/api/jobs/1/description' })
      .flush({ ...offer, description: 'The full offer.' });
    await fixture.whenStable();

    expect(compiled.querySelector('.offer .description')?.textContent?.trim()).toBe(
      'The full offer.',
    );
    expect(compiled.querySelector('.offer .edit')?.textContent?.trim()).toBe('Edit the offer');
  });

  it('cancels the edit without calling the API', async () => {
    const fixture = TestBed.createComponent(Jobs);
    fixture.detectChanges();
    httpTesting.expectOne('/api/jobs').flush([offer]);
    await fixture.whenStable();

    const compiled = fixture.nativeElement as HTMLElement;
    compiled.querySelector<HTMLButtonElement>('tbody .view')?.click();
    await fixture.whenStable();
    compiled.querySelector<HTMLButtonElement>('.offer .edit')?.click();
    await fixture.whenStable();
    compiled.querySelector<HTMLButtonElement>('.offer .cancel')?.click();
    await fixture.whenStable();

    expect(compiled.querySelector('textarea')).toBeNull();
    httpTesting.verify();
  });

  it('shows the score of each offer, or a dash when it is not scored yet', async () => {
    const fixture = TestBed.createComponent(Jobs);
    fixture.detectChanges();

    httpTesting.expectOne('/api/jobs').flush([offer, { ...offer, id: 2, score: null }]);
    await fixture.whenStable();

    const scores = (fixture.nativeElement as HTMLElement).querySelectorAll('td.score');
    expect([...scores].map((cell) => cell.textContent?.trim())).toEqual(['72', '–']);
  });

  it('says why the offers were not scored', async () => {
    const fixture = TestBed.createComponent(Jobs);
    fixture.detectChanges();
    httpTesting.expectOne('/api/jobs').flush([]);

    (fixture.nativeElement as HTMLElement).querySelector('button')?.click();
    httpTesting.expectOne({ method: 'POST', url: '/api/jobs/collect' }).flush({
      fetched: 1,
      added: 1,
      errors: [],
      scored: 0,
      scoring_error: 'Choose a provider and save an API key on the LLM page.',
    });
    httpTesting.expectOne('/api/jobs').flush([offer]);
    await fixture.whenStable();

    expect((fixture.nativeElement as HTMLElement).querySelector('.message')?.textContent).toBe(
      '1 new offers (1 found). Offers not scored: Choose a provider and save an API key on the LLM page.',
    );
  });
});
