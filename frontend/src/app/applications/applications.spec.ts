import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Applications } from './applications';
import { Application } from './applications.service';

const application: Application = {
  id: 1,
  status: 'waiting',
  applied_at: '2026-11-20T09:00:00Z',
  last_news_at: '2026-11-20T09:00:00Z',
  job: {
    id: 7,
    source: 'jooble',
    external_id: '42',
    title: 'Full stack developer',
    company: 'ACME',
    location: 'Clermont-Ferrand',
    salary: null,
    contract_type: 'CDI',
    description: 'Angular and Python.',
    url: 'https://fr.jooble.org/desc/42',
    remote: false,
    published_at: '2026-11-19T09:00:00Z',
    collected_at: '2026-11-19T10:00:00Z',
  },
};

describe('Applications', () => {
  let httpTesting: HttpTestingController;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [Applications],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpTesting = TestBed.inject(HttpTestingController);
  });

  async function render(applications: Application[]) {
    const fixture = TestBed.createComponent(Applications);
    fixture.detectChanges();
    httpTesting.expectOne('/api/applications').flush(applications);
    await fixture.whenStable();
    return { fixture, compiled: fixture.nativeElement as HTMLElement };
  }

  it('lists the applications with their status, last news and a link to the posting', async () => {
    const { compiled } = await render([application]);

    const link = compiled.querySelector('tbody a');
    expect(link?.textContent?.trim()).toBe('Full stack developer');
    expect(link?.getAttribute('href')).toBe('https://fr.jooble.org/desc/42');
    expect(compiled.querySelector('select')?.value).toBe('waiting');
    expect(compiled.querySelector('tbody td:nth-child(5)')?.textContent).toBe('20/11/2026');
  });

  it('changes the status and shows the updated application', async () => {
    const { fixture, compiled } = await render([application]);

    const select = compiled.querySelector('select')!;
    select.value = 'interview';
    select.dispatchEvent(new Event('change'));
    const request = httpTesting.expectOne({ method: 'PUT', url: '/api/applications/1/status' });
    expect(request.request.body).toEqual({ status: 'interview' });
    request.flush({ ...application, status: 'interview', last_news_at: '2026-11-25T09:00:00Z' });
    await fixture.whenStable();

    expect(compiled.querySelector('tbody td:nth-child(5)')?.textContent).toBe('25/11/2026');
  });

  it('records news and updates the last news date', async () => {
    const { fixture, compiled } = await render([application]);

    compiled.querySelector<HTMLButtonElement>('.news')?.click();
    httpTesting
      .expectOne({ method: 'POST', url: '/api/applications/1/news' })
      .flush({ ...application, last_news_at: '2026-11-25T09:00:00Z' });
    await fixture.whenStable();

    expect(compiled.querySelector('tbody td:nth-child(5)')?.textContent).toBe('25/11/2026');
  });

  it('shows and closes the offer details', async () => {
    const { fixture, compiled } = await render([application]);

    compiled.querySelector<HTMLButtonElement>('.view')?.click();
    await fixture.whenStable();
    expect(compiled.querySelector('.offer .description')?.textContent?.trim()).toBe(
      'Angular and Python.',
    );
    expect(compiled.querySelector('.offer a')?.getAttribute('href')).toBe(
      'https://fr.jooble.org/desc/42',
    );

    compiled.querySelector<HTMLButtonElement>('.view')?.click();
    await fixture.whenStable();
    expect(compiled.querySelector('.offer')).toBeNull();
  });

  it('saves a pasted offer text and shows it', async () => {
    const { fixture, compiled } = await render([application]);
    compiled.querySelector<HTMLButtonElement>('.view')?.click();
    await fixture.whenStable();

    compiled.querySelector<HTMLButtonElement>('.offer .edit')?.click();
    await fixture.whenStable();
    compiled.querySelector('textarea')!.value = 'The full offer.';
    compiled.querySelector<HTMLButtonElement>('.offer .save')?.click();
    const request = httpTesting.expectOne({ method: 'PUT', url: '/api/jobs/7/description' });
    expect(request.request.body).toEqual({ description: 'The full offer.' });
    request.flush({ ...application.job, description: 'The full offer.' });
    await fixture.whenStable();

    expect(compiled.querySelector('textarea')).toBeNull();
    expect(compiled.querySelector('.offer .description')?.textContent?.trim()).toBe(
      'The full offer.',
    );
  });

  it('says when there is no application yet', async () => {
    const { compiled } = await render([]);
    expect(compiled.textContent).toContain('No applications yet.');
  });
});
