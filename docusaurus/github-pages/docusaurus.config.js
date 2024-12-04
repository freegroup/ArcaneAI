import { themes as prismThemes } from 'prism-react-renderer';

// docusaurus/docusaurus.config.js
module.exports = {
  title: 'ArcaneAI Dokumentation',
  tagline: 'Minimal und einfach',
  url: 'https://freegroup.github.io',
  baseUrl: '/ArcaneAI',
  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',
  favicon: 'img/favicon.ico',
  organizationName: 'freegroup', // Dein GitHub Username
  projectName: process.env.NODE_ENV === 'production' ? '/ArcaneAI/' : '/',
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
      items: [
        {
          type: 'html',
          value: '<span class="color header-slogan">How to create a AI text adventure engine</span>',
          position: 'left', 
        },
        {
          type: 'html',
          value: `
            <a
              href="https://github.com/freegroup/ArcaneAI"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="GitHub profile"
              class="github-button"
              style="display: flex; align-items: center;">
              <img
                src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
                alt="GitHub logo"
                style="width: 24px; height: 24px; margin-right: 5px;" />
              @freegroup
            </a>`,
          position: 'right',
        },
      ],
    },
    colorMode: {
      defaultMode: 'dark',          // Setzt das Dark Theme als Standard
      disableSwitch: true,          // Deaktiviert den Theme-Switcher, damit der Benutzer nicht wechseln kann
      respectPrefersColorScheme: false, // Ignoriert die Benutzerpräferenz
    },
    prism: {
      theme: prismThemes.dracula,
      additionalLanguages: ['bash', "python"],
    },  
  },
};
