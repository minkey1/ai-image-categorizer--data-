/**
 * Filter Logic Module
 * 
 * This file contains all the filtering logic for the image gallery.
 * Edit this file to customize how images are filtered based on tags and text.
 */

class ImageFilter {
    constructor() {
        this.activeTagFilters = new Set();
        this.textSearchQuery = '';
        this.tagFilterMode = 'or';
    }

    /**
     * Add a tag to the active filters
     */
    addTagFilter(tag) {
        this.activeTagFilters.add(tag.toLowerCase());
    }

    /**
     * Remove a tag from the active filters
     */
    removeTagFilter(tag) {
        this.activeTagFilters.delete(tag.toLowerCase());
    }

    /**
     * Clear all tag filters
     */
    clearTagFilters() {
        this.activeTagFilters.clear();
    }

    /**
     * Set the text search query
     */
    setTextSearch(query) {
        this.textSearchQuery = query.toLowerCase().trim();
    }

    /**
     * Set the tag filter mode: 'and' or 'or'
     */
    setTagFilterMode(mode) {
        const normalized = (mode || '').toLowerCase();
        this.tagFilterMode = normalized === 'and' ? 'and' : 'or';
    }

    /**
     * Check if an image matches the active tag filters
     * 
     * LOGIC: Uses AND/OR based on `tagFilterMode`
     */
    matchesTagFilters(imageTags) {
        // No tag filters active = show all
        if (this.activeTagFilters.size === 0) {
            return true;
        }

        // Convert image tags to lowercase for comparison
        const imageTagsLower = imageTags.map(tag => tag.toLowerCase());

        if (this.tagFilterMode === 'and') {
            // AND logic: Image must have ALL selected tags
            for (let filterTag of this.activeTagFilters) {
                if (!imageTagsLower.includes(filterTag)) {
                    return false;
                }
            }
            return true;
        }

        // OR logic: Image must have ANY selected tag
        for (let filterTag of this.activeTagFilters) {
            if (imageTagsLower.includes(filterTag)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Check if an image matches the text search query
     * 
     * Searches in: filename, raw_text, structured_data, profile_mentions
     */
    matchesTextSearch(imageData) {
        // No search query = show all
        if (!this.textSearchQuery) {
            return true;
        }

        // Search in filename
        if (imageData.filename && imageData.filename.toLowerCase().includes(this.textSearchQuery)) {
            return true;
        }

        // Search in raw text
        if (imageData.raw_text && imageData.raw_text.toLowerCase().includes(this.textSearchQuery)) {
            return true;
        }

        // Search in tags
        if (imageData.tags && imageData.tags.some(tag => tag.toLowerCase().includes(this.textSearchQuery))) {
            return true;
        }

        // Search in structured data (convert to string)
        if (imageData.structured_data) {
            const structuredStr = JSON.stringify(imageData.structured_data).toLowerCase();
            if (structuredStr.includes(this.textSearchQuery)) {
                return true;
            }
        }

        // Search in profile mentions
        if (imageData.profile_mentions && imageData.profile_mentions.some(mention => 
            mention.toLowerCase().includes(this.textSearchQuery)
        )) {
            return true;
        }

        // Search in additional metadata
        if (imageData.additional_metadata) {
            const additionalStr = JSON.stringify(imageData.additional_metadata).toLowerCase();
            if (additionalStr.includes(this.textSearchQuery)) {
                return true;
            }
        }

        return false;
    }

    /**
     * Main filter function - checks both tag and text filters
     * 
     * LOGIC: Image must pass BOTH tag filter AND text filter
     */
    shouldShowImage(imageData) {
        const matchesTags = this.matchesTagFilters(imageData.tags || []);
        const matchesText = this.matchesTextSearch(imageData);

        // Must pass both filters
        return matchesTags && matchesText;
    }

    /**
     * Filter an array of images
     */
    filterImages(images) {
        return images.filter(imageData => this.shouldShowImage(imageData));
    }

    /**
     * Get all active filters as a readable string
     */
    getActiveFiltersDescription() {
        const parts = [];
        
        if (this.activeTagFilters.size > 0) {
            parts.push(`Tags: ${Array.from(this.activeTagFilters).join(', ')}`);
        }
        
        if (this.textSearchQuery) {
            parts.push(`Text: "${this.textSearchQuery}"`);
        }

        return parts.length > 0 ? parts.join(' | ') : 'No filters active';
    }

    /**
     * Check if any filters are active
     */
    hasActiveFilters() {
        return this.activeTagFilters.size > 0 || this.textSearchQuery.length > 0;
    }
}

// Export for use in main app
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ImageFilter;
}
