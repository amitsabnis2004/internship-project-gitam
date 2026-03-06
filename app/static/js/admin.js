const analyticsBox = document.getElementById('analyticsBox');
const faqList = document.getElementById('faqList');
const unresolvedList = document.getElementById('unresolvedList');
const faqForm = document.getElementById('faqForm');

async function loadAnalytics() {
  const response = await fetch('/analytics/summary');
  const data = await response.json();
  analyticsBox.textContent = JSON.stringify(data, null, 2);
}

async function loadFaqs() {
  const response = await fetch('/admin/faqs');
  const faqs = await response.json();
  faqList.innerHTML = '';

  faqs.forEach((faq) => {
    const div = document.createElement('div');
    div.className = 'card-item';
    div.innerHTML = `<strong>[${faq.intent}]</strong> ${faq.question}<br/><small>${faq.answer}</small>`;
    faqList.appendChild(div);
  });
}

async function loadUnresolved() {
  const response = await fetch('/admin/unresolved');
  const unresolved = await response.json();
  unresolvedList.innerHTML = '';

  unresolved.forEach((item) => {
    const div = document.createElement('div');
    div.className = 'card-item';
    div.innerHTML = `<strong>#${item.id}</strong> ${item.query}<br/><small>Intent: ${item.detected_intent} | Confidence: ${item.confidence}</small>`;
    unresolvedList.appendChild(div);
  });

  if (!unresolved.length) {
    unresolvedList.innerHTML = '<div class="card-item">No unresolved escalations.</div>';
  }
}

faqForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const intent = document.getElementById('faqIntent').value.trim();
  const question = document.getElementById('faqQuestion').value.trim();
  const answer = document.getElementById('faqAnswer').value.trim();

  if (!intent || !question || !answer) {
    return;
  }

  await fetch('/admin/faqs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ intent, question, answer })
  });

  faqForm.reset();
  await Promise.all([loadFaqs(), loadAnalytics()]);
});

Promise.all([loadAnalytics(), loadFaqs(), loadUnresolved()]).catch(() => {
  analyticsBox.textContent = 'Failed to load dashboard data';
});
