/**
 * Simple Kanban Board - Frontend Application
 * Handles board management, task operations, and drag-and-drop functionality
 */

class KanbanApp {
    constructor() {
        Debug.log('KanbanApp constructor called');
        this.currentBoard = null;
        this.boards = [];
        this.columns = [];
        this.tasks = [];
        this.draggedTask = null;
        this.authManager = window.authManager;
        
        // WebSocket for real-time updates
        this.ws = null;
        this.wsReconnectAttempts = 0;
        this.wsMaxReconnectAttempts = 5;
        this.wsReconnectDelay = 1000;
    }

    async init() {
        Debug.log('init() called - authenticated user');
        this.bindEvents();
        Debug.log('Events bound, loading boards...');
        await this.loadBoards();
        Debug.log('Boards loaded, hiding loading...');
        this.hideLoading();
        Debug.log('init() complete');
    }

    bindEvents() {
        // Board management
        document.getElementById('new-board-btn').addEventListener('click', () => this.showBoardModal());
        document.getElementById('create-first-board').addEventListener('click', () => this.showBoardModal());
        document.getElementById('board-select').addEventListener('change', (e) => this.selectBoard(e.target.value));
        document.getElementById('edit-board-btn').addEventListener('click', () => this.editCurrentBoard());

        // Board modal
        document.getElementById('board-modal-close').addEventListener('click', () => this.hideBoardModal());
        document.getElementById('board-cancel').addEventListener('click', () => this.hideBoardModal());
        document.getElementById('board-form').addEventListener('submit', (e) => this.handleBoardSubmit(e));
        document.getElementById('board-delete').addEventListener('click', () => this.deleteCurrentBoard());

        // Column modal
        document.getElementById('add-column-btn').addEventListener('click', () => this.showColumnModal());
        document.getElementById('column-modal-close').addEventListener('click', () => this.hideColumnModal());
        document.getElementById('column-cancel').addEventListener('click', () => this.hideColumnModal());
        document.getElementById('column-form').addEventListener('submit', (e) => this.handleColumnSubmit(e));

        // Task modal
        document.getElementById('task-modal-close').addEventListener('click', () => this.hideTaskModal());
        document.getElementById('task-cancel').addEventListener('click', () => this.hideTaskModal());
        document.getElementById('task-form').addEventListener('submit', (e) => this.handleTaskSubmit(e));

        // Notification
        document.getElementById('notification-close').addEventListener('click', () => this.hideNotification());

        // Close modals on backdrop click
        document.getElementById('board-modal').addEventListener('click', (e) => {
            if (e.target.id === 'board-modal') this.hideBoardModal();
        });
        document.getElementById('column-modal').addEventListener('click', (e) => {
            if (e.target.id === 'column-modal') this.hideColumnModal();
        });
        document.getElementById('task-modal').addEventListener('click', (e) => {
            if (e.target.id === 'task-modal') this.hideTaskModal();
        });
    }

    // API Methods
    async apiCall(endpoint, options = {}) {
        try {
            Debug.log('Making API call to:', `/api${endpoint}`, options);
            
            let response;
            
            // Use authenticated fetch if auth manager is available
            if (this.authManager && this.authManager.token) {
                Debug.log('Using authenticated fetch with token:', this.authManager.token ? 'present' : 'missing');
                response = await this.authManager.authenticatedFetch(`/api${endpoint}`, {
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    ...options
                });
            } else {
                Debug.log('Using fallback fetch - authManager:', !!this.authManager, 'token:', this.authManager?.token ? 'present' : 'missing');
                // Fallback to regular fetch with credentials
                response = await fetch(`/api${endpoint}`, {
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    ...options
                });
            }
            
            Debug.log('API Response status:', response.status, response.statusText, 'for endpoint:', endpoint);
            
            if (!response.ok) {
                let errorMessage = `HTTP ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                    Debug.error('API Error details:', errorData);
                } catch (parseError) {
                    Debug.error('Failed to parse error response:', parseError);
                    const errorText = await response.text();
                    Debug.error('Error response text:', errorText);
                }
                throw new Error(errorMessage);
            }
            
            // Handle empty responses (like DELETE operations)
            const contentType = response.headers.get('content-type');
            if (response.status === 204 || !contentType || !contentType.includes('application/json')) {
                return null;
            }
            
            const data = await response.json();
            Debug.log('API Response data:', data);
            return data;
        } catch (error) {
            Debug.error('API Error:', error);
            this.showNotification(error.message || 'Unknown API error', 'error');
            throw error;
        }
    }

    // Board Management
    async loadBoards() {
        try {
            Debug.log('Loading boards...');
            const response = await this.apiCall('/boards/');
            Debug.log('Boards API response:', response);
            
            // Ensure we have an array
            this.boards = Array.isArray(response) ? response : [];
            Debug.log('Boards loaded:', this.boards);
            
            // Debug: Check if boards array is empty
            if (this.boards.length === 0) {
                Debug.warn('No boards found in the array');
            } else {
                Debug.log(`Found ${this.boards.length} boards`);
                this.boards.forEach((board, index) => {
                    Debug.log(`Board ${index + 1}:`, board);
                });
            }
            
            // Update the board selector dropdown
            this.updateBoardSelector();
            
            if (this.boards.length === 0) {
                Debug.log('No boards found, showing empty state');
                this.showEmptyState();
            } else {
                // Try to restore previously selected board from localStorage
                const savedBoardId = localStorage.getItem('selectedBoardId');
                Debug.log('Saved board ID from localStorage:', savedBoardId);
                let boardToSelect = null;
                
                if (savedBoardId) {
                    // Check if saved board still exists
                    boardToSelect = this.boards.find(board => board.id == savedBoardId);
                    Debug.log('Found saved board:', boardToSelect);
                }
                
                // Fall back to first board if saved board not found
                if (!boardToSelect) {
                    boardToSelect = this.boards[0];
                    Debug.log('Using first board:', boardToSelect);
                }
                
                // Always select the determined board (either saved or first)
                Debug.log('Selecting board:', boardToSelect);
                if (boardToSelect && boardToSelect.id) {
                    Debug.log('Calling selectBoard with id:', boardToSelect.id);
                    await this.selectBoard(boardToSelect.id);
                } else {
                    Debug.error('Invalid board to select:', boardToSelect);
                }
            }
        } catch (error) {
            Debug.error('Error loading boards:', error);
            // Initialize boards as empty array on error
            this.boards = [];
            this.showEmptyState();
        }
    }

    updateBoardSelector() {
        Debug.log('updateBoardSelector() called');
        Debug.log('Current boards array:', this.boards);
        
        const select = document.getElementById('board-select');
        if (!select) {
            Debug.error('Board select element not found!');
            return;
        }
        
        // Clear existing options
        select.innerHTML = '<option value="">Select a board...</option>';
        
        // Ensure boards is an array before using forEach
        if (!Array.isArray(this.boards)) {
            Debug.error('this.boards is not an array:', this.boards);
            return;
        }
        
        Debug.log(`Adding ${this.boards.length} boards to selector`);
        this.boards.forEach((board, index) => {
            Debug.log(`Adding board ${index + 1}:`, board);
            const option = document.createElement('option');
            option.value = board.id;
            option.textContent = board.name || `Untitled Board ${board.id}`;
            select.appendChild(option);
        });
        
        Debug.log('Updated board selector with options:', select.innerHTML);
    }

    async selectBoard(boardId) {
        Debug.log('selectBoard() called with boardId:', boardId);
        if (!boardId) {
            Debug.warn('No boardId provided to selectBoard');
            return;
        }
        
        try {
            this.showLoading();
            Debug.log('Fetching board details for ID:', boardId);
            const board = await this.apiCall(`/boards/${boardId}`);
            Debug.log('Received board details:', board);
            
            if (!board) {
                throw new Error('No board data returned from API');
            }
            
            this.currentBoard = board;
            Debug.log('Current board set to:', this.currentBoard);
            
            // Update the board selector
            const boardSelect = document.getElementById('board-select');
            if (boardSelect) {
                boardSelect.value = boardId;
                Debug.log('Updated board select element value to:', boardId);
            } else {
                Debug.warn('Board select element not found');
            }
            
            // Save selected board to localStorage
            localStorage.setItem('selectedBoardId', boardId);
            Debug.log('Saved selectedBoardId to localStorage');
            
            // Connect to WebSocket for real-time updates
            this.connectWebSocket(boardId);
            
            // Process the board data we already have
            Debug.log('Processing board data...');
            await this.processBoardData(board);
            Debug.log('Rendering board...');
            this.renderBoard();
            
            this.hideLoading();
            Debug.log('Board selection complete');
        } catch (error) {
            Debug.error('Failed to load board:', error);
            this.hideLoading();
            
            // Show error to user
            this.showNotification('Failed to load board. Please try again.');
            
            // Try to load the first available board if this one fails
            if (this.boards && this.boards.length > 0) {
                Debug.log('Attempting to load first available board...');
                const firstBoard = this.boards[0];
                if (firstBoard && firstBoard.id !== boardId) {
                    Debug.log('Loading first available board instead:', firstBoard);
                    await this.selectBoard(firstBoard.id);
                }
            }
        }
    }

    async processBoardData(board) {
        if (!board) return;

        try {
            // Use the columns and tasks from the board data
            this.columns = board.columns || [];
            
            // Extract tasks from columns
            this.tasks = [];
            for (const column of this.columns) {
                if (column.tasks) {
                    column.tasks.forEach(task => {
                        task.column_id = column.id;
                        this.tasks.push(task);
                    });
                }
            }
            
            Debug.log('Processed board data:', {
                columns: this.columns,
                tasks: this.tasks
            });
        } catch (error) {
            Debug.error('Failed to process board data:', error);
            throw error; // Re-throw to be caught by the caller
        }
    }
    
    // Keep loadBoardData for backward compatibility
    async loadBoardData() {
        if (!this.currentBoard) return;
        
        try {
            // If we already have columns with tasks, use them
            if (this.currentBoard.columns) {
                await this.processBoardData(this.currentBoard);
            } else {
                // Fallback to API call if needed
                const board = await this.apiCall(`/boards/${this.currentBoard.id}`);
                await this.processBoardData(board);
            }
        } catch (error) {
            Debug.error('Failed to load board data:', error);
            throw error; // Re-throw to be caught by the caller
        }
    }

    // Always fetch fresh board data from API
    async refreshBoardData() {
        if (!this.currentBoard) return;
        
        try {
            Debug.log('Refreshing board data from API...');
            const board = await this.apiCall(`/boards/${this.currentBoard.id}`);
            this.currentBoard = board; // Update current board with fresh data
            await this.processBoardData(board);
            this.renderBoard();
            Debug.log('Board data refreshed and rendered');
        } catch (error) {
            Debug.error('Failed to refresh board data:', error);
            throw error;
        }
    }

    renderBoard() {
        Debug.log('renderBoard() called');
        Debug.log('Current board:', this.currentBoard);
        Debug.log('Columns to render:', this.columns);
        
        // Update board header
        document.getElementById('board-title').textContent = this.currentBoard.name;
        document.getElementById('board-description').textContent = this.currentBoard.description || '';

        // Render columns
        const container = document.getElementById('columns-container');
        Debug.log('Columns container:', container);
        container.innerHTML = '';

        this.columns.forEach(column => {
            Debug.log('Creating column element for:', column);
            const columnElement = this.createColumnElement(column);
            container.appendChild(columnElement);
        });
        
        Debug.log('Board rendered, calling showBoard()');
        this.showBoard();
    }

    createColumnElement(column) {
        const columnTasks = this.tasks.filter(task => task.column_id === column.id);
        
        const columnDiv = document.createElement('div');
        columnDiv.className = 'column';
        columnDiv.dataset.columnId = column.id;
        
        columnDiv.innerHTML = `
            <div class="column-header">
                <div class="column-title">
                    ${column.name}
                    <span class="task-count">${columnTasks.length}</span>
                </div>
                <button class="add-task-btn" data-column-id="${column.id}">
                    <i class="fas fa-plus"></i>
                </button>
            </div>
            <div class="tasks-list" data-column-id="${column.id}">
                ${columnTasks.map(task => this.createTaskHTML(task)).join('')}
            </div>
        `;

        // Add event listeners
        columnDiv.querySelector('.add-task-btn').addEventListener('click', () => {
            this.showTaskModal(column.id);
        });

        // Make column droppable
        const tasksList = columnDiv.querySelector('.tasks-list');
        this.makeDroppable(tasksList);

        return columnDiv;
    }

    createTaskHTML(task) {
        const createdDate = task.created_at ? new Date(task.created_at).toLocaleDateString() : 'Recently';
        const daysOpen = this.calculateDaysOpen(task.created_at);
        
        // Build tags HTML
        const tagsHTML = task.tags && task.tags.length > 0 
            ? `<div class="task-tags">${task.tags.map(tag => `<span class="task-tag">${this.escapeHtml(tag)}</span>`).join('')}</div>` 
            : '';
        
        // Build priority badge
        const priorityHTML = task.priority && task.priority !== 'medium'
            ? `<span class="task-priority priority-${task.priority}">${task.priority}</span>`
            : '';
        
        // Build steps progress
        let stepsHTML = '';
        if (task.steps && task.steps.length > 0) {
            const completed = task.steps.filter(s => s.completed).length;
            const total = task.steps.length;
            const percent = Math.round((completed / total) * 100);
            stepsHTML = `
                <div class="task-steps">
                    <div class="steps-progress">
                        <div class="steps-bar" style="width: ${percent}%"></div>
                    </div>
                    <span class="steps-count">${completed}/${total}</span>
                </div>`;
        }
        
        // Build results indicator
        const resultsHTML = task.results && task.results.status
            ? `<span class="task-result result-${task.results.status}" title="${this.escapeHtml(task.results.summary || '')}">
                <i class="fas fa-${task.results.status === 'success' ? 'check-circle' : task.results.status === 'failed' ? 'times-circle' : 'exclamation-circle'}"></i>
               </span>`
            : '';
        
        return `
            <div class="task-card clickable" draggable="true" data-task-id="${task.id}" data-priority="${task.priority || 'medium'}">
                <div class="task-header">
                    <div class="task-title">${this.escapeHtml(task.title)}</div>
                    ${priorityHTML}${resultsHTML}
                </div>
                ${tagsHTML}
                ${task.description ? `<div class="task-description">${this.escapeHtml(task.description)}</div>` : ''}
                ${stepsHTML}
                <div class="task-meta">
                    <span>Created: ${createdDate}</span>
                    <span class="days-open ${this.getDaysOpenClass(daysOpen)}">${daysOpen}</span>
                    <div class="task-actions">
                        <button class="task-action delete" data-task-id="${task.id}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    calculateDaysOpen(createdAt) {
        if (!createdAt) return 'New';
        
        const created = new Date(createdAt);
        const now = new Date();
        const diffTime = Math.abs(now - created);
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return '1 day';
        return `${diffDays} days`;
    }

    getDaysOpenClass(daysText) {
        if (daysText === 'New' || daysText === 'Today') return 'days-new';
        
        const days = parseInt(daysText);
        if (isNaN(days)) return 'days-new';
        if (days <= 3) return 'days-fresh';
        if (days <= 7) return 'days-aging';
        return 'days-stale';
    }

    // Drag and Drop
    makeDroppable(element) {
        element.addEventListener('dragover', this.handleDragOver.bind(this));
        element.addEventListener('drop', this.handleDrop.bind(this));
        element.addEventListener('dragenter', this.handleDragEnter.bind(this));
        element.addEventListener('dragleave', this.handleDragLeave.bind(this));

        // Add drag listeners to existing tasks
        element.querySelectorAll('.task-card').forEach(taskCard => {
            this.makeDraggable(taskCard);
        });
    }

    makeDraggable(taskCard) {
        taskCard.addEventListener('dragstart', this.handleDragStart.bind(this));
        taskCard.addEventListener('dragend', this.handleDragEnd.bind(this));
        
        // Add click listener to open edit modal
        taskCard.addEventListener('click', (e) => {
            // Don't trigger if clicking on action buttons
            if (e.target.closest('.task-action')) {
                return;
            }
            this.editTask(taskCard.dataset.taskId);
        });
        
        // Add task action listeners
        const deleteBtn = taskCard.querySelector('.task-action.delete');
        
        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteTask(taskCard.dataset.taskId);
            });
        }
    }

    handleDragStart(e) {
        this.draggedTask = e.target;
        e.target.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', e.target.outerHTML);
    }

    handleDragEnd(e) {
        e.target.classList.remove('dragging');
        this.draggedTask = null;
    }

    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }

    handleDragEnter(e) {
        e.preventDefault();
        if (e.target.classList.contains('tasks-list')) {
            e.target.parentElement.classList.add('drag-over');
        }
    }

    handleDragLeave(e) {
        if (e.target.classList.contains('tasks-list')) {
            e.target.parentElement.classList.remove('drag-over');
        }
    }

    async handleDrop(e) {
        e.preventDefault();
        
        if (!this.draggedTask) return;
        
        const tasksList = e.target.closest('.tasks-list');
        if (!tasksList) return;
        
        const newColumnId = parseInt(tasksList.dataset.columnId);
        const taskId = parseInt(this.draggedTask.dataset.taskId);
        
        // Remove drag-over class
        tasksList.parentElement.classList.remove('drag-over');
        
        try {
            // Calculate new position (add to end of target column)
            const targetColumnTasks = this.tasks.filter(t => t.column_id === newColumnId);
            const newPosition = targetColumnTasks.length;
            
            // Update task column via API using the move endpoint
            await this.apiCall(`/tasks/${taskId}/move`, {
                method: 'POST',
                body: JSON.stringify({
                    column_id: newColumnId,
                    position: newPosition
                })
            });
            
            // Refresh board data to reflect the move
            await this.refreshBoardData();
            this.showNotification('Task moved successfully!');
            
        } catch (error) {
            Debug.error('Failed to move task:', error);
            this.showNotification('Failed to move task. Please try again.', 'error');
        }
    }

    // Task Management
    showTaskModal(columnId = null, task = null) {
        const modal = document.getElementById('task-modal');
        const form = document.getElementById('task-form');
        const submitBtn = document.getElementById('task-submit');
        const detailsSection = document.getElementById('task-details-section');

        modal.style.display = '';
        modal.style.pointerEvents = '';
        
        if (task) {
            // Edit mode
            submitBtn.textContent = 'Update Task';
            document.getElementById('task-title').value = task.title;
            document.getElementById('task-desc').value = task.description || '';
            document.getElementById('task-id').value = task.id;
            document.getElementById('task-column-id').value = task.column_id;
            
            // Show task details section and populate it
            this.populateTaskDetails(task);
            detailsSection.style.display = 'block';
            
            // Load comments for this task
            this.loadTaskComments(task.id);
        } else {
            // Create mode
            submitBtn.textContent = 'Create Task';
            form.reset();
            document.getElementById('task-column-id').value = columnId;
            document.getElementById('task-id').value = '';
            
            // Hide task details section
            detailsSection.style.display = 'none';
            
            // Clear comments section
            this.clearComments();
        }
        
        // Setup comment form event listener
        this.setupCommentForm();
        
        modal.classList.add('show');
    }
    
    populateTaskDetails(task) {
        // Store current task for editing
        this.currentEditTask = task;
        this.currentTags = task.tags ? [...task.tags] : [];
        this.currentSteps = task.steps ? task.steps.map(s => ({...s})) : [];
        
        // Tags (editable)
        this.renderTagsEditor();
        this.setupTagsEditor();
        
        // Priority (editable dropdown) - auto-save on change
        const prioritySelect = document.getElementById('task-priority-select');
        prioritySelect.value = task.priority || 'medium';
        // Remove old listener and add new one
        const newPrioritySelect = prioritySelect.cloneNode(true);
        prioritySelect.parentNode.replaceChild(newPrioritySelect, prioritySelect);
        newPrioritySelect.value = task.priority || 'medium';
        newPrioritySelect.addEventListener('change', () => this.autoSaveTask());
        
        // Steps (editable)
        this.renderStepsEditor();
        this.setupStepsEditor();
        
        // Results
        const resultsEl = document.getElementById('task-detail-results');
        const resultsSection = document.querySelector('.detail-results-section');
        if (task.results && Object.keys(task.results).length > 0) {
            const statusIcon = task.results.status === 'success' ? 'check-circle' : 
                              task.results.status === 'failed' ? 'times-circle' : 'exclamation-circle';
            resultsEl.innerHTML = `
                <div class="results-header result-${task.results.status || 'pending'}">
                    <i class="fas fa-${statusIcon}"></i>
                    <span>${task.results.status || 'Pending'}</span>
                </div>
                ${task.results.summary ? `<div class="results-summary">${this.escapeHtml(task.results.summary)}</div>` : ''}
                ${task.results.output ? `<pre class="results-output">${this.escapeHtml(task.results.output)}</pre>` : ''}`;
            resultsSection.style.display = 'flex';
        } else {
            resultsEl.innerHTML = '';
            resultsSection.style.display = 'none';
        }
        
        // Metadata
        const metadataEl = document.getElementById('task-detail-metadata');
        const metadataSection = document.querySelector('.detail-metadata-section');
        if (task.task_metadata && Object.keys(task.task_metadata).length > 0) {
            metadataEl.innerHTML = `<pre class="metadata-json">${JSON.stringify(task.task_metadata, null, 2)}</pre>`;
            metadataSection.style.display = 'flex';
        } else {
            metadataEl.innerHTML = '';
            metadataSection.style.display = 'none';
        }
    }

    // Tags Editor Methods
    renderTagsEditor() {
        const tagsList = document.getElementById('task-tags-list');
        tagsList.innerHTML = this.currentTags.map(tag => `
            <span class="tag-chip" data-tag="${this.escapeHtml(tag)}">
                ${this.escapeHtml(tag)}
                <button type="button" class="tag-remove" data-tag="${this.escapeHtml(tag)}">
                    <i class="fas fa-times"></i>
                </button>
            </span>
        `).join('');
    }

    setupTagsEditor() {
        const tagInput = document.getElementById('tag-input');
        const suggestions = document.getElementById('tag-suggestions');
        const tagsList = document.getElementById('task-tags-list');

        // Remove existing listeners by cloning
        const newInput = tagInput.cloneNode(true);
        tagInput.parentNode.replaceChild(newInput, tagInput);

        const newSuggestions = suggestions.cloneNode(true);
        suggestions.parentNode.replaceChild(newSuggestions, suggestions);

        const newTagsList = tagsList.cloneNode(true);
        tagsList.parentNode.replaceChild(newTagsList, tagsList);

        // Input handler for autocomplete
        newInput.addEventListener('input', (e) => {
            const value = e.target.value.trim().toLowerCase();
            if (value.length < 1) {
                newSuggestions.innerHTML = '';
                newSuggestions.style.display = 'none';
                return;
            }
            const allTags = this.getAllUsedTags();
            const matches = allTags.filter(t => 
                t.toLowerCase().includes(value) && !this.currentTags.includes(t)
            ).slice(0, 5);
            
            if (matches.length > 0) {
                newSuggestions.innerHTML = matches.map(t => 
                    `<div class="tag-suggestion" data-tag="${this.escapeHtml(t)}">${this.escapeHtml(t)}</div>`
                ).join('');
                newSuggestions.style.display = 'block';
            } else {
                newSuggestions.style.display = 'none';
            }
        });

        // Enter key to add tag - auto-save
        newInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const value = e.target.value.trim();
                if (value && !this.currentTags.includes(value)) {
                    this.currentTags.push(value);
                    this.renderTagsEditor();
                    e.target.value = '';
                    newSuggestions.style.display = 'none';
                    this.autoSaveTask();
                }
            }
        });

        // Click suggestion - auto-save
        newSuggestions.addEventListener('click', (e) => {
            const suggestion = e.target.closest('.tag-suggestion');
            if (suggestion) {
                const tag = suggestion.dataset.tag;
                if (!this.currentTags.includes(tag)) {
                    this.currentTags.push(tag);
                    this.renderTagsEditor();
                    this.autoSaveTask();
                }
                newInput.value = '';
                newSuggestions.style.display = 'none';
            }
        });

        // Remove tag - auto-save
        newTagsList.addEventListener('click', (e) => {
            const removeBtn = e.target.closest('.tag-remove');
            if (removeBtn) {
                const tag = removeBtn.dataset.tag;
                this.currentTags = this.currentTags.filter(t => t !== tag);
                this.renderTagsEditor();
                this.autoSaveTask();
            }
        });

        newInput.addEventListener('blur', () => {
            setTimeout(() => { newSuggestions.style.display = 'none'; }, 200);
        });
    }

    getAllUsedTags() {
        const tags = new Set();
        this.tasks.forEach(task => {
            if (task.tags) task.tags.forEach(t => tags.add(t));
        });
        return Array.from(tags).sort();
    }

    renderStepsEditor() {
        const stepsList = document.getElementById('task-steps-list');
        stepsList.innerHTML = this.currentSteps.map((step, idx) => `
            <div class="step-item" data-index="${idx}" draggable="true">
                <span class="step-drag-handle"><i class="fas fa-grip-vertical"></i></span>
                <input type="checkbox" class="step-checkbox" ${step.completed ? 'checked' : ''} data-index="${idx}">
                <input type="text" class="step-text" value="${this.escapeHtml(step.step || '')}" data-index="${idx}" placeholder="Step description...">
                <button type="button" class="step-remove" data-index="${idx}">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `).join('');
    }

    setupStepsEditor() {
        const stepsList = document.getElementById('task-steps-list');
        const addBtn = document.getElementById('add-step-btn');

        const newStepsList = stepsList.cloneNode(true);
        stepsList.parentNode.replaceChild(newStepsList, stepsList);

        const newAddBtn = addBtn.cloneNode(true);
        addBtn.parentNode.replaceChild(newAddBtn, addBtn);

        newAddBtn.addEventListener('click', () => {
            this.currentSteps.push({ step: '', completed: false, completed_at: null });
            this.renderStepsEditor();
            const inputs = newStepsList.querySelectorAll('.step-text');
            if (inputs.length > 0) inputs[inputs.length - 1].focus();
        });

        newStepsList.addEventListener('input', (e) => {
            if (e.target.classList.contains('step-text')) {
                const idx = parseInt(e.target.dataset.index);
                this.currentSteps[idx].step = e.target.value;
            }
        });

        newStepsList.addEventListener('change', (e) => {
            if (e.target.classList.contains('step-checkbox')) {
                const idx = parseInt(e.target.dataset.index);
                this.currentSteps[idx].completed = e.target.checked;
                this.currentSteps[idx].completed_at = e.target.checked ? new Date().toISOString() : null;
                this.autoSaveTask();
            }
        });

        newStepsList.addEventListener('focusout', (e) => {
            if (e.target.classList.contains('step-text')) {
                this.autoSaveTask();
            }
        });

        newStepsList.addEventListener('click', (e) => {
            const removeBtn = e.target.closest('.step-remove');
            if (removeBtn) {
                const idx = parseInt(removeBtn.dataset.index);
                this.currentSteps.splice(idx, 1);
                this.renderStepsEditor();
                this.autoSaveTask();
            }
        });

        let draggedIdx = null;
        newStepsList.addEventListener('dragstart', (e) => {
            const item = e.target.closest('.step-item');
            if (item) {
                draggedIdx = parseInt(item.dataset.index);
                item.classList.add('dragging');
            }
        });

        newStepsList.addEventListener('dragend', (e) => {
            const item = e.target.closest('.step-item');
            if (item) item.classList.remove('dragging');
            draggedIdx = null;
        });

        newStepsList.addEventListener('dragover', (e) => {
            if (draggedIdx === null) return;
            e.preventDefault();
        });

        newStepsList.addEventListener('drop', (e) => {
            if (draggedIdx === null) return;
            e.preventDefault();

            const item = e.target.closest('.step-item');
            if (!item) return;

            const targetIdx = parseInt(item.dataset.index);
            if (Number.isNaN(targetIdx) || targetIdx === draggedIdx) return;

            const [moved] = this.currentSteps.splice(draggedIdx, 1);
            this.currentSteps.splice(targetIdx, 0, moved);
            this.renderStepsEditor();
            this.autoSaveTask();
        });
    }

    hideTaskModal() {
        const modal = document.getElementById('task-modal');
        modal.classList.remove('show');
        modal.style.display = 'none';
        modal.style.pointerEvents = 'none';

        document.querySelectorAll('.dragging').forEach(el => el.classList.remove('dragging'));
        document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
        this.draggedTask = null;
    }

    async autoSaveTask() {
        const taskId = document.getElementById('task-id')?.value;
        if (!taskId) return;
        
        const priorityEl = document.getElementById('task-priority-select');
        const columnIdEl = document.getElementById('task-column-id');
        if (!priorityEl) return;
        
        const columnId = parseInt(
            columnIdEl?.value || this.currentEditTask?.column_id || '0'
        );
        if (!columnId) return;
        
        const taskData = {
            title: document.getElementById('task-title')?.value || '',
            description: document.getElementById('task-desc')?.value || null,
            column_id: columnId,
            tags: this.currentTags || [],
            priority: priorityEl.value || 'medium',
            steps: (this.currentSteps || []).filter(s => s.step && s.step.trim())
        };
        
        try {
            const updatedTask = await this.apiCall(`/tasks/${taskId}`, {
                method: 'PUT',
                body: JSON.stringify(taskData)
            });

            const idx = this.tasks.findIndex(t => t.id === parseInt(taskId));
            if (idx !== -1) this.tasks[idx] = updatedTask;
            this.currentEditTask = updatedTask;

            const oldCard = document.querySelector(`.task-card[data-task-id="${taskId}"]`);
            if (oldCard) {
                const wrapper = document.createElement('div');
                wrapper.innerHTML = this.createTaskHTML(updatedTask).trim();
                const newCard = wrapper.firstElementChild;
                if (newCard) {
                    oldCard.replaceWith(newCard);
                    this.makeDraggable(newCard);
                }
            }
        } catch (error) {
            Debug.error('Auto-save failed:', error);
        }
    }

    async handleTaskSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const taskId = formData.get('id');

        const taskData = {
            title: formData.get('title') || '',
            description: formData.get('description') || null,
            column_id: parseInt(formData.get('column_id'))
        };

        if (taskId) {
            taskData.tags = this.currentTags || [];
            taskData.priority = document.getElementById('task-priority-select')?.value || 'medium';
            taskData.steps = (this.currentSteps || []).filter(s => s.step && s.step.trim());
        }
        
        try {
            if (taskId) {
                await this.apiCall(`/tasks/${taskId}`, {
                    method: 'PUT',
                    body: JSON.stringify(taskData)
                });
                this.showNotification('Task updated successfully!');
            } else {
                const newTask = await this.apiCall('/tasks/', {
                    method: 'POST',
                    body: JSON.stringify(taskData)
                });
                this.tasks.push(newTask);
                this.showNotification('Task created successfully!');
            }

            this.hideTaskModal();
            await this.refreshBoardData();
        } catch (error) {
            Debug.error('Failed to save task:', error);
        }
    }

    // Comment Management
    async loadTaskComments(taskId) {
        try {
            const response = await this.apiCall(`/tasks/${taskId}/comments`);
            this.renderComments(response.comments || []);
        } catch (error) {
            Debug.error('Failed to load comments:', error);
            this.renderComments([]);
        }
    }

    renderComments(comments) {
        const commentsList = document.getElementById('comments-list');
        
        if (!comments || comments.length === 0) {
            commentsList.innerHTML = '<div class="comments-empty">No comments yet</div>';
            return;
        }

        commentsList.innerHTML = comments.map(comment => {
            const date = new Date(comment.created_at).toLocaleString();
            return `
                <div class="comment-item" data-comment-id="${comment.id}">
                    <div class="comment-header">
                        <span class="comment-author">${this.escapeHtml(comment.author_name)}</span>
                        <span class="comment-date">${date}</span>
                    </div>
                    <div class="comment-content">${this.escapeHtml(comment.content)}</div>
                    <div class="comment-actions">
                        <button class="comment-action edit-comment" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="comment-action delete-comment" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        // Add event listeners for comment actions
        this.setupCommentActions();
    }

    setupCommentForm() {
        const addBtn = document.getElementById('add-comment-btn');
        const newCommentTextarea = document.getElementById('new-comment');
        
        // Remove existing listeners
        addBtn.replaceWith(addBtn.cloneNode(true));
        const newAddBtn = document.getElementById('add-comment-btn');
        
        newAddBtn.addEventListener('click', async () => {
            const content = newCommentTextarea.value.trim();
            if (!content) return;
            if (content.length > 2000) {
                alert('Comment is too long. Maximum 2000 characters allowed.');
                return;
            }
            
            const taskId = document.getElementById('task-id').value;
            if (!taskId) return;
            
            try {
                await this.apiCall(`/tasks/${taskId}/comments`, {
                    method: 'POST',
                    body: JSON.stringify({
                        content: content,
                        task_id: parseInt(taskId)
                    })
                });
                
                newCommentTextarea.value = '';
                await this.loadTaskComments(taskId);
                this.showNotification('Comment added successfully!');
            } catch (error) {
                Debug.error('Failed to add comment:', error);
                this.showNotification('Failed to add comment. Please try again.', 'error');
            }
        });

        // Allow Enter+Ctrl to submit comment
        newCommentTextarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                newAddBtn.click();
            }
        });
    }

    setupCommentActions() {
        const commentsList = document.getElementById('comments-list');
        
        commentsList.addEventListener('click', async (e) => {
            const commentItem = e.target.closest('.comment-item');
            if (!commentItem) return;
            
            const commentId = commentItem.dataset.commentId;
            
            if (e.target.closest('.edit-comment')) {
                await this.editComment(commentId, commentItem);
            } else if (e.target.closest('.delete-comment')) {
                await this.deleteComment(commentId);
            }
        });
    }

    async editComment(commentId, commentItem) {
        const contentDiv = commentItem.querySelector('.comment-content');
        const originalContent = contentDiv.textContent;
        
        // Replace content with textarea
        contentDiv.innerHTML = `
            <textarea class="edit-comment-textarea" style="width: 100%; min-height: 60px; resize: vertical;">${originalContent}</textarea>
            <div style="margin-top: 0.5rem;">
                <button class="btn btn-primary save-comment" style="margin-right: 0.5rem;">Save</button>
                <button class="btn btn-secondary cancel-edit">Cancel</button>
            </div>
        `;
        
        const textarea = contentDiv.querySelector('.edit-comment-textarea');
        const saveBtn = contentDiv.querySelector('.save-comment');
        const cancelBtn = contentDiv.querySelector('.cancel-edit');
        
        textarea.focus();
        
        saveBtn.addEventListener('click', async () => {
            const newContent = textarea.value.trim();
            if (!newContent) return;
            
            try {
                await this.apiCall(`/tasks/comments/${commentId}`, {
                    method: 'PUT',
                    body: JSON.stringify({ content: newContent })
                });
                
                const taskId = document.getElementById('task-id').value;
                await this.loadTaskComments(taskId);
                this.showNotification('Comment updated successfully!');
            } catch (error) {
                Debug.error('Failed to update comment:', error);
                this.showNotification('Failed to update comment. Please try again.', 'error');
            }
        });
        
        cancelBtn.addEventListener('click', () => {
            contentDiv.innerHTML = this.escapeHtml(originalContent);
        });
    }

    async deleteComment(commentId) {
        if (!confirm('Are you sure you want to delete this comment?')) return;
        
        try {
            await this.apiCall(`/tasks/comments/${commentId}`, {
                method: 'DELETE'
            });
            
            const taskId = document.getElementById('task-id').value;
            await this.loadTaskComments(taskId);
            this.showNotification('Comment deleted successfully!');
        } catch (error) {
            Debug.error('Failed to delete comment:', error);
            this.showNotification('Failed to delete comment. Please try again.', 'error');
        }
    }

    clearComments() {
        const commentsList = document.getElementById('comments-list');
        commentsList.innerHTML = '<div class="comments-empty">No comments yet</div>';
        
        const newCommentTextarea = document.getElementById('new-comment');
        if (newCommentTextarea) {
            const commentText = newCommentTextarea.value.trim();
            if (commentText.length > 2000) {
                alert('Comment is too long. Maximum 2000 characters allowed.');
            } else {
                newCommentTextarea.value = '';
            }
        }
    }

    async editTask(taskId) {
        const task = this.tasks.find(t => t.id === parseInt(taskId));
        if (task) {
            this.showTaskModal(null, task);
        }
    }

    async deleteTask(taskId) {
        if (!confirm('Are you sure you want to delete this task?')) return;
        
        try {
            await this.apiCall(`/tasks/${taskId}`, {
                method: 'DELETE'
            });
            
            // Refresh board data to reflect the deletion
            await this.refreshBoardData();
            this.showNotification('Task deleted successfully!');
            
        } catch (error) {
            Debug.error('Failed to delete task:', error);
        }
    }

    // Board Modal Management
    showBoardModal(board = null) {
        const modal = document.getElementById('board-modal');
        const form = document.getElementById('board-form');
        const title = document.getElementById('board-modal-title');
        const submitBtn = document.getElementById('board-submit');
        const deleteBtn = document.getElementById('board-delete');
        
        if (board) {
            // Edit mode
            title.textContent = 'Edit Board';
            submitBtn.textContent = 'Update Board';
            document.getElementById('board-name').value = board.name;
            document.getElementById('board-desc').value = board.description || '';
            form.dataset.boardId = board.id; // Store board ID for editing
            deleteBtn.style.display = 'block'; // Show delete button in edit mode
        } else {
            // Create mode
            title.textContent = 'Create New Board';
            submitBtn.textContent = 'Create Board';
            form.reset();
            delete form.dataset.boardId; // Remove board ID for new boards
            deleteBtn.style.display = 'none'; // Hide delete button in create mode
        }
        
        modal.classList.add('show');
    }

    hideBoardModal() {
        document.getElementById('board-modal').classList.remove('show');
    }

    async handleBoardSubmit(e) {
        e.preventDefault();
        
        const form = e.target;
        const formData = new FormData(form);
        const boardData = {
            name: formData.get('name'),
            description: formData.get('description') || null
        };
        
        const boardId = form.dataset.boardId;
        
        try {
            if (boardId) {
                // Update existing board
                const updatedBoard = await this.apiCall(`/boards/${boardId}`, {
                    method: 'PUT',
                    body: JSON.stringify(boardData)
                });
                
                this.currentBoard = updatedBoard;
                this.hideBoardModal();
                await this.loadBoards();
                this.renderBoard(); // Re-render with updated info
                this.showNotification('Board updated successfully!');
                
            } else {
                // Create new board (default columns are created by the API)
                const newBoard = await this.apiCall('/boards/', {
                    method: 'POST',
                    body: JSON.stringify(boardData)
                });
                
                this.hideBoardModal();
                await this.loadBoards();
                await this.selectBoard(newBoard.id);
                this.showNotification('Board created successfully!');
            }
            
        } catch (error) {
            Debug.error('Failed to save board:', error);
        }
    }

    async editCurrentBoard() {
        if (this.currentBoard) {
            this.showBoardModal(this.currentBoard);
        }
    }

    async deleteCurrentBoard() {
        if (!this.currentBoard) return;
        
        const boardName = this.currentBoard.name;
        const confirmMessage = `Are you sure you want to delete the board "${boardName}"?\n\nThis action cannot be undone and will delete all columns and tasks in this board.`;
        
        if (!confirm(confirmMessage)) return;
        
        try {
            await this.apiCall(`/boards/${this.currentBoard.id}`, {
                method: 'DELETE'
            });
            
            this.hideBoardModal();
            this.currentBoard = null;
            
            // Remove deleted board from localStorage
            localStorage.removeItem('selectedBoardId');
            
            // Reload boards list
            await this.loadBoards();
            
            // If there are remaining boards, select the first one
            if (this.boards.length > 0) {
                await this.selectBoard(this.boards[0].id);
            } else {
                // No boards left, show empty state
                this.showEmptyState();
            }
            
            this.showNotification(`Board "${boardName}" deleted successfully!`);
            
        } catch (error) {
            Debug.error('Failed to delete board:', error);
            this.showNotification('Failed to delete board. Please try again.', 'error');
        }
    }

    // Column Modal Management
    showColumnModal() {
        if (!this.currentBoard) {
            this.showNotification('Please select a board first', 'error');
            return;
        }

        const modal = document.getElementById('column-modal');
        const form = document.getElementById('column-form');
        
        // Reset form
        form.reset();
        
        // Show modal
        modal.style.display = 'block';
        setTimeout(() => modal.classList.add('show'), 10);
        
        // Focus on name input
        document.getElementById('column-name').focus();
    }

    hideColumnModal() {
        const modal = document.getElementById('column-modal');
        modal.classList.remove('show');
        setTimeout(() => modal.style.display = 'none', 300);
    }

    async handleColumnSubmit(e) {
        e.preventDefault();
        
        if (!this.currentBoard) {
            this.showNotification('No board selected', 'error');
            return;
        }

        const form = e.target;
        const formData = new FormData(form);
        
        const columnData = {
            name: formData.get('name'),
            board_id: this.currentBoard.id,
            position: formData.get('position') ? parseInt(formData.get('position')) : this.columns.length
        };

        try {
            const newColumn = await this.apiCall('/columns/', {
                method: 'POST',
                body: JSON.stringify(columnData)
            });
            
            this.hideColumnModal();
            await this.selectBoard(this.currentBoard.id);
            this.showNotification(`Column "${newColumn.name}" created successfully!`);
            
        } catch (error) {
            Debug.error('Failed to create column:', error);
            this.showNotification('Failed to create column. Please try again.', 'error');
        }
    }

    // UI State Management
    showLoading() {
        document.getElementById('loading').style.display = 'flex';
        document.getElementById('empty-state').style.display = 'none';
        document.getElementById('kanban-board').style.display = 'none';
    }

    hideLoading() {
        document.getElementById('loading').style.display = 'none';
    }

    showEmptyState() {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('empty-state').style.display = 'flex';
        document.getElementById('kanban-board').style.display = 'none';
    }

    showBoard() {
        Debug.log('showBoard() called');
        const loading = document.getElementById('loading');
        const emptyState = document.getElementById('empty-state');
        const kanbanBoard = document.getElementById('kanban-board');
        
        Debug.log('Loading element:', loading);
        Debug.log('Empty state element:', emptyState);
        Debug.log('Kanban board element:', kanbanBoard);
        
        loading.style.display = 'none';
        emptyState.style.display = 'none';
        kanbanBoard.style.display = 'block';
        
        Debug.log('Board visibility updated');
    }

    // Notifications
    showNotification(message, type = 'success') {
        const notification = document.getElementById('notification');
        const messageEl = document.getElementById('notification-message');
        
        messageEl.textContent = message;
        notification.className = `notification ${type}`;
        notification.classList.add('show');
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            this.hideNotification();
        }, 3000);
    }

    hideNotification() {
        document.getElementById('notification').classList.remove('show');
    }

    // Utility Methods
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // WebSocket Methods for Real-Time Updates
    connectWebSocket(boardId) {
        // Close existing connection if any
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        
        if (!boardId) return;
        
        // Build WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        let wsUrl = `${protocol}//${host}/ws/board/${boardId}`;
        
        // Add token if available
        if (this.authManager && this.authManager.token) {
            wsUrl += `?token=${encodeURIComponent(this.authManager.token)}`;
        }
        
        Debug.log('Connecting to WebSocket:', wsUrl);
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                Debug.log('WebSocket connected for board:', boardId);
                this.wsReconnectAttempts = 0;
                this.showNotification('Real-time updates enabled', 'success');
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    Debug.log('WebSocket message received:', data);
                    this.handleWebSocketEvent(data);
                } catch (e) {
                    Debug.error('Failed to parse WebSocket message:', e);
                }
            };
            
            this.ws.onclose = (event) => {
                Debug.log('WebSocket closed:', event.code, event.reason);
                this.ws = null;
                
                // Attempt reconnection if not a clean close
                if (event.code !== 1000 && this.currentBoard) {
                    this.attemptWebSocketReconnect();
                }
            };
            
            this.ws.onerror = (error) => {
                Debug.error('WebSocket error:', error);
            };
            
        } catch (error) {
            Debug.error('Failed to create WebSocket:', error);
        }
    }
    
    attemptWebSocketReconnect() {
        if (this.wsReconnectAttempts >= this.wsMaxReconnectAttempts) {
            Debug.log('Max WebSocket reconnect attempts reached');
            return;
        }
        
        this.wsReconnectAttempts++;
        const delay = this.wsReconnectDelay * Math.pow(2, this.wsReconnectAttempts - 1);
        
        Debug.log(`Attempting WebSocket reconnect in ${delay}ms (attempt ${this.wsReconnectAttempts})`);
        
        setTimeout(() => {
            if (this.currentBoard && !this.ws) {
                this.connectWebSocket(this.currentBoard.id);
            }
        }, delay);
    }
    
    disconnectWebSocket() {
        if (this.ws) {
            this.ws.close(1000, 'User disconnected');
            this.ws = null;
        }
    }
    
    handleWebSocketEvent(event) {
        const { event_type, data, user_id } = event;
        
        // Skip updates triggered by current user (already reflected in UI)
        // Uncomment below to ignore own updates:
        // if (this.authManager && user_id === this.authManager.userId) return;
        
        switch (event_type) {
            case 'connected':
                Debug.log('WebSocket connection confirmed');
                break;
                
            case 'task_created':
                this.handleTaskCreated(data);
                break;
                
            case 'task_updated':
                this.handleTaskUpdated(data);
                break;
                
            case 'task_moved':
                this.handleTaskMoved(data);
                break;
                
            case 'task_deleted':
                this.handleTaskDeleted(data);
                break;
                
            case 'column_created':
            case 'column_updated':
            case 'column_deleted':
            case 'board_updated':
                // For column/board changes, do a full refresh
                this.refreshBoardData();
                break;
                
            default:
                Debug.log('Unknown WebSocket event:', event_type);
        }
    }
    
    handleTaskCreated(taskData) {
        Debug.log('Handling task_created:', taskData);
        
        // Check if task already exists (avoid duplicates)
        if (this.tasks.find(t => t.id === taskData.id)) {
            Debug.log('Task already exists, skipping');
            return;
        }
        
        // Add to local tasks array
        this.tasks.push(taskData);
        
        // Find the column and add the task card
        const tasksList = document.querySelector(`.tasks-list[data-column-id="${taskData.column_id}"]`);
        if (tasksList) {
            const wrapper = document.createElement('div');
            wrapper.innerHTML = this.createTaskHTML(taskData).trim();
            const taskCard = wrapper.firstElementChild;
            if (taskCard) {
                tasksList.appendChild(taskCard);
                this.makeDraggable(taskCard);
                
                // Update task count
                this.updateColumnTaskCount(taskData.column_id);
                
                // Highlight new task briefly
                taskCard.classList.add('task-highlight');
                setTimeout(() => taskCard.classList.remove('task-highlight'), 2000);
            }
        }
    }
    
    handleTaskUpdated(taskData) {
        Debug.log('Handling task_updated:', taskData);
        
        // Update local tasks array
        const taskIndex = this.tasks.findIndex(t => t.id === taskData.id);
        if (taskIndex !== -1) {
            this.tasks[taskIndex] = taskData;
        }
        
        // Update the task card in DOM
        const oldCard = document.querySelector(`.task-card[data-task-id="${taskData.id}"]`);
        if (oldCard) {
            const wrapper = document.createElement('div');
            wrapper.innerHTML = this.createTaskHTML(taskData).trim();
            const newCard = wrapper.firstElementChild;
            if (newCard) {
                oldCard.replaceWith(newCard);
                this.makeDraggable(newCard);
                
                // Highlight updated task briefly
                newCard.classList.add('task-highlight');
                setTimeout(() => newCard.classList.remove('task-highlight'), 2000);
            }
        }
        
        // Update edit modal if this task is being edited
        const editingTaskId = document.getElementById('task-id')?.value;
        if (editingTaskId && parseInt(editingTaskId) === taskData.id) {
            // Update the currentEditTask reference
            this.currentEditTask = taskData;
        }
    }
    
    handleTaskMoved(taskData) {
        Debug.log('Handling task_moved:', taskData);
        
        const oldColumnId = taskData.old_column_id;
        const newColumnId = taskData.column_id;
        
        // Update local tasks array
        const taskIndex = this.tasks.findIndex(t => t.id === taskData.id);
        if (taskIndex !== -1) {
            this.tasks[taskIndex] = taskData;
        }
        
        // Move the task card in DOM
        const taskCard = document.querySelector(`.task-card[data-task-id="${taskData.id}"]`);
        const newTasksList = document.querySelector(`.tasks-list[data-column-id="${newColumnId}"]`);
        
        if (taskCard && newTasksList) {
            // Update card content
            const wrapper = document.createElement('div');
            wrapper.innerHTML = this.createTaskHTML(taskData).trim();
            const newCard = wrapper.firstElementChild;
            
            if (newCard) {
                taskCard.replaceWith(newCard);
                newTasksList.appendChild(newCard);
                this.makeDraggable(newCard);
                
                // Update task counts for both columns
                this.updateColumnTaskCount(oldColumnId);
                this.updateColumnTaskCount(newColumnId);
                
                // Highlight moved task briefly
                newCard.classList.add('task-highlight');
                setTimeout(() => newCard.classList.remove('task-highlight'), 2000);
            }
        }
    }
    
    handleTaskDeleted(data) {
        Debug.log('Handling task_deleted:', data);
        
        const { task_id, column_id } = data;
        
        // Remove from local tasks array
        this.tasks = this.tasks.filter(t => t.id !== task_id);
        
        // Remove from DOM
        const taskCard = document.querySelector(`.task-card[data-task-id="${task_id}"]`);
        if (taskCard) {
            taskCard.remove();
            
            // Update task count
            this.updateColumnTaskCount(column_id);
        }
        
        // Close edit modal if this task was being edited
        const editingTaskId = document.getElementById('task-id')?.value;
        if (editingTaskId && parseInt(editingTaskId) === task_id) {
            this.hideTaskModal();
            this.showNotification('Task was deleted by another user', 'info');
        }
    }
    
    updateColumnTaskCount(columnId) {
        const column = document.querySelector(`.column[data-column-id="${columnId}"]`);
        if (column) {
            const taskCount = column.querySelectorAll('.task-card').length;
            const countSpan = column.querySelector('.task-count');
            if (countSpan) {
                countSpan.textContent = taskCount;
            }
        }
    }
}

// Global function for auth system to initialize kanban app
window.initializeKanbanApp = () => {
    Debug.log('Initializing authenticated KanbanApp...');
    window.kanbanApp = new KanbanApp();
    window.kanbanApp.init();
    Debug.log('KanbanApp initialized:', window.kanbanApp);
};

// Legacy initialization (will be handled by auth system)
document.addEventListener('DOMContentLoaded', () => {
    Debug.log('DOM loaded - auth system will handle initialization');
});
