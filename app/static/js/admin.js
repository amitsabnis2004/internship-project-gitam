const analyticsBox = document.getElementById('analyticsBox');
const faqList = document.getElementById('faqList');
const unresolvedList = document.getElementById('unresolvedList');
const faqForm = document.getElementById('faqForm');
const contextForm = document.getElementById('contextForm');
const contextPdfInput = document.getElementById('contextPdf');
const replaceContextInput = document.getElementById('replaceContext');
const contextStatus = document.getElementById('contextStatus');
const contextList = document.getElementById('contextList');

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

async function loadContextFiles() {
  const response = await fetch('/chat/context/files');
  const files = await response.json();
  contextList.innerHTML = '';

  if (!files.length) {
    contextList.innerHTML = '<div class="card-item">No PDF context uploaded yet.</div>';
    return;
  }

  files.forEach((file) => {
    const div = document.createElement('div');
    div.className = 'card-item';
    div.innerHTML = `<strong>${file.file_name}</strong><br/><small>Chunks: ${file.chunk_count}</small>`;
    contextList.appendChild(div);
  });
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

contextForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const file = contextPdfInput.files?.[0];
  if (!file) {
    return;
  }

  const payload = new FormData();
  payload.append('file', file);

  contextStatus.textContent = 'Uploading and indexing PDF...';

  try {
    const replaceExisting = replaceContextInput.checked;
    const response = await fetch(`/chat/context/upload?replace_existing=${replaceExisting}`, {
      method: 'POST',
      body: payload,
    });

    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.detail || 'Upload failed');
    }

    contextStatus.textContent = `Uploaded ${result.file_name}. Chunks indexed: ${result.total_chunks}.`;
    contextForm.reset();
    await loadContextFiles();
  } catch (error) {
    contextStatus.textContent = error.message || 'Failed to upload context PDF';
  }
});

Promise.all([loadAnalytics(), loadFaqs(), loadUnresolved(), loadContextFiles()]).catch(() => {
  analyticsBox.textContent = 'Failed to load dashboard data';
});
