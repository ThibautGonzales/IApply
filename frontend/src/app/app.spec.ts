import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { App } from './app';
import { routes } from './app.routes';
import { I18nService } from './core/i18n/i18n.service';

describe('App', () => {
  let httpTesting: HttpTestingController;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter(routes)],
    }).compileComponents();
    httpTesting = TestBed.inject(HttpTestingController);
  });

  it('shows the backend status returned by /api/health', async () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();

    httpTesting.expectOne('/api/health').flush({ status: 'ok', database: 'ok' });
    await fixture.whenStable();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('strong')?.textContent?.trim()).toBe('API ok, database ok');
  });

  it('shows an error when the backend is unreachable', async () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();

    httpTesting.expectOne('/api/health').flush(null, { status: 503, statusText: 'Unavailable' });
    await fixture.whenStable();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('strong')?.textContent?.trim()).toBe('API unreachable');
  });

  it('translates the page when the language changes', async () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    httpTesting.expectOne('/api/health').flush(null, { status: 503, statusText: 'Unavailable' });
    await fixture.whenStable();

    TestBed.inject(I18nService).setLanguage('fr');
    await fixture.whenStable();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('strong')?.textContent?.trim()).toBe('API injoignable');
    expect(compiled.querySelector('nav a .label')?.textContent?.trim()).toBe("Offres d'emploi");
    expect(document.documentElement.lang).toBe('fr');
  });

  it('shows a menu with the offers, rejected offers, tracking, profile, letter examples and LLM pages', async () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    await fixture.whenStable();

    const links = (fixture.nativeElement as HTMLElement).querySelectorAll('nav a');
    expect([...links].map((link) => link.getAttribute('href'))).toEqual([
      '/',
      '/rejected',
      '/applications',
      '/profile',
      '/letter-examples',
      '/llm',
    ]);
  });

  it('switches the language with the EN / FR buttons, starting from the saved one', async () => {
    localStorage.setItem('language', 'fr');
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    const pressed = () => compiled.querySelector('.languages button.active')?.textContent?.trim();
    expect(pressed()).toBe('FR');

    (compiled.querySelector('.languages button') as HTMLButtonElement).click();
    await fixture.whenStable();
    expect(pressed()).toBe('EN');
    expect(localStorage.getItem('language')).toBe('en');
  });
});
