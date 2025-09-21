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

(ii) TechCorp Solutions Inc., a company established in accordance with the laws of Delaware and having its principal offices located at 123 Business Ave, San Francisco, CA 94105 (hereinafter the "Bidder" or the "Recipient").

The Discloser and Recipient are also referred to collectively as the "Parties" and individually as a "Party".

RECITALS

WHEREAS in connection with RFP/2014/620, Request for Proposal for the provision Off-the-shelf Soft-skill, IT Online and HR specific E-learning Courses (the "RFP"), it is advantageous to share certain data and information with the Bidder participating in the RFP;

WHEREAS UNHCR agrees to provide such data and information to the Bidder for the sole purpose of preparing its Proposal under said RFP;

WHEREAS the Bidder is willing to ensure that UNHCR's data and information will be held in strict confidence and only used for the permitted purpose;

NOW, THEREFORE, the Parties agree as follows:

1. DEFINITION OF CONFIDENTIAL INFORMATION
"Confidential Information", whenever used in this Agreement, shall mean any data, document, specification and other information or material, that is delivered or disclosed by UNHCR to the Recipient in any form whatsoever, whether orally, visually in writing or otherwise (including computerized form), and that, at the time of disclosure to the Recipient, is designated as confidential.

2. OBLIGATIONS OF RECIPIENT
The Confidential Information that is delivered or otherwise disclosed by the Discloser to the Recipient shall be held in trust and confidence by the Recipient and shall be handled as follows:

2.1 The Recipient shall use the same care and discretion to avoid disclosure, publication or dissemination of the Confidential Information as it uses with its own similar information that it does not wish to disclose, publish or disseminate;

2.2 The Recipient shall use the Confidential Information solely for the purpose for which it was disclosed;

2.3 Provided that the Recipient has a written agreement with the following persons or entities requiring them to treat the Confidential Information in accordance with this Agreement, the Recipient may disclose the Confidential Information to:

2.3.1 Any other party with the Discloser's prior written consent; and

2.3.2 the Recipient's employees, officials, representatives and agents who have a strict need to know the contents of the Confidential Information.

3. NO WARRANTIES
The Recipient acknowledges that UNHCR hereto makes no any representation or warranty, express or implied, as to the accuracy or completeness of the Confidential Information.

4. NO RIGHTS GRANTED
Nothing in this Agreement is to be construed as granting the Recipient, by implication or otherwise, any right whatsoever with respect to the Confidential Information or part thereof.

5. RETURN OF INFORMATION
All Confidential Information in any form and any medium, including all copies thereof, disclosed to the Recipient shall be returned to UNHCR or destroyed: (a) if a business relationship is not entered into with UNHCR on or before the date which is three (3) months after the date both Parties have signed the Agreement; or (b) promptly upon request by the UNHCR at any time.

6. INDEMNIFICATION
The Recipient agrees to indemnify UNHCR in respect of any expenses, losses, damages, costs, claims or liability UNHCR may suffer or incur as a result of an act or omission by the Recipient or its employees, consultants and agents in connection with the Confidential Information and the Recipient's obligations under this Agreement.

7. NO OBLIGATION TO CONTINUE
Nothing in this Agreement shall be construed as obligating any Party to continue any discussions or to enter into a business relationship.

8. TERM AND TERMINATION
This Agreement shall enter into force on the date it is signed by both Parties. Either Party may terminate the working relationship contemplated by this Agreement by providing written notice to the other, provided, however, that the obligations and restrictions hereunder regarding the Confidential Information shall remain effective following any such termination or any other termination or expiration of this Agreement.

9. DISPUTE RESOLUTION
Any dispute, controversy or claim between the Parties arising out of, this Agreement or the breach, termination or invalidity thereof, unless settled amicably within twenty (20) days after receipt by one Party of the other Party's request for such amicable settlement, shall be referred by either Party to arbitration in accordance with the UNCITRAL Arbitration Rules then obtaining, including provisions on applicable law.

10. PRIVILEGES AND IMMUNITIES
Nothing in or relating to this Agreement shall be deemed a waiver, express or implied, of any of the privileges and immunities of the United Nations, including UNHCR as its subsidiary organ.

11. PUBLICITY RESTRICTIONS
The Recipient shall not advertise or otherwise make public the fact that it has a confidential relationship with UNHCR, nor shall the Recipient, in any manner whatsoever use the name, emblem, or official seal of the United Nations or UNHCR.

12. SEVERABILITY
If any provision of this Agreement shall be held to be invalid, illegal or unenforceable, the validity, legality and enforceability of the remaining provisions shall not in any way be affected or impaired.

13. ENTIRE AGREEMENT
This Agreement constitutes the entire agreement concerning the subject matter hereof above and supersedes all prior representations, agreements and understandings, whether written or oral, by and between the Parties on the subject hereof.

14. AUTHORITY TO SIGN
The Parties acknowledge and agree that their representatives who have signed this Agreement had full authority to do so and to fully bind the Party being represented by doing so.

IN WITNESS WHEREOF, the Parties, acting through their authorized representatives, have caused this Agreement to be signed on the dates set forth below:

For and on behalf of UNHCR:
_________________________
Name: Dr. Sarah Johnson
Title: Procurement Director
Date: March 15, 2024

For and on behalf of TechCorp Solutions Inc.:
_________________________
Name: Michael Chen
Title: Chief Executive Officer
Date: March 15, 2024

[EXTRACTED TEXT - AI PROCESSED]
Document Type: Non-Disclosure Agreement
Jurisdiction: International (UN) / Delaware
Effective Date: March 15, 2024
Key Clauses Identified: Confidentiality, Indemnification, Arbitration, Term Limits
Risk Level: Medium-High (Broad indemnification clause)
Compliance Notes: UN procurement standards applied`;

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