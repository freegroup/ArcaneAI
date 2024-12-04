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
        'examples/mood',
      ],
    },
    {
      type: 'doc',
      id: 'setup', 
      label: 'Setup',
    },
  ],
};
