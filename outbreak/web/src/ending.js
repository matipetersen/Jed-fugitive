// ---------------------------------------------------------------- how a run ends
function _band(h) { return h >= 75 ? 'saint' : h >= 40 ? 'survivor' : h >= 15 ? 'cold' : 'monster'; }

function build_ending(game, kind, cause = '') {
  const p = game.player, sc = game.scenario, days = game_day(game);
  const decoded = Object.values(game.docs).filter((d) => p.documents.includes(d.id) && is_decoded(d, game.know)).length;
  const score = p.kills * 2 + days * 25 + p.humanity + decoded * 8 + p.level * 12 + (kind === 'won' ? 500 : 0);
  const summary = [
    `Survived ${days} day${days !== 1 ? 's' : ''} (${game.clock.turn} turns)`,
    `Zombies destroyed: ${p.stats.zombies || 0}   People killed: ${p.stats.humans || 0}`,
    `Level ${p.level}   Humanity ${p.humanity}   Fluency ${Math.floor(game.know.fluency * 100)}%`,
    `Documents read: ${p.documents.length}   Words known: ${game.know.known.size}/${game.know.vocab.length}`,
  ];
  if (game.fallen.length) summary.push(`Survivors lost: ${game.fallen.length}   You were survivor #${game.generation}`);
  if (p.lost.length) summary.push('You lost your ' + p.lost.join(' and your ') + ' to survive.');
  let title, text;
  if (kind === 'won') [title, text] = CONTENT.win_endings[`${sc.id}|${_band(p.humanity)}`];
  else if (kind === 'turned') {
    title = 'You turned';
    text = 'The fever peaks and the world goes quiet. When you open your eyes again, you are hungry, and the sounds of the living are very loud.';
  } else if (kind === 'left_behind') {
    title = 'Left behind';
    text = `Day ${game.deadline_days + 1} dawns. Somewhere far away, the last way out leaves without you. The dead are patient. You are not.`;
  } else if (kind === 'closed') { title = 'The world is closed'; text = cause; }
  else { title = 'You died'; text = cause ? cap(cause) + '.' : 'You did not make it.'; }
  return { kind, title, text, summary, score, victory: kind === 'won' };
}
