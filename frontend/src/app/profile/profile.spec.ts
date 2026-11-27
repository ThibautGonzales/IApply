import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Profile } from './profile';
import { JoobleSearch, UserProfile } from './profile.service';

const profile: UserProfile = {
  looking_for: 'Python backend developer, Clermont-Ferrand or remote',
  background: '5 years of Python at Michelin',
  min_score_onsite: 50,
  min_score_remote: 70,
  updated_at: '2026-11-26T13:00:00Z',
};

const searches: JoobleSearch[] = [
  {
    id: 1,
    keywords: 'développeur Python',
    remote: false,
    location: 'Clermont-Ferrand',
    radius_km: 40,
  },
  { id: 2, keywords: 'développeur Python', remote: true, location: null, radius_km: null },
];

describe('Profile', () => {
  let httpTesting: HttpTestingController;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [Profile],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpTesting = TestBed.inject(HttpTestingController);
  });

  async function render(saved: UserProfile, savedSearches: JoobleSearch[] = searches) {
    const fixture = TestBed.createComponent(Profile);
    fixture.detectChanges();
    httpTesting.expectOne('/api/profile').flush(saved);
    httpTesting.expectOne('/api/profile/searches').flush(savedSearches);
    await fixture.whenStable();
    return { fixture, compiled: fixture.nativeElement as HTMLElement };
  }

  it('shows the saved profile in the text box', async () => {
    const { compiled } = await render(profile);

    expect(compiled.querySelector<HTMLTextAreaElement>('.looking-for')?.value).toBe(
      profile.looking_for,
    );
    expect(compiled.querySelector<HTMLTextAreaElement>('.background')?.value).toBe(
      profile.background,
    );
    expect(compiled.querySelector<HTMLInputElement>('.onsite')?.value).toBe('50');
    expect(compiled.querySelector<HTMLInputElement>('.remote')?.value).toBe('70');
  });

  it('saves the text and confirms it', async () => {
    const { fixture, compiled } = await render({ ...profile, looking_for: '', background: '' });

    compiled.querySelector<HTMLTextAreaElement>('.looking-for')!.value = 'AI developer, remote';
    compiled.querySelector<HTMLTextAreaElement>('.background')!.value = '3 years of Angular';
    compiled.querySelector<HTMLInputElement>('.onsite')!.value = '65';
    compiled.querySelector<HTMLInputElement>('.remote')!.value = '80';
    compiled.querySelector('button')!.click();
    const request = httpTesting.expectOne('/api/profile');
    expect(request.request.method).toBe('PUT');
    expect(request.request.body).toEqual({
      looking_for: 'AI developer, remote',
      background: '3 years of Angular',
      min_score_onsite: 65,
      min_score_remote: 80,
    });
    request.flush({
      ...profile,
      looking_for: 'AI developer, remote',
      background: '3 years of Angular',
      min_score_onsite: 65,
      min_score_remote: 80,
    });
    httpTesting.expectOne('/api/profile/searches').flush(searches);
    fixture.detectChanges();
    await fixture.whenStable();

    expect(compiled.querySelector('.saved')?.textContent).toContain('Saved');
    expect(compiled.querySelectorAll('.searches li').length).toBe(2);
  });

  it('lists the searches worked out from the profile', async () => {
    const { compiled } = await render(profile);

    const items = compiled.querySelectorAll('.searches li');
    expect(items[0].textContent).toContain('développeur Python');
    expect(items[0].textContent).toContain('Clermont-Ferrand');
    expect(items[0].textContent).toContain('40 km');
    expect(items[1].textContent).toContain('full remote');
  });

  it('says when there is no search yet', async () => {
    const { compiled } = await render(profile, []);

    expect(compiled.querySelector('.no-searches')).not.toBeNull();
  });

  it('shows why the profile was not saved', async () => {
    const { fixture, compiled } = await render(profile);

    compiled.querySelector('button')!.click();
    httpTesting
      .expectOne('/api/profile')
      .flush(
        {
          detail:
            'Could not work out the Jooble searches, the profile was not saved: quota reached',
        },
        { status: 400, statusText: 'Bad Request' },
      );
    fixture.detectChanges();
    await fixture.whenStable();

    expect(compiled.querySelector('.error')?.textContent).toContain('quota reached');
    expect(compiled.querySelector('.saved')).toBeNull();
  });
});
