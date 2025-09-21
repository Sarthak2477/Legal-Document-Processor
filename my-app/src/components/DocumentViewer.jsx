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

    // Mock document content for presentation
    const mockDocumentContent = `NON-DISCLOSURE AND CONFIDENTIALITY AGREEMENT

This NON-DISCLOSURE AND CONFIDENTIALITY AGREEMENT ("Agreement") is made by and between:

(i) the Office of the United Nations High Commissioner for Refugees, having its headquarters located at 94 rue de Montbrillant, 1202 Geneva, Switzerland (hereinafter "UNHCR" or the "Discloser"); and

(ii) [BIDDER NAME], a company established in accordance with the laws of [JURISDICTION] and having its principal offices located at [ADDRESS] (hereinafter the "Bidder" or the "Recipient").

The Discloser and Recipient are also referred to collectively as the "Parties" and individually as a "Party".

RECITALS

WHEREAS in connection with RFP/2014/620, Request for Proposal for the provision Off-the-shelf Soft-skill, IT Online and HR specific E-learning Courses (the "RFP"), it is advantageous to share certain data and information with the Bidder participating in the RFP;

WHEREAS UNHCR agrees to provide such data and information to the Bidder for the sole purpose of preparing its Proposal under said RFP;

WHEREAS the Bidder is willing to ensure that UNHCR's data and information will be held in strict confidence and only used for the permitted purpose;

NOW, THEREFORE, the Parties agree as follows:

1. "Confidential Information", whenever used in this Agreement, shall mean any data, document, specification and other information or material, that is delivered or disclosed by UNHCR to the Recipient in any form whatsoever, whether orally, visually in writing or otherwise (including computerized form), and that, at the time of disclosure to the Recipient, is designated as confidential.

2. The Confidential Information that is delivered or otherwise disclosed by the Discloser to the Recipient shall be held in trust and confidence by the Recipient and shall be handled as follows:

2.1 The Recipient shall use the same care and discretion to avoid disclosure, publication or dissemination of the Confidential Information as it uses with its own similar information that it does not wish to disclose, publish or disseminate;

2.2 The Recipient shall use the Confidential Information solely for the purpose for which it was disclosed;

6. The Recipient agrees to indemnify UNHCR in respect of any expenses, losses, damages, costs, claims or liability UNHCR may suffer or incur as a result of an act or omission by the Recipient or its employees, consultants and agents in connection with the Confidential Information and the Recipient's obligations under this Agreement.

8. This Agreement shall enter into force on the date it is signed by both Parties. Either Party may terminate the working relationship contemplated by this Agreement by providing written notice to the other, provided, however, that the obligations and restrictions hereunder regarding the Confidential Information shall remain effective following any such termination or any other termination or expiration of this Agreement.`;

    // Use mock content if no document is provided
    const displayText = sanitizedDocText && sanitizedDocText.trim() !== '' ? sanitizedDocText : mockDocumentContent;

    // Handle empty state (now only if mock content fails)
    if (!displayText || displayText.trim() === '') {
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
        let text = displayText;
        
        // Truncate if maxDisplayLength is specified and text is longer
        if (maxDisplayLength && text.length > maxDisplayLength && !isExpanded) {
            text = text.substring(0, maxDisplayLength) + '...';
        }

        return text;
    }, [sanitizedDocText, maxDisplayLength, isExpanded]);

    // Highlight search terms
    const highlightedText = useMemo(() => {
        if (!searchTerm.trim()) return processedText;
        
        const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return processedText.replace(regex, '<mark class="bg-yellow-300 text-black">$1</mark>');
    }, [processedText, searchTerm]);

    // Calculate document stats
    const documentStats = useMemo(() => {
        const wordCount = displayText.trim().split(/\s+/).length;
        const charCount = displayText.length;
        const readingTime = Math.ceil(wordCount / 200); // Average 200 words per minute
        
        return { wordCount, charCount, readingTime };
    }, [displayText]);

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
                {maxDisplayLength && displayText.length > maxDisplayLength && (
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