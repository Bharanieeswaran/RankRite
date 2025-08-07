// Navbar search functionality
class NavbarSearch {
    constructor() {
        this.searchInput = null;
        this.searchButton = null;
        this.searchResults = null;
        this.searchOverlay = null;
        this.isOpen = false;
        this.searchHistory = [];
        this.maxHistoryItems = 5;
        
        this.init();
    }

    init() {
        this.setupElements();
        this.setupEventListeners();
        this.loadSearchHistory();
    }

    setupElements() {
        this.searchInput = document.getElementById('navbar-search');
        this.searchButton = document.getElementById('search-button');
        this.searchResults = document.getElementById('search-results');
        this.searchOverlay = document.getElementById('search-overlay');
        
        // Create elements if they don't exist
        if (!this.searchResults) {
            this.createSearchResults();
        }
        
        if (!this.searchOverlay) {
            this.createSearchOverlay();
        }
    }

    createSearchResults() {
        this.searchResults = document.createElement('div');
        this.searchResults.id = 'search-results';
        this.searchResults.className = 'search-results hidden';
        
        const searchContainer = this.searchInput?.parentElement || document.querySelector('.navbar');
        if (searchContainer) {
            searchContainer.appendChild(this.searchResults);
        }
    }

    createSearchOverlay() {
        this.searchOverlay = document.createElement('div');
        this.searchOverlay.id = 'search-overlay';
        this.searchOverlay.className = 'search-overlay hidden';
        document.body.appendChild(this.searchOverlay);
    }

    setupEventListeners() {
        if (this.searchInput) {
            // Search input events
            this.searchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
            
            this.searchInput.addEventListener('focus', () => {
                this.openSearch();
            });
            
            this.searchInput.addEventListener('keydown', (e) => {
                this.handleKeydown(e);
            });
        }

        if (this.searchButton) {
            this.searchButton.addEventListener('click', () => {
                this.executeSearch();
            });
        }

        // Close search when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-container')) {
                this.closeSearch();
            }
        });

        // Close search with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeSearch();
            }
        });

        // Search overlay click
        if (this.searchOverlay) {
            this.searchOverlay.addEventListener('click', () => {
                this.closeSearch();
            });
        }
    }

    handleSearch(query) {
        const trimmedQuery = query.trim();
        
        if (trimmedQuery.length === 0) {
            this.showSearchHistory();
            return;
        }

        if (trimmedQuery.length < 2) {
            this.clearResults();
            return;
        }

        // Debounce search
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.performSearch(trimmedQuery);
        }, 300);
    }

    async performSearch(query) {
        try {
            this.showLoading();
            
            // Mock search API call - replace with actual endpoint
            const results = await this.searchAPI(query);
            
            this.displayResults(results, query);
            
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Search failed. Please try again.');
        }
    }

    async searchAPI(query) {
        // Mock API - replace with actual search endpoint
        return new Promise((resolve) => {
            setTimeout(() => {
                const mockResults = [
                    {
                        type: 'page',
                        title: 'Resume Analysis',
                        description: 'Analyze your resume for ATS compatibility',
                        url: '/check',
                        icon: '📄'
                    },
                    {
                        type: 'page',
                        title: 'Resume Comparison',
                        description: 'Compare multiple resumes',
                        url: '/compare',
                        icon: '⚖️'
                    },
                    {
                        type: 'feature',
                        title: 'Career Tips',
                        description: 'Professional development advice',
                        url: '/tips',
                        icon: '💡'
                    },
                    {
                        type: 'page',
                        title: 'Resume Trends',
                        description: 'Latest industry trends',
                        url: '/trends',
                        icon: '📈'
                    }
                ].filter(item => 
                    item.title.toLowerCase().includes(query.toLowerCase()) ||
                    item.description.toLowerCase().includes(query.toLowerCase())
                );
                
                resolve(mockResults);
            }, 500);
        });
    }

    displayResults(results, query) {
        if (!this.searchResults) return;

        this.searchResults.innerHTML = '';
        
        if (results.length === 0) {
            this.showNoResults(query);
            return;
        }

        const resultsContainer = document.createElement('div');
        resultsContainer.className = 'search-results-list';

        results.forEach((result, index) => {
            const resultItem = this.createResultItem(result, index);
            resultsContainer.appendChild(resultItem);
        });

        // Add "View all results" option
        if (results.length > 3) {
            const viewAllItem = document.createElement('div');
            viewAllItem.className = 'search-result-item view-all';
            viewAllItem.innerHTML = `
                <span class="result-icon">🔍</span>
                <div class="result-content">
                    <div class="result-title">View all results for "${query}"</div>
                </div>
            `;
            viewAllItem.addEventListener('click', () => {
                this.executeSearch(query);
            });
            resultsContainer.appendChild(viewAllItem);
        }

        this.searchResults.appendChild(resultsContainer);
        this.searchResults.classList.remove('hidden');
    }

    createResultItem(result, index) {
        const item = document.createElement('div');
        item.className = 'search-result-item';
        item.setAttribute('data-index', index);
        
        item.innerHTML = `
            <span class="result-icon">${result.icon}</span>
            <div class="result-content">
                <div class="result-title">${result.title}</div>
                <div class="result-description">${result.description}</div>
                <div class="result-type">${result.type}</div>
            </div>
        `;

        item.addEventListener('click', () => {
            this.selectResult(result);
        });

        return item;
    }

    selectResult(result) {
        this.addToHistory(result.title);
        this.closeSearch();
        
        // Navigate to result
        if (result.url) {
            window.location.href = result.url;
        }
    }

    showSearchHistory() {
        if (!this.searchResults || this.searchHistory.length === 0) return;

        this.searchResults.innerHTML = '';
        
        const historyContainer = document.createElement('div');
        historyContainer.className = 'search-history';
        
        const historyTitle = document.createElement('div');
        historyTitle.className = 'search-history-title';
        historyTitle.textContent = 'Recent Searches';
        historyContainer.appendChild(historyTitle);

        this.searchHistory.forEach(query => {
            const historyItem = document.createElement('div');
            historyItem.className = 'search-history-item';
            historyItem.innerHTML = `
                <span class="history-icon">🕒</span>
                <span class="history-query">${query}</span>
                <button class="remove-history" data-query="${query}">×</button>
            `;
            
            historyItem.querySelector('.history-query').addEventListener('click', () => {
                this.searchInput.value = query;
                this.handleSearch(query);
            });
            
            historyItem.querySelector('.remove-history').addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeFromHistory(query);
            });
            
            historyContainer.appendChild(historyItem);
        });

        this.searchResults.appendChild(historyContainer);
        this.searchResults.classList.remove('hidden');
    }

    showLoading() {
        if (!this.searchResults) return;
        
        this.searchResults.innerHTML = `
            <div class="search-loading">
                <div class="search-spinner"></div>
                <span>Searching...</span>
            </div>
        `;
        this.searchResults.classList.remove('hidden');
    }

    showError(message) {
        if (!this.searchResults) return;
        
        this.searchResults.innerHTML = `
            <div class="search-error">
                <span class="error-icon">⚠️</span>
                <span>${message}</span>
            </div>
        `;
        this.searchResults.classList.remove('hidden');
    }

    showNoResults(query) {
        if (!this.searchResults) return;
        
        this.searchResults.innerHTML = `
            <div class="search-no-results">
                <span class="no-results-icon">🔍</span>
                <div>No results found for "${query}"</div>
                <div class="no-results-suggestion">Try different keywords</div>
            </div>
        `;
        this.searchResults.classList.remove('hidden');
    }

    clearResults() {
        if (this.searchResults) {
            this.searchResults.classList.add('hidden');
            this.searchResults.innerHTML = '';
        }
    }

    openSearch() {
        this.isOpen = true;
        if (this.searchOverlay) {
            this.searchOverlay.classList.remove('hidden');
        }
        
        // Show history if input is empty
        if (!this.searchInput.value.trim()) {
            this.showSearchHistory();
        }
    }

    closeSearch() {
        this.isOpen = false;
        this.clearResults();
        
        if (this.searchOverlay) {
            this.searchOverlay.classList.add('hidden');
        }
    }

    executeSearch(query = null) {
        const searchQuery = query || this.searchInput?.value?.trim();
        if (!searchQuery) return;

        this.addToHistory(searchQuery);
        this.closeSearch();
        
        // Redirect to search results page or perform search
        window.location.href = `/search?q=${encodeURIComponent(searchQuery)}`;
    }

    handleKeydown(e) {
        switch (e.key) {
            case 'Enter':
                e.preventDefault();
                this.executeSearch();
                break;
            case 'ArrowDown':
                e.preventDefault();
                this.navigateResults('down');
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.navigateResults('up');
                break;
        }
    }

    navigateResults(direction) {
        const items = this.searchResults?.querySelectorAll('.search-result-item:not(.view-all)');
        if (!items || items.length === 0) return;

        const currentActive = this.searchResults.querySelector('.search-result-item.active');
        let newIndex = 0;

        if (currentActive) {
            const currentIndex = parseInt(currentActive.getAttribute('data-index'));
            if (direction === 'down') {
                newIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
            } else {
                newIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
            }
            currentActive.classList.remove('active');
        }

        items[newIndex].classList.add('active');
        items[newIndex].scrollIntoView({ block: 'nearest' });
    }

    addToHistory(query) {
        if (!query || this.searchHistory.includes(query)) return;

        this.searchHistory.unshift(query);
        if (this.searchHistory.length > this.maxHistoryItems) {
            this.searchHistory.pop();
        }

        this.saveSearchHistory();
    }

    removeFromHistory(query) {
        this.searchHistory = this.searchHistory.filter(item => item !== query);
        this.saveSearchHistory();
        this.showSearchHistory();
    }

    loadSearchHistory() {
        try {
            const saved = localStorage.getItem('search-history');
            if (saved) {
                this.searchHistory = JSON.parse(saved);
            }
        } catch (error) {
            console.warn('Failed to load search history:', error);
            this.searchHistory = [];
        }
    }

    saveSearchHistory() {
        try {
            localStorage.setItem('search-history', JSON.stringify(this.searchHistory));
        } catch (error) {
            console.warn('Failed to save search history:', error);
        }
    }

    clearHistory() {
        this.searchHistory = [];
        this.saveSearchHistory();
        this.clearResults();
    }
}

// Initialize search functionality
document.addEventListener('DOMContentLoaded', () => {
    window.navbarSearch = new NavbarSearch();
});

// Add search styles
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('search-styles')) return;
    
    const styles = document.createElement('style');
    styles.id = 'search-styles';
    styles.textContent = `
        .search-container {
            position: relative;
        }
        
        .search-results {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: var(--bg-color, #fff);
            border: 1px solid var(--border-color, #ddd);
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            max-height: 400px;
            overflow-y: auto;
            z-index: 1000;
            margin-top: 4px;
        }
        
        .search-results.hidden {
            display: none;
        }
        
        .search-result-item {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            cursor: pointer;
            border-bottom: 1px solid var(--border-color, #eee);
            transition: background-color 0.2s;
        }
        
        .search-result-item:hover,
        .search-result-item.active {
            background-color: var(--hover-bg, #f5f5f5);
        }
        
        .search-result-item:last-child {
            border-bottom: none;
        }
        
        .result-icon {
            font-size: 18px;
            margin-right: 12px;
            min-width: 24px;
        }
        
        .result-content {
            flex: 1;
        }
        
        .result-title {
            font-weight: 600;
            margin-bottom: 4px;
            color: var(--text-color, #333);
        }
        
        .result-description {
            font-size: 14px;
            color: var(--text-muted, #666);
            margin-bottom: 2px;
        }
        
        .result-type {
            font-size: 12px;
            color: var(--text-light, #999);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .search-history-title {
            padding: 12px 16px;
            font-weight: 600;
            color: var(--text-muted, #666);
            border-bottom: 1px solid var(--border-color, #eee);
            font-size: 14px;
        }
        
        .search-history-item {
            display: flex;
            align-items: center;
            padding: 8px 16px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .search-history-item:hover {
            background-color: var(--hover-bg, #f5f5f5);
        }
        
        .history-icon {
            margin-right: 12px;
            opacity: 0.6;
        }
        
        .history-query {
            flex: 1;
            color: var(--text-color, #333);
        }
        
        .remove-history {
            background: none;
            border: none;
            color: var(--text-muted, #999);
            cursor: pointer;
            padding: 4px;
            border-radius: 4px;
            opacity: 0.6;
            transition: opacity 0.2s;
        }
        
        .remove-history:hover {
            opacity: 1;
            background-color: var(--danger-bg, #fee);
            color: var(--danger-color, #dc2626);
        }
        
        .search-loading,
        .search-error,
        .search-no-results {
            padding: 20px;
            text-align: center;
            color: var(--text-muted, #666);
        }
        
        .search-spinner {
            width: 20px;
            height: 20px;
            border: 2px solid var(--border-color, #ddd);
            border-top: 2px solid var(--primary-color, #007bff);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 8px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .search-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.3);
            z-index: 999;
        }
        
        .search-overlay.hidden {
            display: none;
        }
        
        .view-all {
            font-weight: 600;
            color: var(--primary-color, #007bff);
        }
        
        .no-results-suggestion {
            font-size: 12px;
            margin-top: 4px;
            opacity: 0.8;
        }
        
        @media (max-width: 768px) {
            .search-results {
                left: -10px;
                right: -10px;
            }
        }
    `;
    document.head.appendChild(styles);
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NavbarSearch;
}