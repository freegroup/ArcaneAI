// docusaurus/docusaurus.config.js
module.exports = {
  title: 'ArcaneAI Dokumentation',
  tagline: 'Minimal und einfach',
  url: 'https://freegroup.github.io',
  baseUrl: '/',
  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',
  favicon: 'img/favicon.ico',
  organizationName: 'freegroup', // Dein GitHub Username
  projectName: 'ArcaneAI',       // Der Name deines Repositories
  presets: [
    [
      '@docusaurus/preset-classic',
      {
        docs: {
          path: 'docs',
          routeBasePath: '/',
          sidebarPath: require.resolve('./sidebars.js'),
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      },
    ],
  ],
  themeConfig: {
    navbar: {
      title: 'ArcaneAI', // Der Text, der neben dem Logo angezeigt wird
      logo: {
        alt: 'Logo', // Alternativtext für das Logo
        src: 'img/logo.png',  // Pfad zum Logo (relativ zum `static`-Ordner)
      },

    },
    colorMode: {
      defaultMode: 'dark',          // Setzt das Dark Theme als Standard
      disableSwitch: true,          // Deaktiviert den Theme-Switcher, damit der Benutzer nicht wechseln kann
      respectPrefersColorScheme: false, // Ignoriert die Benutzerpräferenz
    },
  },
};
