/**
 * Main Application Logic
 */

let allImages = [];
let allTags = new Set();
let currentPage = 1;
let totalPages = 1;
let totalImages = 0;
const filter = new ImageFilter();

// DOM Elements
const gallery = document.getElementById('gallery');
const searchInput = document.getElementById('searchText');
const tagButtonsContainer = document.getElementById('tagButtons');
const selectedTagsContainer = document.getElementById('selectedTags');
const tagFilterModeSelect = document.getElementById('tagFilterMode');
const clearFiltersBtn = document.getElementById('clearFilters');
const refreshDataBtn = document.getElementById('refreshData');
const imageCountSpan = document.getElementById('imageCount');
const filterCountSpan = document.getElementById('filterCount');
const modal = document.getElementById('modal');
const modalClose = modal.querySelector('.close');
const darkModeToggle = document.getElementById('darkModeToggle');
const prevPageBtn = document.getElementById('prevPage');
const nextPageBtn = document.getElementById('nextPage');
const pageInfo = document.getElementById('pageInfo');

/**
 * Update pagination control states and display
 */
function updatePaginationControls() {
    const hasPages = totalPages > 0;
    prevPageBtn.disabled = !hasPages || currentPage <= 1;
    nextPageBtn.disabled = !hasPages || currentPage >= totalPages;
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
}

/**
 * Load images for a specific page
 */
async function loadPage(page = 1) {
    try {
        gallery.innerHTML = '<p class="loading">Loading images...</p>';
        
        // Fetch the page of images from the server
        const response = await fetch(`/api/images?page=${page}`);
        const data = await response.json();
        
        allImages = data.images;
        currentPage = data.page;
        totalPages = data.total_pages;
        totalImages = data.total_images;
        
        // Extract all unique tags from current page
        allTags.clear();
        allImages.forEach(img => {
            if (img.tags) {
                img.tags.forEach(tag => allTags.add(tag));
            }
        });

        // Render tag buttons
        renderTagButtons();
        
        // Display images
        renderGallery(allImages);
        updatePaginationControls();
        updateStats();
        
    } catch (error) {
        console.error('Error loading images:', error);
        gallery.innerHTML = `<p class="error">Error loading images. Make sure the server is running.<br>Run: python server.py</p>`;
    }
}

/**
 * Load all images from the output folder
 */
async function loadImages() {
    loadPage(1);
}

// Default to OR mode
filter.setTagFilterMode('or');

/**
 * Initialize dark mode from localStorage
 */

/**
 * Render tag filter buttons
 */
function renderTagButtons() {
    tagButtonsContainer.innerHTML = '';
    
    const sortedTags = Array.from(allTags).sort();
    
    sortedTags.forEach(tag => {
        const btn = document.createElement('button');
        btn.className = 'tag-btn';
        btn.textContent = tag;
        btn.dataset.tag = tag;
        
        btn.addEventListener('click', () => toggleTag(tag, btn));
        
        tagButtonsContainer.appendChild(btn);
    });
}

/**
 * Toggle a tag filter on/off
 */
function toggleTag(tag, button) {
    if (filter.activeTagFilters.has(tag.toLowerCase())) {
        filter.removeTagFilter(tag);
        button.classList.remove('active');
    } else {
        filter.addTagFilter(tag);
        button.classList.add('active');
    }
    
    updateSelectedTags();
    applyFilters();
}

/**
 * Update the selected tags display
 */
function updateSelectedTags() {
    if (filter.activeTagFilters.size === 0) {
        selectedTagsContainer.innerHTML = '<span class="no-selection">No tags selected</span>';
        return;
    }
    
    selectedTagsContainer.innerHTML = '';
    Array.from(filter.activeTagFilters).forEach(tag => {
        const badge = document.createElement('span');
        badge.className = 'tag-badge';
        badge.innerHTML = `${tag} <span class="remove" data-tag="${tag}">×</span>`;
        
        badge.querySelector('.remove').addEventListener('click', () => {
            filter.removeTagFilter(tag);
            
            // Also deactivate the button
            const btn = tagButtonsContainer.querySelector(`[data-tag="${tag}"]`);
            if (btn) btn.classList.remove('active');
            
            updateSelectedTags();
            applyFilters();
        });
        
        selectedTagsContainer.appendChild(badge);
    });
}

/**
 * Apply all active filters and render results
 */
function applyFilters() {
    const filteredImages = filter.filterImages(allImages);
    renderGallery(filteredImages);
    updateStats(filteredImages.length);
}

/**
 * Render the gallery with the given images
 */
function renderGallery(images) {
    gallery.innerHTML = '';
    
    if (images.length === 0) {
        gallery.innerHTML = '<p class="no-results">No images match your filters.</p>';
        return;
    }
    
    images.forEach(imageData => {
        const card = createImageCard(imageData);
        gallery.appendChild(card);
    });
}

/**
 * Create an image card element
 */
function createImageCard(imageData) {
    const card = document.createElement('div');
    card.className = 'image-card';
    
    const img = document.createElement('img');
    img.src = `/output/${imageData.filename}`;
    img.alt = imageData.filename;
    img.loading = 'lazy';
    
    const info = document.createElement('div');
    info.className = 'image-info';
    
    const filename = document.createElement('div');
    filename.className = 'filename';
    filename.textContent = imageData.filename;
    
    const tags = document.createElement('div');
    tags.className = 'tags';
    (imageData.tags || []).slice(0, 5).forEach(tag => {
        const tagSpan = document.createElement('span');
        tagSpan.className = 'tag';
        tagSpan.textContent = tag;
        tags.appendChild(tagSpan);
    });
    
    if (imageData.tags && imageData.tags.length > 5) {
        const more = document.createElement('span');
        more.className = 'tag more';
        more.textContent = `+${imageData.tags.length - 5} more`;
        tags.appendChild(more);
    }
    
    info.appendChild(filename);
    info.appendChild(tags);
    card.appendChild(img);
    card.appendChild(info);
    
    // Click to view details
    card.addEventListener('click', () => showModal(imageData));
    
    return card;
}

/**
 * Show the modal with full image details
 */
function showModal(imageData) {
    const modalImage = document.getElementById('modalImage');
    const imageUrl = `/output/${imageData.filename}`;
    
    // Set image with reload functionality
    modalImage.src = imageUrl;
    modalImage.style.cursor = 'pointer';
    modalImage.title = 'Click to reload image';
    
    // Add click handler to reload image
    modalImage.onclick = () => {
        modalImage.src = imageUrl + '?t=' + new Date().getTime();
    };
    
    document.getElementById('modalFilename').textContent = imageData.filename;
    
    // Tags
    const modalTags = document.getElementById('modalTags');
    modalTags.innerHTML = '';
    (imageData.tags || []).forEach(tag => {
        const span = document.createElement('span');
        span.className = 'tag';
        span.textContent = tag;
        modalTags.appendChild(span);
    });
    
    // Raw text
    document.getElementById('modalRawText').textContent = imageData.raw_text || 'No text extracted';
    
    // Structured data
    document.getElementById('modalStructuredData').textContent = 
        JSON.stringify(imageData.structured_data || {}, null, 2);
    
    // Profile mentions
    const modalMentions = document.getElementById('modalMentions');
    if (imageData.profile_mentions && imageData.profile_mentions.length > 0) {
        modalMentions.innerHTML = imageData.profile_mentions.map(m => 
            `<span class="mention">${m}</span>`
        ).join(' ');
    } else {
        modalMentions.textContent = 'None';
    }
    
    // Additional metadata
    document.getElementById('modalAdditionalMetadata').textContent = 
        JSON.stringify(imageData.additional_metadata || {}, null, 2);
    
    modal.style.display = 'block';
}

/**
 * Update statistics
 */
function updateStats(filteredCount = null) {
    imageCountSpan.textContent = `${totalImages} total`;
    
    if (filteredCount !== null) {
        filterCountSpan.textContent = `${filteredCount} shown`;
    }
}

/**
 * Clear all filters
 */
function clearAllFilters() {
    filter.clearTagFilters();
    filter.setTextSearch('');
    searchInput.value = '';
    
    // Deactivate all tag buttons
    document.querySelectorAll('.tag-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    updateSelectedTags();
    applyFilters();
}

function initDarkMode() {
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
    }
}

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDarkMode = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDarkMode);
}

// Event Listeners
searchInput.addEventListener('input', (e) => {
    filter.setTextSearch(e.target.value);
    applyFilters();
});

clearFiltersBtn.addEventListener('click', clearAllFilters);
refreshDataBtn.addEventListener('click', loadImages);
tagFilterModeSelect.addEventListener('change', (e) => {
    filter.setTagFilterMode(e.target.value);
    applyFilters();
});
darkModeToggle.addEventListener('click', toggleDarkMode);
prevPageBtn.addEventListener('click', () => {
    if (currentPage > 1) {
        loadPage(currentPage - 1);
    }
});
nextPageBtn.addEventListener('click', () => {
    if (currentPage < totalPages) {
        loadPage(currentPage + 1);
    }
});

modalClose.addEventListener('click', () => {
    modal.style.display = 'none';
});

window.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.style.display = 'none';
    }
});

initDarkMode();
// Initialize
loadImages();
