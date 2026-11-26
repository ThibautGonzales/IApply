import { Routes } from '@angular/router';
import { Applications } from './applications/applications';
import { Jobs } from './jobs/jobs';
import { Profile } from './profile/profile';

export const routes: Routes = [
  { path: '', component: Jobs },
  { path: 'applications', component: Applications },
  { path: 'profile', component: Profile },
  // Any unknown address goes back to the offers.
  { path: '**', redirectTo: '' },
];
