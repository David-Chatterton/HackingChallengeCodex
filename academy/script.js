const checks = [...document.querySelectorAll('.check input')];
const unlock = document.querySelector('#unlock');
const clue = unlock.querySelector('.clue');

function updateProgress() {
  checks.forEach((check) => check.closest('.module').classList.toggle('complete', check.checked));
  const complete = checks.every((check) => check.checked);
  unlock.classList.toggle('revealed', complete);
  clue.hidden = !complete;
  unlock.querySelector('strong').textContent = complete ? 'Coordinates decrypted' : 'Coordinates encrypted';
  unlock.querySelector('div p').textContent = complete ? 'Your final mission is ready.' : 'Complete all four field checks to reveal your last clue.';
  localStorage.setItem('signal-school-progress', JSON.stringify(checks.map((c) => c.checked)));
}

try {
  const saved = JSON.parse(localStorage.getItem('signal-school-progress'));
  if (Array.isArray(saved)) checks.forEach((check, i) => { check.checked = Boolean(saved[i]); });
} catch (_) {}
checks.forEach((check) => check.addEventListener('change', updateProgress));
updateProgress();
