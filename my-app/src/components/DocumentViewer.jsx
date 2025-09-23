"use client";
import React, { useState, useMemo } from 'react';
import PropTypes from 'prop-types';

const DocumentViewer = ({ 
    fileName, 
    sanitizedDocText, 
    isLoading = false,
    onError = null,
    searchable = true,
    maxDisplayLength = null 
}) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [isExpanded, setIsExpanded] = useState(false);

    // Handle loading state
    if (isLoading) {
        return (
            <div className="flex flex-col h-full">
                <h2 className="text-xl font-bold text-white mb-4 flex-shrink-0">
                    Loading Document...
                </h2>
                <div className="flex-grow flex items-center justify-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
                </div>
            </div>
        );
    }

    // Handle empty state
    if (!sanitizedDocText || sanitizedDocText.trim() === '') {
        // Debug logging
        console.log('❌ DocumentViewer - No text:', {
            fileName,
            sanitizedDocTextType: typeof sanitizedDocText,
            sanitizedDocTextLength: sanitizedDocText ? sanitizedDocText.length : 0,
            sanitizedDocTextPreview: sanitizedDocText ? sanitizedDocText.substring(0, 100) : 'null/undefined'
        });
        
        return (
            <div className="flex flex-col h-full">
                <h2 className="text-xl font-bold text-white mb-4 flex-shrink-0">
                    Document: {fileName || 'Unknown'}
                </h2>
                <div className="flex-grow flex items-center justify-center">
                    <div className="text-center text-slate-400">
                        <div className="text-4xl mb-4">📄</div>
                        <p className="text-lg mb-2">No document content available</p>
                        <p className="text-sm">The document appears to be empty or couldn't be processed.</p>
                        <p className="text-xs mt-2 text-slate-500">
                            Debug: Text length = {sanitizedDocText ? sanitizedDocText.length : 0}
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    // Handle error state
    if (onError) {
        return (
            <div className="flex flex-col h-full">
                <h2 className="text-xl font-bold text-white mb-4 flex-shrink-0">
                    Document: {fileName || 'Unknown'}
                </h2>
                <div className="flex-grow flex items-center justify-center">
                    <div className="text-center text-red-400">
                        <div className="text-4xl mb-4">⚠️</div>
                        <p className="text-lg mb-2">Error loading document</p>
                        <p className="text-sm text-slate-400">Please try uploading again.</p>
                    </div>
                </div>
            </div>
        );
    }

    // Process document text for display
    const processedText = useMemo(() => {
        let text = sanitizedDocText;
        
        // Debug logging for successful case
        console.log('✅ DocumentViewer - Text loaded:', {
            fileName,
            textLength: text.length,
            textPreview: text.substring(0, 200)
        });
        
        // Truncate if maxDisplayLength is specified and text is longer
        if (maxDisplayLength && text.length > maxDisplayLength && !isExpanded) {
            text = text.substring(0, maxDisplayLength) + '...';
        }

        return text;
    }, [sanitizedDocText, maxDisplayLength, isExpanded, fileName]);

    // Highlight search terms
    const highlightedText = useMemo(() => {
        if (!searchTerm.trim()) return processedText;
        
        const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return processedText.replace(regex, '<mark class="bg-yellow-300 text-black">$1</mark>');
    }, [processedText, searchTerm]);

    // Calculate document stats
    const documentStats = useMemo(() => {
        const wordCount = sanitizedDocText.trim().split(/\s+/).length;
        const charCount = sanitizedDocText.length;
        const readingTime = Math.ceil(wordCount / 200); // Average 200 words per minute
        
        return { wordCount, charCount, readingTime };
    }, [sanitizedDocText]);

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="flex-shrink-0 mb-4">
                <h2 className="text-xl font-bold text-white mb-2">
                    Document: {fileName || 'Unknown File'}
                </h2>
                
                {/* Document Stats */}
                <div className="flex flex-wrap gap-4 text-xs text-slate-400 mb-3">
                    <span>{documentStats.wordCount.toLocaleString()} words</span>
                    <span>{documentStats.charCount.toLocaleString()} characters</span>
                    <span>~{documentStats.readingTime} min read</span>
                </div>

                {/* Search Bar */}
                {searchable && (
                    <div className="relative mb-3">
                        <input
                            type="text"
                            placeholder="Search in document..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full px-3 py-2 text-sm bg-slate-800 border border-slate-600 rounded-md text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                            aria-label="Search document content"
                        />
                        {searchTerm && (
                            <button
                                onClick={() => setSearchTerm('')}
                                className="absolute right-2 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-white"
                                aria-label="Clear search"
                            >
                                ✕
                            </button>
                        )}
                    </div>
                )}

                {/* Expand/Collapse Button (if text is truncated) */}
                {maxDisplayLength && sanitizedDocText.length > maxDisplayLength && (
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="text-sm text-blue-400 hover:text-blue-300 mb-2"
                    >
                        {isExpanded ? 'Show Less' : 'Show More'}
                    </button>
                )}
            </div>

            {/* Document Content */}
            <div 
                className="overflow-y-auto flex-grow pr-2 scrollbar-thin scrollbar-thumb-slate-600 scrollbar-track-slate-800"
                role="document"
                aria-label={`Content of ${fileName || 'document'}`}
            >
                <div 
                    className="font-serif text-sm text-slate-300 leading-relaxed whitespace-pre-wrap selection:bg-blue-500 selection:text-white"
                    dangerouslySetInnerHTML={{ 
                        __html: searchTerm ? highlightedText : processedText 
                    }}
                />
                
                {/* End of document indicator */}
                <div className="text-center text-slate-500 text-xs mt-8 py-4 border-t border-slate-700">
                    — End of Document —
                </div>
            </div>

            {/* Search Results Counter */}
            {searchTerm && (
                <div className="flex-shrink-0 mt-2 text-xs text-slate-400">
                    {(() => {
                        const matches = (processedText.match(new RegExp(searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi')) || []).length;
                        return matches > 0 ? `${matches} match${matches !== 1 ? 'es' : ''} found` : 'No matches found';
                    })()}
                </div>
            )}
        </div>
    );
};

// PropTypes for type checking
DocumentViewer.propTypes = {
    fileName: PropTypes.string,
    sanitizedDocText: PropTypes.string,
    isLoading: PropTypes.bool,
    onError: PropTypes.bool,
    searchable: PropTypes.bool,
    maxDisplayLength: PropTypes.number
};

// Default props
DocumentViewer.defaultProps = {
    fileName: 'Unknown File',
    sanitizedDocText: '',
    isLoading: false,
    onError: false,
    searchable: true,
    maxDisplayLength: null
};

export default DocumentViewer;