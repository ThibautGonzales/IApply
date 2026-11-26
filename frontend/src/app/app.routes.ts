import { Routes } from '@angular/router';
import { Applications } from './applications/applications';
import { Jobs } from './jobs/jobs';
import { Llm } from './llm/llm';
import { Profile } from './profile/profile';
import { Rejected } from './rejected/rejected';

export const routes: Routes = [
  { path: '', component: Jobs },
  { path: 'rejected', component: Rejected },
  { path: 'applications', component: Applications },
  { path: 'profile', component: Profile },
  { path: 'llm', component: Llm },
  // Any unknown address goes back to the offers.
  { path: '**', redirectTo: '' },
];
