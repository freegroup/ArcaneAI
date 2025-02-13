module.exports = {
  sidebar: [
    {
      type: 'doc',
      id: 'home', 
      label: 'Press Start',
    },
    {
      type: 'doc',
      id: 'tale', 
      label: 'Tale of an LLM Wrangler',
    },
    {
      type: 'category',
      label: 'Challenges',
      items: [
        'challenges/creative',
        'challenges/player',
        'challenges/audience',
        'challenges/biggest_challenges',
      ],
    },
    {
      type: 'doc',
      id: 'solutions', 
      label: 'Solutions',
    },
    {
      type: 'category',
      label: 'Examples',
      items: [
        'examples/state',
        'examples/mood',
        'examples/stt',
      ],
    },
    {
      type: 'category',
      label: 'Setup',
      items: [
        'setup/prerequisites',
        'setup/console',
        'setup/browser',
      ],
    },
  ],
};
