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
      .flush({ fetched: 3, added: 1, errors: [] });
    httpTesting.expectOne('/api/jobs').flush([offer]);
    await fixture.whenStable();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.message')?.textContent).toBe('1 new offers (3 found).');
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
});
