/**
 * LLM Context Exporter Web Application
 * 
 * This application provides a web interface for exporting ChatGPT context
 * to Gemini or local LLMs via Ollama.
 */

class LLMContextExporter {
    constructor() {
        this.currentPage = 'welcome';
        this.uploadedFile = null;
        this.contextData = null;
        this.targetPlatform = null;
        this.baseModel = 'qwen';
        this.userEmail = '';
        this.exportId = null;
        this.stripe = null;
        this.paymentElement = null;
        this.isBetaUser = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeStripe();
        this.showPage('welcome');
    }

    setupEventListeners() {
        // Welcome page
        document.getElementById('get-started-btn').addEventListener('click', () => {
            this.showPage('upload');
        });

        // Upload page
        this.setupFileUpload();
        document.getElementById('back-to-welcome').addEventListener('click', () => {
            this.showPage('welcome');
        });
        document.getElementById('continue-to-target').addEventListener('click', () => {
            this.showPage('target');
        });

        // Target page
        this.setupTargetSelection();
        document.getElementById('back-to-upload').addEventListener('click', () => {
            this.showPage('upload');
        });
        document.getElementById('continue-to-review').addEventListener('click', () => {
            this.loadPreview();
        });

        // Review page
        this.setupReviewPage();
        document.getElementById('back-to-target').addEventListener('click', () => {
            this.showPage('target');
        });
        document.getElementById('continue-to-payment').addEventListener('click', () => {
            this.checkBetaStatus();
        });

        // Payment page
        this.setupPaymentPage();
        document.getElementById('back-to-review').addEventListener('click', () => {
            this.showPage('review');
        });

        // Results page
        this.setupResultsPage();
        document.getElementById('start-new-export').addEventListener('click', () => {
            this.resetApplication();
        });
    }

    setupFileUpload() {
        const uploadZone = document.getElementById('upload-zone');
        const fileInput = document.getElementById('file-input');

        // Click to upload
        uploadZone.addEventListener('click', () => {
            fileInput.click();
        });

        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });

        // Drag and drop
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            
            if (e.dataTransfer.files.length > 0) {
                this.handleFileUpload(e.dataTransfer.files[0]);
            }
        });
    }

    async handleFileUpload(file) {
        // Validate file type
        const allowedTypes = ['.zip', '.json'];
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExt)) {
            this.showToast('Invalid file type. Please upload a ZIP or JSON file.', 'error');
            return;
        }

        // Validate file size (500MB limit)
        if (file.size > 500 * 1024 * 1024) {
            this.showToast('File too large. Maximum size is 500MB.', 'error');
            return;
        }

        this.uploadedFile = file;
        this.showUploadProgress();

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.showUploadResult(result);
                document.getElementById('continue-to-target').disabled = false;
            } else {
                throw new Error(result.error || 'Upload failed');
            }
        } catch (error) {
            this.hideUploadProgress();
            this.showToast(`Upload failed: ${error.message}`, 'error');
        }
    }

    showUploadProgress() {
        document.getElementById('upload-progress').classList.remove('hidden');
        document.getElementById('upload-result').classList.add('hidden');
        
        // Simulate progress
        const progressFill = document.querySelector('.progress-fill');
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            progressFill.style.width = `${progress}%`;
        }, 200);

        // Store interval to clear it later
        this.progressInterval = interval;
    }

    hideUploadProgress() {
        document.getElementById('upload-progress').classList.add('hidden');
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
    }

    showUploadResult(result) {
        this.hideUploadProgress();
        
        document.getElementById('upload-result').classList.remove('hidden');
        document.getElementById('conversations-count').textContent = `${result.conversations_count} conversations`;
        document.getElementById('projects-count').textContent = `${result.projects_count} projects found`;
        
        this.showToast('Export processed successfully!', 'success');
    }

    setupTargetSelection() {
        const targetRadios = document.querySelectorAll('input[name="target"]');
        const ollamaOptions = document.getElementById('ollama-options');
        const continueBtn = document.getElementById('continue-to-review');

        targetRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.targetPlatform = e.target.value;
                continueBtn.disabled = false;

                if (e.target.value === 'ollama') {
                    ollamaOptions.classList.remove('hidden');
                } else {
                    ollamaOptions.classList.add('hidden');
                }
            });
        });

        document.getElementById('base-model-select').addEventListener('change', (e) => {
            this.baseModel = e.target.value;
        });
    }

    async loadPreview() {
        this.showLoading('Loading context preview...');

        try {
            const response = await fetch('/api/preview');
            const result = await response.json();

            if (result.success) {
                this.contextData = result.preview;
                this.populatePreview(result.preview);
                this.showPage('review');
            } else {
                throw new Error(result.error || 'Failed to load preview');
            }
        } catch (error) {
            this.showToast(`Failed to load preview: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    populatePreview(preview) {
        // User Profile
        const profileDiv = document.getElementById('profile-preview');
        profileDiv.innerHTML = `
            <div class="profile-info">
                <p><strong>Role:</strong> ${preview.user_profile.role || 'Not specified'}</p>
                <p><strong>Expertise Areas:</strong> ${preview.user_profile.expertise_areas.join(', ') || 'None identified'}</p>
                <p><strong>Background:</strong> ${preview.user_profile.background_summary || 'No background summary available'}</p>
            </div>
        `;

        // Projects
        const projectsDiv = document.getElementById('projects-preview');
        if (preview.projects.length === 0) {
            projectsDiv.innerHTML = '<p class="text-center">No projects found in your conversations.</p>';
        } else {
            projectsDiv.innerHTML = preview.projects.map((project, index) => `
                <div class="project-item" data-project-index="${index}">
                    <div class="project-header">
                        <input type="checkbox" class="project-checkbox" checked data-project-index="${index}">
                        <span class="project-name">${project.name}</span>
                    </div>
                    <p class="project-description">${project.description}</p>
                    <div class="project-meta">
                        <span>Tech: ${project.tech_stack.join(', ')}</span>
                        <span>Score: ${project.relevance_score.toFixed(2)}</span>
                        <span>Last: ${new Date(project.last_discussed).toLocaleDateString()}</span>
                    </div>
                </div>
            `).join('');
        }

        // Technical Context
        const technicalDiv = document.getElementById('technical-preview');
        technicalDiv.innerHTML = `
            <div class="technical-info">
                <p><strong>Languages:</strong> ${preview.technical_context.languages.join(', ') || 'None identified'}</p>
                <p><strong>Frameworks:</strong> ${preview.technical_context.frameworks.join(', ') || 'None identified'}</p>
                <p><strong>Tools:</strong> ${preview.technical_context.tools.join(', ') || 'None identified'}</p>
                <p><strong>Domains:</strong> ${preview.technical_context.domains.join(', ') || 'None identified'}</p>
            </div>
        `;

        // Setup project checkboxes
        this.setupProjectFiltering();
    }

    setupReviewPage() {
        // Select/Deselect all projects
        document.getElementById('select-all-projects').addEventListener('click', () => {
            document.querySelectorAll('.project-checkbox').forEach(cb => {
                cb.checked = true;
                cb.closest('.project-item').classList.remove('excluded');
            });
        });

        document.getElementById('deselect-all-projects').addEventListener('click', () => {
            document.querySelectorAll('.project-checkbox').forEach(cb => {
                cb.checked = false;
                cb.closest('.project-item').classList.add('excluded');
            });
        });

        // Relevance slider
        const relevanceSlider = document.getElementById('relevance-min');
        const relevanceValue = document.getElementById('relevance-value');
        
        relevanceSlider.addEventListener('input', (e) => {
            relevanceValue.textContent = e.target.value;
        });

        // Apply filters button
        document.getElementById('apply-filters').addEventListener('click', () => {
            this.applyFilters();
        });
    }

    setupProjectFiltering() {
        document.querySelectorAll('.project-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const projectItem = e.target.closest('.project-item');
                if (e.target.checked) {
                    projectItem.classList.remove('excluded');
                } else {
                    projectItem.classList.add('excluded');
                }
            });
        });
    }

    async applyFilters() {
        const excludedProjects = [];
        document.querySelectorAll('.project-checkbox:not(:checked)').forEach(cb => {
            excludedProjects.push(parseInt(cb.dataset.projectIndex));
        });

        const dateFrom = document.getElementById('date-from').value;
        const dateTo = document.getElementById('date-to').value;
        const minRelevance = parseFloat(document.getElementById('relevance-min').value);

        const filterConfig = {
            excluded_conversation_ids: [], // We'll implement this if needed
            excluded_topics: [], // We'll implement this if needed
            date_range: (dateFrom && dateTo) ? [dateFrom, dateTo] : null,
            min_relevance_score: minRelevance
        };

        this.showLoading('Applying filters...');

        try {
            const response = await fetch('/api/filter', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(filterConfig)
            });

            const result = await response.json();

            if (result.success) {
                this.showToast(`Filters applied. ${result.filtered_projects_count} projects remaining.`, 'success');
            } else {
                throw new Error(result.error || 'Failed to apply filters');
            }
        } catch (error) {
            this.showToast(`Failed to apply filters: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async checkBetaStatus() {
        const email = document.getElementById('user-email').value;
        if (!email) {
            this.showPage('payment');
            return;
        }

        try {
            const response = await fetch(`/api/beta/status?email=${encodeURIComponent(email)}`);
            const result = await response.json();

            if (result.success && result.is_beta_user) {
                this.isBetaUser = true;
                this.userEmail = email;
                this.showBetaNotice();
            } else {
                this.isBetaUser = false;
                this.showPage('payment');
            }
        } catch (error) {
            // If beta check fails, proceed to payment
            this.isBetaUser = false;
            this.showPage('payment');
        }
    }

    showBetaNotice() {
        this.showPage('payment');
        document.getElementById('beta-user-notice').classList.remove('hidden');
        document.getElementById('skip-payment').classList.remove('hidden');
        document.getElementById('pay-button').classList.add('hidden');
        
        document.getElementById('skip-payment').addEventListener('click', () => {
            this.generateOutput();
        });
    }

    setupPaymentPage() {
        const emailInput = document.getElementById('user-email');
        const payButton = document.getElementById('pay-button');

        emailInput.addEventListener('input', (e) => {
            this.userEmail = e.target.value;
            payButton.disabled = !this.isValidEmail(e.target.value);
        });

        payButton.addEventListener('click', () => {
            this.processPayment();
        });
    }

    async initializeStripe() {
        // Initialize Stripe (you'll need to set your publishable key)
        // For demo purposes, we'll skip Stripe initialization
        // In production, you would set: this.stripe = Stripe('pk_live_your_actual_key');
        console.log('Stripe initialization skipped for demo');
    }

    async processPayment() {
        if (this.isBetaUser) {
            this.generateOutput();
            return;
        }

        this.showLoading('Creating payment...');

        try {
            // Create payment intent
            const response = await fetch('/api/payment/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: this.userEmail
                })
            });

            const result = await response.json();

            if (result.success) {
                if (!result.payment_required) {
                    // Beta user
                    this.isBetaUser = true;
                    this.generateOutput();
                    return;
                }

                // Process payment with Stripe
                await this.handleStripePayment(result.payment_intent);
            } else {
                throw new Error(result.error || 'Failed to create payment');
            }
        } catch (error) {
            this.showToast(`Payment failed: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async handleStripePayment(paymentIntent) {
        // Demo mode: simulate successful payment
        // In production, you would integrate with Stripe Elements here
        
        this.showLoading('Processing payment...');
        
        // Show demo notice
        this.showToast('Demo Mode: Simulating payment processing...', 'warning');
        
        // Simulate payment processing delay
        setTimeout(async () => {
            try {
                // In demo mode, we'll just proceed to generation
                // In production, you would verify the actual payment
                this.showToast('Demo payment completed!', 'success');
                this.generateOutput();
            } catch (error) {
                this.showToast(`Payment simulation failed: ${error.message}`, 'error');
            } finally {
                this.hideLoading();
            }
        }, 2000);
    }

    async generateOutput() {
        this.showLoading('Generating your export...');

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    target_platform: this.targetPlatform,
                    base_model: this.baseModel
                })
            });

            const result = await response.json();

            if (result.success) {
                this.exportId = result.export_id;
                this.showResults(result);
            } else {
                throw new Error(result.error || 'Generation failed');
            }
        } catch (error) {
            this.showToast(`Generation failed: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    showResults(result) {
        this.showPage('results');
        
        // Update platform name
        document.getElementById('target-platform-name').textContent = 
            this.targetPlatform === 'gemini' ? 'Google Gemini' : 'Ollama';

        // Update stats
        document.getElementById('final-projects-count').textContent = 
            this.contextData?.projects?.length || 0;
        document.getElementById('files-generated-count').textContent = 
            result.files_generated.length;

        // Setup download
        this.setupDownload();

        // Show platform-specific sections
        if (this.targetPlatform === 'gemini') {
            document.getElementById('gemini-copy-section').classList.remove('hidden');
            this.setupGeminiCopy();
        }

        // Setup instructions
        this.setupInstructions();

        // Load validation questions
        this.loadValidationQuestions();

        // Show feedback form for beta users
        if (this.isBetaUser) {
            document.getElementById('feedback-section').classList.remove('hidden');
            this.setupFeedbackForm();
        }
    }

    setupDownload() {
        document.getElementById('download-zip').addEventListener('click', () => {
            if (this.exportId) {
                window.location.href = `/api/download/${this.exportId}`;
            }
        });
    }

    setupGeminiCopy() {
        document.getElementById('copy-gemini-text').addEventListener('click', async () => {
            try {
                // In a real implementation, you'd fetch the actual Gemini text
                const text = "Your Gemini context text would be here...";
                await navigator.clipboard.writeText(text);
                this.showToast('Gemini text copied to clipboard!', 'success');
            } catch (error) {
                this.showToast('Failed to copy text', 'error');
            }
        });
    }

    setupInstructions() {
        const instructionsDiv = document.getElementById('setup-instructions');
        
        if (this.targetPlatform === 'gemini') {
            instructionsDiv.innerHTML = `
                <ol>
                    <li>Go to <a href="https://gemini.google.com" target="_blank">Gemini</a></li>
                    <li>Click on your profile picture in the top right</li>
                    <li>Select "Saved Info" from the menu</li>
                    <li>Click "Add info about you"</li>
                    <li>Paste the copied text or upload the text file</li>
                    <li>Save your information</li>
                </ol>
            `;
        } else {
            instructionsDiv.innerHTML = `
                <ol>
                    <li>Make sure <a href="https://ollama.ai" target="_blank">Ollama</a> is installed</li>
                    <li>Extract the downloaded ZIP file</li>
                    <li>Open terminal in the extracted folder</li>
                    <li>Run: <code>ollama create my-context -f Modelfile</code></li>
                    <li>Test with: <code>ollama run my-context "Tell me about my projects"</code></li>
                </ol>
            `;
        }
    }

    async loadValidationQuestions() {
        try {
            const response = await fetch('/api/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    target_platform: this.targetPlatform
                })
            });

            const result = await response.json();

            if (result.success) {
                this.displayValidationQuestions(result.validation_suite.questions);
            }
        } catch (error) {
            console.error('Failed to load validation questions:', error);
        }
    }

    displayValidationQuestions(questions) {
        const questionsDiv = document.getElementById('validation-questions');
        
        if (questions.length === 0) {
            questionsDiv.innerHTML = '<p>No validation questions available.</p>';
            return;
        }

        questionsDiv.innerHTML = questions.slice(0, 5).map(q => `
            <div class="validation-question">
                <div class="question-text">${q.question}</div>
                <div class="expected-answer">Expected: ${q.expected_answer_summary}</div>
            </div>
        `).join('');
    }

    setupFeedbackForm() {
        document.getElementById('feedback-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const rating = document.querySelector('input[name="rating"]:checked')?.value;
            const feedback = document.getElementById('feedback-text').value;

            if (!rating) {
                this.showToast('Please provide a rating', 'warning');
                return;
            }

            try {
                const response = await fetch('/api/beta/feedback', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email: this.userEmail,
                        rating: parseInt(rating),
                        feedback: feedback
                    })
                });

                const result = await response.json();

                if (result.success) {
                    this.showToast('Thank you for your feedback!', 'success');
                    document.getElementById('feedback-section').style.opacity = '0.5';
                } else {
                    throw new Error(result.error || 'Failed to submit feedback');
                }
            } catch (error) {
                this.showToast(`Failed to submit feedback: ${error.message}`, 'error');
            }
        });
    }

    setupResultsPage() {
        // Results page is set up in showResults method
    }

    // Utility methods
    showPage(pageId) {
        // Hide all pages
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });

        // Show target page
        document.getElementById(`${pageId}-page`).classList.add('active');
        this.currentPage = pageId;

        // Scroll to top
        window.scrollTo(0, 0);
    }

    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loading-overlay');
        const messageEl = overlay.querySelector('.loading-message');
        messageEl.textContent = message;
        overlay.classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loading-overlay').classList.add('hidden');
    }

    showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        toast.innerHTML = `
            <div class="toast-title">${type === 'error' ? 'Error' : type === 'warning' ? 'Warning' : 'Success'}</div>
            <div class="toast-message">${message}</div>
        `;

        container.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    resetApplication() {
        // Reset all state
        this.uploadedFile = null;
        this.contextData = null;
        this.targetPlatform = null;
        this.baseModel = 'qwen';
        this.userEmail = '';
        this.exportId = null;
        this.isBetaUser = false;

        // Reset form elements
        document.getElementById('file-input').value = '';
        document.querySelectorAll('input[name="target"]').forEach(radio => {
            radio.checked = false;
        });
        document.getElementById('user-email').value = '';
        document.getElementById('feedback-text').value = '';
        document.querySelectorAll('input[name="rating"]').forEach(radio => {
            radio.checked = false;
        });

        // Hide dynamic elements
        document.getElementById('upload-progress').classList.add('hidden');
        document.getElementById('upload-result').classList.add('hidden');
        document.getElementById('ollama-options').classList.add('hidden');
        document.getElementById('beta-user-notice').classList.add('hidden');
        document.getElementById('skip-payment').classList.add('hidden');
        document.getElementById('gemini-copy-section').classList.add('hidden');
        document.getElementById('feedback-section').classList.add('hidden');

        // Reset buttons
        document.getElementById('continue-to-target').disabled = true;
        document.getElementById('continue-to-review').disabled = true;
        document.getElementById('pay-button').disabled = true;

        // Go back to welcome page
        this.showPage('welcome');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new LLMContextExporter();
});