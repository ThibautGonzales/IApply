/** Languages the interface can be displayed in. English is the default. */
export type Language = 'en' | 'fr';

export const DEFAULT_LANGUAGE: Language = 'en';

/** English texts: the reference list of keys. */
const en = {
  'language.label': 'Language',
  'backend.label': 'Backend status:',
  'backend.checking': 'checking...',
  'backend.database': 'database',
  'backend.unreachable': 'API unreachable',
  'jobs.title': 'Job offers',
  'jobs.onSite': 'On-site',
  'jobs.remote': 'Remote',
  'jobs.none': 'No offers yet.',
  'collect.button': 'Collect',
  'collect.running': 'Collecting...',
  'collect.newOffers': 'new offers',
  'collect.found': 'found',
  'collect.errors': 'Errors:',
  'collect.failed': 'Collection failed: API unreachable.',
  'table.published': 'Published',
  'table.title': 'Title',
  'table.company': 'Company',
  'table.location': 'Location',
  'table.contract': 'Contract',
};

export type TranslationKey = keyof typeof en;

/** Every language must define every key: TypeScript reports any missing one. */
export const translations: Record<Language, Record<TranslationKey, string>> = {
  en,
  fr: {
    'language.label': 'Langue',
    'backend.label': 'État du backend :',
    'backend.checking': 'vérification...',
    'backend.database': 'base de données',
    'backend.unreachable': 'API injoignable',
    'jobs.title': "Offres d'emploi",
    'jobs.onSite': 'Sur site',
    'jobs.remote': 'Télétravail',
    'jobs.none': 'Aucune offre pour le moment.',
    'collect.button': 'Collecter',
    'collect.running': 'Collecte en cours...',
    'collect.newOffers': 'nouvelles offres',
    'collect.found': 'trouvées',
    'collect.errors': 'Erreurs :',
    'collect.failed': 'Échec de la collecte : API injoignable.',
    'table.published': 'Publiée le',
    'table.title': 'Intitulé',
    'table.company': 'Entreprise',
    'table.location': 'Lieu',
    'table.contract': 'Contrat',
  },
};
