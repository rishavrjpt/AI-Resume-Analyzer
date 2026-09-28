/**
 * ResumeScope — Client-Side Application Logic
 * Professional UI state management and backend integration.
 */

// Global state
const state = {
  selectedFile: null,
  latestAnalysis: null,
  sampleResumes: [],
  builtInJobs: [],
  testResults: null,
  activeTab: 'analyze'
};

// DOM Elements
const elements = {
  // Navigation
  navTabs: document.querySelectorAll('.nav-tab'),
  tabContents: document.querySelectorAll('.tab-content'),
  systemStatusPill: document.getElementById('systemStatusPill'),

  // Analyzer
  dropzone: document.getElementById('dropzone'),
  resumeFileInput: document.getElementById('resumeFileInput'),
  fileSelectedBadge: document.getElementById('fileSelectedBadge'),
  selectedFileName: document.getElementById('selectedFileName'),
  btnRemoveFile: document.getElementById('btnRemoveFile'),
  jobDescriptionInput: document.getElementById('jobDescriptionInput'),
  btnLoadSampleJob: document.getElementById('btnLoadSampleJob'),
  analyzeForm: document.getElementById('analyzeForm'),
  btnAnalyze: document.getElementById('btnAnalyze'),
  btnClear: document.getElementById('btnClear'),
  analyzeError: document.getElementById('analyzeError'),
  emptyStatePlaceholder: document.getElementById('emptyStatePlaceholder'),
  loadingState: document.getElementById('loadingState'),
  analysisResults: document.getElementById('analysisResults'),

  // Metrics
  resDocStats: document.getElementById('resDocStats'),
  resDocType: document.getElementById('resDocType'),
  resSectionsCount: document.getElementById('resSectionsCount'),
  resSectionMethod: document.getElementById('resSectionMethod'),
  resSkillsCount: document.getElementById('resSkillsCount'),
  resCandidateTerms: document.getElementById('resCandidateTerms'),
  resLexicalSim: document.getElementById('resLexicalSim'),
  resSemanticSim: document.getElementById('resSemanticSim'),
  similarityActiveView: document.getElementById('similarityActiveView'),
  similarityEmptyView: document.getElementById('similarityEmptyView'),
  btnQuickLoadJD: document.getElementById('btnQuickLoadJD'),
  quickRoleChips: document.getElementById('quickRoleChips'),

  // Results Subtabs
  subTabs: document.querySelectorAll('.sub-tab'),
  subtabPanes: document.querySelectorAll('.subtab-pane'),
  comparisonContent: document.getElementById('comparisonContent'),
  noComparisonMessage: document.getElementById('noComparisonMessage'),
  comparisonExplanation: document.getElementById('comparisonExplanation'),
  matchingTermsCloud: document.getElementById('matchingTermsCloud'),
  notFoundTermsCloud: document.getElementById('notFoundTermsCloud'),
  additionalTermsCloud: document.getElementById('additionalTermsCloud'),
  countMatching: document.getElementById('countMatching'),
  countNotFound: document.getElementById('countNotFound'),
  countAdditional: document.getElementById('countAdditional'),
  feedbackList: document.getElementById('feedbackList'),
  sectionsContainer: document.getElementById('sectionsContainer'),
  skillsTaxonomyView: document.getElementById('skillsTaxonomyView'),
  rawTextPreview: document.getElementById('rawTextPreview'),

  // Export
  btnCopyFeedback: document.getElementById('btnCopyFeedback'),
  btnDownloadReport: document.getElementById('btnDownloadReport'),
  btnDownloadJson: document.getElementById('btnDownloadJson'),

  // Dashboard
  statApiStatus: document.getElementById('statApiStatus'),
  statApiVersion: document.getElementById('statApiVersion'),
  statModelName: document.getElementById('statModelName'),
  statModelType: document.getElementById('statModelType'),
  statTrainingStatus: document.getElementById('statTrainingStatus'),
  statTrainSamples: document.getElementById('statTrainSamples'),
  statEvalStatus: document.getElementById('statEvalStatus'),
  statEvalMetrics: document.getElementById('statEvalMetrics'),
  statTestSamplesCount: document.getElementById('statTestSamplesCount'),
  statSemanticModel: document.getElementById('statSemanticModel'),

  testJobSelect: document.getElementById('testJobSelect'),
  sampleResumesGrid: document.getElementById('sampleResumesGrid'),
  btnSelectAllTests: document.getElementById('btnSelectAllTests'),
  btnDeselectAllTests: document.getElementById('btnDeselectAllTests'),
  btnRunSelectedTests: document.getElementById('btnRunSelectedTests'),
  btnResetTestResults: document.getElementById('btnResetTestResults'),
  testResultsTableBody: document.getElementById('testResultsTableBody'),
  testRunMeta: document.getElementById('testRunMeta'),
  testExportButtons: document.getElementById('testExportButtons'),
  btnExportTestJson: document.getElementById('btnExportTestJson'),
  btnExportTestCsv: document.getElementById('btnExportTestCsv'),
  diagSummaryRow: document.getElementById('diagSummaryRow'),
  diagPassBar: document.getElementById('diagPassBar'),
  diagPassText: document.getElementById('diagPassText'),
  diagAvgSections: document.getElementById('diagAvgSections'),
  diagAvgSkills: document.getElementById('diagAvgSkills'),

  // Modal
  sampleDetailModal: document.getElementById('sampleDetailModal'),
  modalTitle: document.getElementById('modalTitle'),
  modalBody: document.getElementById('modalBody'),
  btnCloseModal: document.getElementById('btnCloseModal'),
  btnCloseModalFooter: document.getElementById('btnCloseModalFooter'),

  // Insights
  sectionModelCompBody: document.getElementById('sectionModelCompBody'),
  perClassTableBody: document.getElementById('perClassTableBody'),
  skillEvalPrecision: document.getElementById('skillEvalPrecision'),
  skillEvalRecall: document.getElementById('skillEvalRecall'),
  skillEvalF1: document.getElementById('skillEvalF1'),
  skillConfusionCounts: document.getElementById('skillConfusionCounts'),
  matchingModelsBody: document.getElementById('matchingModelsBody')
};

// ----------------------------------------------------
// Initialization
// ----------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  setupNavigation();
  setupUploadHandlers();
  setupAnalyzerForm();
  setupDashboardControls();
  setupModal();
  checkSystemHealth();
  loadTestSamples();
  loadInsights();
});

// ----------------------------------------------------
// 1. Navigation
// ----------------------------------------------------
function setupNavigation() {
  elements.navTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetTab = tab.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });

  // Results Subtabs
  elements.subTabs.forEach(subTab => {
    subTab.addEventListener('click', () => {
      const targetSubtab = subTab.getAttribute('data-subtab');
      elements.subTabs.forEach(t => t.classList.remove('active'));
      elements.subtabPanes.forEach(p => p.classList.remove('active'));

      subTab.classList.add('active');
      const pane = document.getElementById(`subtab-${targetSubtab}`);
      if (pane) pane.classList.add('active');
    });
  });
}

function switchTab(tabId) {
  state.activeTab = tabId;
  elements.navTabs.forEach(t => {
    const isActive = t.getAttribute('data-tab') === tabId;
    t.classList.toggle('active', isActive);
    t.setAttribute('aria-selected', isActive ? 'true' : 'false');
  });

  elements.tabContents.forEach(content => {
    content.classList.toggle('active', content.id === `tab-${tabId}`);
  });

  // If opening insights or dashboard, refresh data
  if (tabId === 'insights') loadInsights();
  if (tabId === 'dashboard') loadModelInfo();
}

// ----------------------------------------------------
// 2. System Health & Model Info
// ----------------------------------------------------
async function checkSystemHealth() {
  try {
    const res = await fetch('/api/health');
    if (!res.ok) throw new Error('API returned non-200');
    const data = await res.json();

    elements.systemStatusPill.classList.add('healthy');
    elements.systemStatusPill.querySelector('.status-text').textContent = 'API & Pipeline Online';

    if (elements.statApiStatus) {
      elements.statApiStatus.textContent = 'Active (Online)';
      elements.statApiVersion.textContent = `Version ${data.version}`;
      elements.statTestSamplesCount.textContent = `${data.sample_resumes_count} Synthetic Resumes`;
    }
  } catch (err) {
    elements.systemStatusPill.classList.remove('healthy');
    elements.systemStatusPill.querySelector('.status-text').textContent = 'API Offline';
    if (elements.statApiStatus) elements.statApiStatus.textContent = 'Unavailable';
  }
}

async function loadModelInfo() {
  try {
    const res = await fetch('/api/model-info');
    if (!res.ok) return;
    const data = await res.json();

    if (elements.statModelName) elements.statModelName.textContent = data.model_name;
    if (elements.statModelType) elements.statModelType.textContent = data.model_type;
    if (elements.statTrainSamples) elements.statTrainSamples.textContent = `${data.train_samples} samples across 11 documents`;
    if (elements.statEvalStatus) {
      elements.statEvalStatus.textContent = data.evaluation_status === 'completed' ? 'Completed' : 'Pending';
    }
  } catch (e) {
    console.error('Failed to load model info', e);
  }
}

// ----------------------------------------------------
// 3. File Upload & Drag-and-Drop
// ----------------------------------------------------
function setupUploadHandlers() {
  const { dropzone, resumeFileInput, btnRemoveFile } = elements;

  dropzone.addEventListener('click', (e) => {
    if (e.target !== btnRemoveFile) {
      resumeFileInput.click();
    }
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFileSelection(files[0]);
  });

  resumeFileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) handleFileSelection(e.target.files[0]);
  });

  btnRemoveFile.addEventListener('click', (e) => {
    e.stopPropagation();
    clearSelectedFile();
  });
}

function handleFileSelection(file) {
  const allowedExts = ['.pdf', '.docx', '.txt'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();

  if (!allowedExts.includes(ext)) {
    showAnalyzeError(`Unsupported file format '${ext}'. Please upload a PDF, DOCX, or TXT file.`);
    return;
  }

  if (file.size > 5 * 1024 * 1024) {
    showAnalyzeError('File exceeds the 5MB size limit. Please upload a smaller document.');
    return;
  }

  hideAnalyzeError();
  state.selectedFile = file;
  elements.selectedFileName.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  elements.fileSelectedBadge.style.display = 'flex';
  elements.dropzone.querySelector('.dropzone-content').style.display = 'none';
}

function clearSelectedFile() {
  state.selectedFile = null;
  elements.resumeFileInput.value = '';
  elements.fileSelectedBadge.style.display = 'none';
  elements.dropzone.querySelector('.dropzone-content').style.display = 'block';
}

function showAnalyzeError(msg) {
  elements.analyzeError.textContent = msg;
  elements.analyzeError.style.display = 'block';
}

function hideAnalyzeError() {
  elements.analyzeError.textContent = '';
  elements.analyzeError.style.display = 'none';
}

// ----------------------------------------------------
// 4. Analyze Resume Execution
// ----------------------------------------------------
function setupAnalyzerForm() {
  // Indian Tech Role Quick Selectors
  const roleKeywords = {
    backend: "jd_backend_engineer_india",
    analyst: "jd_data_analyst_india",
    ml: "jd_ml_engineer_india",
    frontend: "jd_frontend_developer_india"
  };

  document.querySelectorAll('.btn-role-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const role = chip.getAttribute('data-role');
      const targetId = roleKeywords[role];
      const found = state.builtInJobs.find(j => j.id === targetId || j.id.includes(role));
      if (found) {
        elements.jobDescriptionInput.value = found.description;
        chip.style.borderColor = 'var(--primary)';
        chip.style.backgroundColor = '#eff6ff';
        setTimeout(() => { 
          chip.style.borderColor = ''; 
          chip.style.backgroundColor = '';
        }, 1200);
      }
    });
  });

  if (elements.btnQuickLoadJD) {
    elements.btnQuickLoadJD.addEventListener('click', () => {
      if (state.builtInJobs.length > 0) {
        elements.jobDescriptionInput.value = state.builtInJobs[0].description;
        if (state.selectedFile) {
          elements.btnAnalyze.click();
        } else {
          elements.jobDescriptionInput.focus();
        }
      }
    });
  }

  elements.btnLoadSampleJob.addEventListener('click', () => {
    if (state.builtInJobs.length > 0) {
      const job = state.builtInJobs[0];
      elements.jobDescriptionInput.value = job.description;
    }
  });

  elements.btnClear.addEventListener('click', () => {
    clearSelectedFile();
    elements.jobDescriptionInput.value = '';
    hideAnalyzeError();
    elements.analysisResults.style.display = 'none';
    elements.emptyStatePlaceholder.style.display = 'block';
  });

  elements.analyzeForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!state.selectedFile) {
      showAnalyzeError('Please select a resume file (PDF, DOCX, or TXT) before analyzing.');
      return;
    }

    hideAnalyzeError();
    elements.emptyStatePlaceholder.style.display = 'none';
    elements.analysisResults.style.display = 'none';
    elements.loadingState.style.display = 'block';

    const formData = new FormData();
    formData.append('resume_file', state.selectedFile);

    const jdText = elements.jobDescriptionInput.value.trim();
    if (jdText) {
      formData.append('job_description', jdText);
    }

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errJson = await response.json();
        throw new Error(errJson.detail || 'Analysis request failed.');
      }

      const results = await response.json();
      state.latestAnalysis = results;
      displayAnalysisResults(results);
    } catch (err) {
      showAnalyzeError(`Error: ${err.message}`);
      elements.emptyStatePlaceholder.style.display = 'block';
    } finally {
      elements.loadingState.style.display = 'none';
    }
  });

  // Export Listeners
  elements.btnCopyFeedback.addEventListener('click', copyAllFeedback);
  elements.btnDownloadReport.addEventListener('click', downloadTextReport);
  elements.btnDownloadJson.addEventListener('click', downloadJsonReport);
}

function displayAnalysisResults(data) {
  elements.analysisResults.style.display = 'block';

  // 1. Metric Tiles
  const doc = data.document_info;
  elements.resDocStats.textContent = `${doc.word_count} words`;
  elements.resDocType.textContent = `${doc.file_type.toUpperCase()} • ${doc.line_count} lines`;

  const sec = data.section_analysis;
  elements.resSectionsCount.textContent = `${sec.total_detected} / 6`;
  elements.resSectionMethod.textContent = sec.classification_method;

  const skl = data.skill_analysis;
  elements.resSkillsCount.textContent = skl.total_skills;
  elements.resCandidateTerms.textContent = `${skl.total_candidates} candidate terms`;

  // Similarity display
  const comp = data.job_comparison;
  if (comp) {
    if (elements.similarityActiveView) elements.similarityActiveView.style.display = 'block';
    if (elements.similarityEmptyView) elements.similarityEmptyView.style.display = 'none';

    const sim = comp.similarity_estimates;
    const lexScore = sim.lexical_similarity_score;
    const semScore = sim.semantic_similarity_score;

    elements.resLexicalSim.textContent = lexScore !== null 
      ? `${Math.round(lexScore * 100)}% (${lexScore.toFixed(3)})` 
      : '—';
    elements.resSemanticSim.textContent = semScore !== null 
      ? `${Math.round(semScore * 100)}% (${semScore.toFixed(3)})` 
      : 'N/A';
    renderComparison(comp);
  } else {
    if (elements.similarityActiveView) elements.similarityActiveView.style.display = 'none';
    if (elements.similarityEmptyView) elements.similarityEmptyView.style.display = 'block';

    elements.noComparisonMessage.style.display = 'block';
    elements.comparisonContent.style.display = 'none';
  }

  // 2. Feedback Suggestions
  renderFeedback(data.feedback_suggestions);

  // 3. Extracted Sections
  renderSections(sec.sections, sec.missing_sections);

  // 4. Skills Taxonomy
  renderSkillsTaxonomy(skl);

  // 5. Preview
  elements.rawTextPreview.textContent = data.clean_text_preview;
}

function renderComparison(comp) {
  elements.noComparisonMessage.style.display = 'none';
  elements.comparisonContent.style.display = 'block';

  elements.comparisonExplanation.textContent = comp.explanation;

  const tc = comp.term_comparison;
  elements.countMatching.textContent = tc.total_matching;
  elements.countNotFound.textContent = tc.total_not_found;
  elements.countAdditional.textContent = tc.total_additional;

  // Matching
  elements.matchingTermsCloud.innerHTML = tc.matching_skills.length > 0
    ? tc.matching_skills.map(s => `<span class="skill-tag" title="Category: ${s.category}">${escapeHtml(s.name)}</span>`).join('')
    : '<span class="text-muted" style="font-size:0.8rem;">No explicit taxonomy matches found between documents.</span>';

  // Not Found
  elements.notFoundTermsCloud.innerHTML = tc.not_found_in_resume.length > 0
    ? tc.not_found_in_resume.map(s => `<span class="skill-tag" style="border-color:#f59e0b;" title="Category: ${s.category}">${escapeHtml(s.name)}</span>`).join('')
    : '<span class="text-muted" style="font-size:0.8rem;">All identified job terms were found in resume text.</span>';

  // Additional
  elements.additionalTermsCloud.innerHTML = tc.additional_resume_skills.length > 0
    ? tc.additional_resume_skills.slice(0, 15).map(s => `<span class="skill-tag" title="Category: ${s.category}">${escapeHtml(s.name)}</span>`).join('')
    : '<span class="text-muted" style="font-size:0.8rem;">No additional taxonomy skills detected.</span>';
}

function renderFeedback(suggestions) {
  if (!suggestions || suggestions.length === 0) {
    elements.feedbackList.innerHTML = `
      <div class="empty-state" style="padding:2rem;">
        <p>No actionable writing issues detected based on our heuristic checks. Keep your bullets concise and factually accurate!</p>
      </div>`;
    return;
  }

  elements.feedbackList.innerHTML = suggestions.map(s => `
    <div class="feedback-item severity-${s.severity}">
      <div class="feedback-item-header">
        <span class="feedback-cat-badge">${escapeHtml(s.category)} • ${escapeHtml(s.target_section)}</span>
        <button type="button" class="btn-copy-sug" onclick="copyText('${escapeQuote(s.suggested_action)}')">Copy Guidance</button>
      </div>
      <div class="feedback-issue">${escapeHtml(s.issue)}</div>
      <div class="feedback-source">"${escapeHtml(s.source_text)}"</div>
      <div class="feedback-explanation">${escapeHtml(s.explanation)}</div>
      ${s.example_rewrite ? `
        <div class="feedback-rewrite-box">
          <strong>Safe Template Suggestion:</strong>
          <div>${escapeHtml(s.example_rewrite)}</div>
        </div>
      ` : ''}
    </div>
  `).join('');
}

function renderSections(sectionsMap, missingList) {
  const container = elements.sectionsContainer;
  let html = '';

  if (missingList && missingList.length > 0) {
    html += `
      <div class="info-banner" style="margin-bottom:1rem; border-color:var(--warning); color:#fcd34d;">
        <strong>Missing Standard Sections:</strong> ${missingList.map(s => s.toUpperCase()).join(', ')}
      </div>`;
  }

  for (const [secName, text] of Object.entries(sectionsMap)) {
    html += `
      <div class="section-accordion">
        <div class="accordion-header" onclick="toggleAccordion(this)">
          <span>${secName.toUpperCase()}</span>
          <span style="font-size:0.8rem; color:var(--text-dim);">${text.split('\n').length} lines ▼</span>
        </div>
        <div class="accordion-content">${escapeHtml(text)}</div>
      </div>
    `;
  }
  container.innerHTML = html;
}

function toggleAccordion(header) {
  const content = header.nextElementSibling;
  const isHidden = content.style.display === 'none';
  content.style.display = isHidden ? 'block' : 'none';
  header.querySelector('span:last-child').textContent = isHidden ? '▲' : '▼';
}

function renderSkillsTaxonomy(skillAnalysis) {
  const container = elements.skillsTaxonomyView;
  let html = '<div style="display:flex; flex-direction:column; gap:1.25rem;">';

  // Grouped by Category
  for (const [cat, skills] of Object.entries(skillAnalysis.by_category)) {
    html += `
      <div>
        <h4 style="font-size:0.9rem; color:var(--primary); margin-bottom:0.4rem;">${escapeHtml(cat)} (${skills.length})</h4>
        <div class="tag-cloud">
          ${skills.map(name => `<span class="skill-tag">${escapeHtml(name)}</span>`).join('')}
        </div>
      </div>
    `;
  }

  // Candidate Terms
  if (skillAnalysis.candidate_terms.length > 0) {
    html += `
      <div style="margin-top:0.5rem; border-top:1px solid var(--border-subtle); padding-top:1rem;">
        <h4 style="font-size:0.9rem; color:#fcd34d; margin-bottom:0.4rem;">Candidate Acronyms & Terms (${skillAnalysis.candidate_terms.length})</h4>
        <div class="tag-cloud">
          ${skillAnalysis.candidate_terms.map(c => `<span class="skill-tag" style="border-color:#f59e0b;">${escapeHtml(c.name)}</span>`).join('')}
        </div>
      </div>
    `;
  }

  html += '</div>';
  container.innerHTML = html;
}

// ----------------------------------------------------
// 5. ML Testing Dashboard
// ----------------------------------------------------
async function loadTestSamples() {
  try {
    const res = await fetch('/api/test-samples');
    if (!res.ok) return;
    const data = await res.json();
    state.sampleResumes = data.samples;
    state.builtInJobs = data.built_in_job_descriptions;

    // Populate Job dropdown
    elements.testJobSelect.innerHTML = state.builtInJobs.map(j => `
      <option value="${j.id}">${escapeHtml(j.title)}</option>
    `).join('') + '<option value="none">None (Analyze without Job Description)</option>';

    // Render 8 synthetic resume cards
    elements.sampleResumesGrid.innerHTML = state.sampleResumes.map((s, idx) => `
      <div class="sample-resume-item selected" data-filename="${s.filename}" onclick="toggleSampleCard(this)">
        <input type="checkbox" checked value="${s.filename}" onclick="event.stopPropagation(); syncCardSelection(this);">
        <div class="sample-resume-info">
          <div class="sample-resume-name">${escapeHtml(s.filename)}</div>
          <div style="font-size:0.75rem; color:#93c5fd; margin-top:2px;">${escapeHtml(s.persona)}</div>
          <div class="sample-resume-desc">${escapeHtml(s.edge_case_tested)}</div>
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error('Failed to load test samples', err);
  }
}

function toggleSampleCard(card) {
  const checkbox = card.querySelector('input[type="checkbox"]');
  checkbox.checked = !checkbox.checked;
  card.classList.toggle('selected', checkbox.checked);
}

function syncCardSelection(checkbox) {
  checkbox.closest('.sample-resume-item').classList.toggle('selected', checkbox.checked);
}

function setupDashboardControls() {
  elements.btnSelectAllTests.addEventListener('click', () => {
    document.querySelectorAll('.sample-resume-item').forEach(card => {
      card.classList.add('selected');
      card.querySelector('input[type="checkbox"]').checked = true;
    });
  });

  elements.btnDeselectAllTests.addEventListener('click', () => {
    document.querySelectorAll('.sample-resume-item').forEach(card => {
      card.classList.remove('selected');
      card.querySelector('input[type="checkbox"]').checked = false;
    });
  });

  elements.btnResetTestResults.addEventListener('click', () => {
    state.testResults = null;
    elements.testResultsTableBody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center text-muted">Select synthetic resumes above and click <strong>Run Test on Selected</strong>.</td>
      </tr>`;
    elements.testRunMeta.textContent = 'Displayed test results have been reset.';
    elements.testExportButtons.style.display = 'none';
    elements.diagSummaryRow.style.display = 'none';
  });

  elements.btnRunSelectedTests.addEventListener('click', runSelectedTests);
  elements.btnExportTestJson.addEventListener('click', exportTestResultsJson);
  elements.btnExportTestCsv.addEventListener('click', exportTestResultsCsv);
}

async function runSelectedTests() {
  const selectedCheckboxes = document.querySelectorAll('.sample-resume-item input[type="checkbox"]:checked');
  const selectedFiles = Array.from(selectedCheckboxes).map(cb => cb.value);

  if (selectedFiles.length === 0) {
    alert('Please select at least one synthetic resume to test.');
    return;
  }

  const selectedJobId = elements.testJobSelect.value;

  elements.btnRunSelectedTests.disabled = true;
  elements.btnRunSelectedTests.textContent = 'Executing Tests...';
  elements.testRunMeta.textContent = `Running live test on ${selectedFiles.length} synthetic resume fixtures...`;

  try {
    const res = await fetch('/api/test-samples/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        selected_filenames: selectedFiles,
        job_description_id: selectedJobId !== 'none' ? selectedJobId : null
      })
    });

    if (!res.ok) throw new Error('Test run request failed');
    const data = await res.json();
    state.testResults = data;
    renderTestResults(data);
  } catch (err) {
    elements.testRunMeta.textContent = `Error running tests: ${err.message}`;
  } finally {
    elements.btnRunSelectedTests.disabled = false;
    elements.btnRunSelectedTests.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
      Run Test on Selected`;
  }
}

function renderTestResults(data) {
  elements.testRunMeta.textContent = `Run ID: ${data.run_id} • Executed at ${new Date(data.timestamp).toLocaleTimeString()} • ${data.successful_runs} Passed, ${data.failed_runs} Failed`;
  elements.testExportButtons.style.display = 'flex';
  elements.diagSummaryRow.style.display = 'grid';

  const rows = data.results;
  let totalSections = 0;
  let totalSkills = 0;

  elements.testResultsTableBody.innerHTML = rows.map((r, idx) => {
    totalSections += r.sections_count;
    totalSkills += r.skills_extracted_count;

    return `
      <tr>
        <td><strong>${escapeHtml(r.filename)}</strong></td>
        <td><span class="comp-badge badge-green">${escapeHtml(r.parsing_status)}</span></td>
        <td>${r.sections_count} detected</td>
        <td>${r.skills_extracted_count} skills</td>
        <td>${r.matched_terms_count} terms</td>
        <td>${r.not_found_terms_count} terms</td>
        <td><span class="comp-badge ${r.analysis_status === 'Success' ? 'badge-green' : 'badge-amber'}">${escapeHtml(r.analysis_status)}</span></td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="openSampleDetails(${idx})">View Details</button>
        </td>
      </tr>
    `;
  }).join('');

  // Diagnostic charts update
  const pct = Math.round((data.successful_runs / data.total_tested) * 100);
  elements.diagPassBar.style.width = `${pct}%`;
  elements.diagPassText.textContent = `${data.successful_runs} / ${data.total_tested} (${pct}%)`;
  elements.diagAvgSections.textContent = (totalSections / rows.length).toFixed(1);
  elements.diagAvgSkills.textContent = (totalSkills / rows.length).toFixed(1);
}

function openSampleDetails(index) {
  if (!state.testResults || !state.testResults.results[index]) return;
  const row = state.testResults.results[index];
  const analysis = row.full_analysis;

  elements.modalTitle.textContent = `Test Fixture Details: ${row.filename}`;

  if (!analysis) {
    elements.modalBody.innerHTML = `<p class="text-muted">No detailed analysis available for this fixture.</p>`;
  } else {
    elements.modalBody.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:1rem;">
        <div class="metrics-grid">
          <div class="metric-card">
            <span class="metric-label">Sections Detected</span>
            <span class="metric-value">${row.sections_count}</span>
            <span class="metric-sub">${row.sections_detected.join(', ')}</span>
          </div>
          <div class="metric-card">
            <span class="metric-label">Skills Extracted</span>
            <span class="metric-value">${row.skills_extracted_count}</span>
            <span class="metric-sub">${row.extracted_skills_sample.join(', ')}</span>
          </div>
          <div class="metric-card">
            <span class="metric-label">Text Similarity</span>
            <span class="metric-value">${row.lexical_similarity !== null ? row.lexical_similarity.toFixed(3) : 'N/A'}</span>
            <span class="metric-sub">TF-IDF Lexical Cosine</span>
          </div>
        </div>

        <div>
          <h4>Detected Sections:</h4>
          <pre class="code-preview" style="max-height:180px;">${escapeHtml(JSON.stringify(analysis.section_analysis.sections, null, 2))}</pre>
        </div>

        <div>
          <h4>Feedback Generated (${row.feedback_count}):</h4>
          <ul style="padding-left:1.25rem; font-size:0.85rem; color:var(--text-muted);">
            ${analysis.feedback_suggestions.map(s => `<li><strong>${escapeHtml(s.issue)}:</strong> ${escapeHtml(s.suggested_action)}</li>`).join('')}
          </ul>
        </div>
      </div>
    `;
  }

  elements.sampleDetailModal.style.display = 'flex';
}

function setupModal() {
  const close = () => { elements.sampleDetailModal.style.display = 'none'; };
  elements.btnCloseModal.addEventListener('click', close);
  elements.btnCloseModalFooter.addEventListener('click', close);
  elements.sampleDetailModal.addEventListener('click', (e) => {
    if (e.target === elements.sampleDetailModal) close();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') close();
  });
}

// ----------------------------------------------------
// 6. ML Insights Page
// ----------------------------------------------------
async function loadInsights() {
  try {
    const res = await fetch('/api/insights');
    if (!res.ok) return;
    const data = await res.json();

    if (!data.has_evaluation || data.evaluation_summary === 'Not run yet') {
      elements.sectionModelCompBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Evaluation experiments not executed yet. Run 'python src/evaluate.py' to generate benchmark metrics.</td></tr>`;
      return;
    }

    const evalData = data.evaluation_summary;
    const secEval = evalData.section_classification;
    const skillEval = evalData.skill_extraction;
    const matchEval = evalData.matching_models;

    // 1. Model comparison table
    const ruleBase = secEval.baseline_rule_based;
    const mlModel = secEval.ml_classifier;

    elements.sectionModelCompBody.innerHTML = `
      <tr>
        <td><strong>Rule-Based Baseline</strong></td>
        <td>Regex patterns & layout cues</td>
        <td><code>${ruleBase.macro_f1.toFixed(4)}</code></td>
        <td><code>${ruleBase.weighted_f1.toFixed(4)}</code></td>
        <td>Baseline (0.0000)</td>
      </tr>
      <tr>
        <td><strong>Trained ML Section Classifier</strong></td>
        <td>TF-IDF (1-3 n-grams) + Logistic Regression</td>
        <td><strong class="text-green">${mlModel.macro_f1.toFixed(4)}</strong></td>
        <td><strong class="text-green">${mlModel.weighted_f1.toFixed(4)}</strong></td>
        <td><strong class="text-purple">+${secEval.comparison_delta_macro_f1.toFixed(4)}</strong></td>
      </tr>
    `;

    // 2. Per-class table
    const perClass = mlModel.per_class;
    elements.perClassTableBody.innerHTML = Object.entries(perClass).map(([cls, metrics]) => `
      <tr>
        <td><strong>${escapeHtml(cls.toUpperCase())}</strong></td>
        <td>${metrics.precision.toFixed(4)}</td>
        <td>${metrics.recall.toFixed(4)}</td>
        <td><strong>${metrics['f1-score'].toFixed(4)}</strong></td>
        <td>${metrics.support}</td>
      </tr>
    `).join('');

    // 3. Skill Eval
    elements.skillEvalPrecision.textContent = skillEval.precision.toFixed(4);
    elements.skillEvalRecall.textContent = skillEval.recall.toFixed(4);
    elements.skillEvalF1.textContent = skillEval.f1_score.toFixed(4);
    elements.skillConfusionCounts.textContent = `${skillEval.total_true_positives} / ${skillEval.total_false_positives} / ${skillEval.total_false_negatives}`;

    // 4. Matching Models
    const lex = matchEval.lexical_tfidf;
    const sem = matchEval.semantic_embeddings;

    elements.matchingModelsBody.innerHTML = `
      <tr>
        <td><strong>Lexical Matching (TF-IDF)</strong></td>
        <td>${escapeHtml(lex.model_description)}</td>
        <td><strong>${lex.spearman_correlation_with_relevance.toFixed(4)}</strong></td>
        <td>${(lex.precision_at_1 * 100).toFixed(0)}%</td>
        <td>Measures exact vocabulary and n-gram overlap between documents.</td>
      </tr>
      <tr>
        <td><strong>Semantic Embeddings</strong></td>
        <td>${escapeHtml(sem.model_name)}</td>
        <td><strong>${sem.spearman_correlation_with_relevance ? sem.spearman_correlation_with_relevance.toFixed(4) : 'N/A'}</strong></td>
        <td>${sem.precision_at_1 ? (sem.precision_at_1 * 100).toFixed(0) + '%' : 'N/A'}</td>
        <td>Measures dense semantic vector similarity in latent embedding space.</td>
      </tr>
    `;

  } catch (err) {
    console.error('Failed to load insights', err);
  }
}

// ----------------------------------------------------
// 7. Utilities & Exports
// ----------------------------------------------------
function copyText(text) {
  navigator.clipboard.writeText(text).then(() => {
    alert('Copied to clipboard!');
  });
}

function copyAllFeedback() {
  if (!state.latestAnalysis || !state.latestAnalysis.feedback_suggestions) return;
  const lines = state.latestAnalysis.feedback_suggestions.map(s => (
    `[${s.category}] Section: ${s.target_section}\nIssue: ${s.issue}\nSource: "${s.source_text}"\nSuggested Action: ${s.suggested_action}\n`
  ));
  copyText(lines.join('\n---\n'));
}

function downloadTextReport() {
  if (!state.latestAnalysis) return;
  const a = state.latestAnalysis;
  const doc = a.document_info;
  const sec = a.section_analysis;
  const skl = a.skill_analysis;
  const comp = a.job_comparison;

  let report = `====================================================\n`;
  report += `RESUMESCOPE — DOCUMENT ALIGNMENT REPORT\n`;
  report += `Document: ${doc.filename} (${doc.file_type.toUpperCase()}, ${doc.word_count} words)\n`;
  report += `Date: ${new Date().toLocaleString()}\n`;
  report += `====================================================\n\n`;

  report += `1. DETECTED SECTIONS (${sec.total_detected}/6):\n`;
  sec.detected_sections.forEach(s => report += `  - ${s.toUpperCase()}\n`);
  if (sec.missing_sections.length > 0) {
    report += `  Missing standard sections: ${sec.missing_sections.join(', ')}\n`;
  }
  report += `\n`;

  report += `2. EXTRACTED SKILLS (${skl.total_skills}):\n`;
  skl.verified_skills.forEach(s => report += `  - ${s.name} (${s.category})\n`);
  report += `\n`;

  if (comp) {
    const tc = comp.term_comparison;
    const sim = comp.similarity_estimates;
    report += `3. JOB DESCRIPTION COMPARISON:\n`;
    report += `  Lexical Text Similarity: ${sim.lexical_similarity_score}\n`;
    report += `  Semantic Similarity:     ${sim.semantic_similarity_score || 'N/A'}\n`;
    report += `  Matching Terms (${tc.total_matching}): ${tc.matching_skills.map(s => s.name).join(', ')}\n`;
    report += `  Not Found in Resume (${tc.total_not_found}): ${tc.not_found_in_resume.map(s => s.name).join(', ')}\n\n`;
  }

  report += `4. EVIDENCE-GROUNDED SUGGESTIONS (${a.feedback_suggestions.length}):\n`;
  a.feedback_suggestions.forEach((s, idx) => {
    report += `  [Suggestion ${idx + 1}] ${s.category} (${s.target_section})\n`;
    report += `  Issue: ${s.issue}\n`;
    report += `  Source Text: "${s.source_text}"\n`;
    report += `  Guidance: ${s.suggested_action}\n`;
    if (s.example_rewrite) report += `  Example Rewrite: ${s.example_rewrite}\n`;
    report += `\n`;
  });

  report += `====================================================\n`;
  report += `DISCLAIMER: This report is a personal resume review aid.\n`;
  report += `It does NOT predict ATS pass rates, interview calls, or hiring outcomes.\n`;
  report += `====================================================\n`;

  downloadBlob(new Blob([report], { type: 'text/plain' }), `ResumeScope_Report_${doc.filename}.txt`);
}

function downloadJsonReport() {
  if (!state.latestAnalysis) return;
  const jsonStr = JSON.stringify(state.latestAnalysis, null, 2);
  downloadBlob(new Blob([jsonStr], { type: 'application/json' }), `ResumeScope_Analysis_${state.latestAnalysis.document_info.filename}.json`);
}

function exportTestResultsJson() {
  if (!state.testResults) return;
  downloadBlob(new Blob([JSON.stringify(state.testResults, null, 2)], { type: 'application/json' }), `ResumeScope_Test_Results_${state.testResults.run_id}.json`);
}

function exportTestResultsCsv() {
  if (!state.testResults) return;
  const rows = state.testResults.results;
  const headers = ['Filename', 'Parsing Status', 'Sections Count', 'Skills Count', 'Matched Terms', 'Not Found Terms', 'Lexical Sim', 'Semantic Sim', 'Feedback Count', 'Status'];
  const csvLines = [headers.join(',')];

  rows.forEach(r => {
    csvLines.push([
      `"${r.filename}"`,
      `"${r.parsing_status}"`,
      r.sections_count,
      r.skills_extracted_count,
      r.matched_terms_count,
      r.not_found_terms_count,
      r.lexical_similarity !== null ? r.lexical_similarity : '',
      r.semantic_similarity !== null ? r.semantic_similarity : '',
      r.feedback_count,
      `"${r.analysis_status}"`
    ].join(','));
  });

  downloadBlob(new Blob([csvLines.join('\n')], { type: 'text/csv' }), `ResumeScope_Test_Results_${state.testResults.run_id}.csv`);
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function escapeQuote(str) {
  if (!str) return '';
  return String(str).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}
