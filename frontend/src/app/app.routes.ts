import { Routes } from '@angular/router';
import { Applications } from './applications/applications';
import { LetterPage } from './cover-letter/letter-page';
import { Jobs } from './jobs/jobs';
import { LetterExamples } from './letter-examples/letter-examples';
import { Llm } from './llm/llm';
import { Profile } from './profile/profile';
import { Rejected } from './rejected/rejected';

// `label` names the page in the top bar ("My space / Offers"): a translation key.
export const routes: Routes = [
  { path: '', component: Jobs, data: { label: 'nav.jobs' } },
  { path: 'rejected', component: Rejected, data: { label: 'nav.rejected' } },
  { path: 'applications', component: Applications, data: { label: 'nav.applications' } },
  { path: 'profile', component: Profile, data: { label: 'nav.profile' } },
  { path: 'letter-examples', component: LetterExamples, data: { label: 'nav.letterExamples' } },
  { path: 'jobs/:id/letter', component: LetterPage, data: { label: 'letter.title' } },
  { path: 'llm', component: Llm, data: { label: 'nav.llm' } },
  // Any unknown address goes back to the offers.
  { path: '**', redirectTo: '' },
];
