const form = document.querySelector('#brief');
const message = document.querySelector('#form-message');
const entityInput = document.querySelector('#conflict-name');
const entityMessage = document.querySelector('#entity-message');
const selectedConflicts = new Map();

document.querySelectorAll('.numeric-grid input').forEach(input => {
  const error = input.parentElement.querySelector('.field-error');
  const validate = () => {
    const value = input.valueAsNumber;
    let text = '';
    if (input.value && Number.isNaN(value)) text = 'Enter a number.';
    else if (!Number.isNaN(value) && value < Number(input.min)) text = `Minimum is ${input.min}.`;
    else if (!Number.isNaN(value) && value > Number(input.max)) text = `Maximum is ${input.max}.`;
    error.textContent = text;
    input.setAttribute('aria-invalid', text ? 'true' : 'false');
  };
  input.addEventListener('input', validate);
  input.addEventListener('blur', validate);
});

function updatePickerSummaries() {
  document.querySelector('#vertical-summary').textContent = 'Verticals';
  document.querySelector('#support-summary').textContent = 'Opportunity types';
  document.querySelector('#stage-summary').textContent = 'Stage';
}
document.querySelectorAll('.picker-panel input').forEach(input => input.addEventListener('change', updatePickerSummaries));
updatePickerSummaries();

function editDistance(left, right) {
  const row = Array.from({ length: right.length + 1 }, (_, index) => index);
  for (let i = 1; i <= left.length; i += 1) {
    let diagonal = row[0]; row[0] = i;
    for (let j = 1; j <= right.length; j += 1) {
      const previous = row[j];
      row[j] = Math.min(row[j] + 1, row[j - 1] + 1, diagonal + (left[i - 1] === right[j - 1] ? 0 : 1));
      diagonal = previous;
    }
  }
  return row[right.length];
}
document.querySelector('#vertical-search').addEventListener('input', event => {
  const query = event.target.value.trim().toLowerCase().replace(/[^a-z0-9]/g, '');
  const matches = [];
  document.querySelectorAll('[data-picker="industry"] label').forEach(label => {
    const text = label.textContent.toLowerCase().replace(/[^a-z0-9]/g, '');
    const close = query && editDistance(query, text.slice(0, Math.max(query.length, 1))) <= Math.max(1, Math.floor(query.length / 3));
    label.hidden = Boolean(query) && !text.includes(query) && !close;
    if (!label.hidden && query) matches.push({ label: label.textContent.trim(), input: label.querySelector('input') });
  });
  const results = document.querySelector('#vertical-search-results');
  results.innerHTML = query ? (matches.length ? matches.map(match => `<button type="button" data-vertical="${match.input.value}">${match.label}</button>`).join('') : '<span>No close verticals</span>') : '';
  results.querySelectorAll('[data-vertical]').forEach(button => button.addEventListener('click', () => {
    const input = document.querySelector(`[data-picker="industry"] input[value="${button.dataset.vertical}"]`);
    input.checked = !input.checked; input.dispatchEvent(new Event('change')); event.target.value = ''; event.target.dispatchEvent(new Event('input'));
  }));
});
document.querySelector('#vertical-search').addEventListener('keydown', event => { if (event.key === 'Enter') event.preventDefault(); });
document.addEventListener('click', event => {
  document.querySelectorAll('.multi-picker[open]').forEach(picker => { if (!picker.contains(event.target)) picker.open = false; });
});

function renderCandidateOptions(result, raw) {
  const options = document.querySelector('#candidate-options');
  if (!result.candidates.length) { options.innerHTML = ''; return; }
  options.innerHTML = result.candidates.map(candidate => `<button type="button" data-candidate="${candidate.id}">${candidate.label}</button>`).join('');
  options.querySelectorAll('[data-candidate]').forEach(button => button.addEventListener('click', () => {
    const candidate = result.candidates.find(item => item.id === button.dataset.candidate);
    addConflict(candidate.id, candidate.label);
  }));
}
let resolveTimer;
let resolveSequence = 0;
entityInput.addEventListener('input', () => {
  clearTimeout(resolveTimer);
  const raw = entityInput.value.trim();
  document.querySelector('#candidate-options').innerHTML = '';
  if (raw.length < 2) return;
  const sequence = ++resolveSequence;
  resolveTimer = setTimeout(async () => {
    try {
      const response = await fetch('/api/resolve', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: raw }) });
      if (!response.ok || sequence !== resolveSequence) return;
      renderCandidateOptions(await response.json(), raw);
    } catch { /* Leave the entry untouched; suggestions are optional. */ }
  }, 250);
});
entityInput.addEventListener('keydown', event => {
  if (event.key === 'Enter') { event.preventDefault(); document.querySelector('#add-conflict').click(); }
});

function addConflict(id, label) { selectedConflicts.set(id, label); entityInput.value = ''; document.querySelector('#candidate-options').innerHTML = ''; entityMessage.textContent = ''; renderConflicts(); }
function renderConflicts() {
  document.querySelector('#conflicts').innerHTML = [...selectedConflicts].map(([id, label]) => `<button type="button" data-conflict="${id}" aria-label="Remove ${label}">${label} <span aria-hidden="true">×</span></button>`).join('');
  document.querySelectorAll('[data-conflict]').forEach(button => button.addEventListener('click', () => { selectedConflicts.delete(button.dataset.conflict); renderConflicts(); }));
}

document.querySelector('#add-conflict').addEventListener('click', () => {
  const raw = entityInput.value.trim();
  if (!raw) return;
  addConflict(`unknown:${raw.toLowerCase()}`, raw);
});

function renderMatches(matches) {
  const labels = ['Highest alignment', 'Strong next option', 'Worth a look'];
  document.querySelector('#matches').innerHTML = matches.map((match, index) => `<article class="match"><div class="match-topline"><span class="rank">${index + 1}</span><span class="alignment">${labels[index]}</span></div><div class="match-main"><p class="match-type">${match.type}</p><h3>${match.name}</h3><p>${match.summary}</p>${match.conflict_status ? `<p class="conflict-status ${match.conflict_status.startsWith('A private exclusion') ? 'conflict-found' : ''}">${match.conflict_status}</p>` : ''}<div class="why-fit"><strong>Why it ranked highly</strong><p>${match.reason}</p></div>${match.public_detail ? `<p class="public-detail"><strong>Published detail:</strong> ${match.public_detail}</p>` : ''}<p class="watchout"><strong>Before you apply:</strong> ${match.watchout}</p><a href="${match.source}" target="_blank" rel="noreferrer">Review the official program details <span aria-hidden="true">↗</span></a></div></article>`).join('');
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  const values = new FormData(form);
  const filters = { industry: [...document.querySelectorAll('[data-picker="industry"] input:checked')].map(input => input.value), stage: values.get('stage'), support: [...document.querySelectorAll('[data-picker="support"] input:checked')].map(input => input.value) };
  const mandate = Object.fromEntries(['program_window_months','raise_millions','dilution_percent','capital_raised_millions','revenue_millions','trl','team_size_band','institutional_ownership_band','institutional_control_band'].map(name => [name, values.get(name)]));
  mandate.conflicts = [...selectedConflicts.keys()].filter(id => !id.startsWith('unknown:'));
  message.textContent = '';
  const resultSection = document.querySelector('#result');
  const status = document.querySelector('#status');
  resultSection.hidden = false; resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  status.textContent = 'Encrypting your private mandate and scoring the catalog…'; document.querySelector('#matches').innerHTML = '';
  try {
    const response = await fetch('/api/match', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ filters, mandate }) });
    if (!response.ok) { const body = await response.json(); throw new Error(body.error || 'Unable to create a match.'); }
    const result = await response.json();
    status.textContent = 'Your encrypted match is complete. These are starting points for research, not a prediction of funding or acceptance.';
    renderMatches(result.matches);
  } catch (error) { status.textContent = error.message || 'The local matching bridge is not available. Start it with: python3 app/server.py'; }
});
