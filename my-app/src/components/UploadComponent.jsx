"use client";
import React, { useState, useRef, useCallback } from 'react';
import PropTypes from 'prop-types';

const UploadComponent = ({ 
    onFileUpload,
    acceptedTypes = ['.pdf', '.doc', '.docx', '.txt'],
    maxFileSize = 10 * 1024 * 1024, // 10MB
    disabled = false,
    title = "Get Started",
    subtitle = "Upload your legal document to begin your AI-powered analysis.",
    showFileTypes = true,
    showMaxSize = true,
    className = ""
}) => {
    const [isDragOver, setIsDragOver] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState(null);
    const [dragCounter, setDragCounter] = useState(0);
    const fileInputRef = useRef(null);

    // File validation
    const validateFile = useCallback((file) => {
        if (!file) {
            throw new Error('No file selected');
        }

        // Check file size
        if (file.size > maxFileSize) {
            const maxSizeMB = (maxFileSize / (1024 * 1024)).toFixed(1);
            throw new Error(`File size exceeds ${maxSizeMB}MB limit. Please choose a smaller file.`);
        }

        // Check file type
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        if (!acceptedTypes.includes(fileExtension)) {
            const typesString = acceptedTypes.join(', ').toUpperCase();
            throw new Error(`Unsupported file type. Please upload ${typesString} files only.`);
        }

        return true;
    }, [acceptedTypes, maxFileSize]);

    // Handle file processing
    const processFile = useCallback(async (file) => {
        try {
            setError(null);
            setIsUploading(true);
            
            validateFile(file);
            
            if (onFileUpload) {
                await onFileUpload(file);
            }
        } catch (err) {
            console.error('File upload error:', err);
            setError(err.message);
        } finally {
            setIsUploading(false);
            // Reset file input
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    }, [validateFile, onFileUpload]);

    // Drag and drop handlers
    const handleDragEnter = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragCounter(prev => prev + 1);
        
        if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
            setIsDragOver(true);
        }
    }, []);

    const handleDragLeave = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragCounter(prev => {
            const newCounter = prev - 1;
            if (newCounter === 0) {
                setIsDragOver(false);
            }
            return newCounter;
        });
    }, []);

    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        
        setIsDragOver(false);
        setDragCounter(0);
        
        if (disabled || isUploading) return;
        
        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            processFile(files[0]);
        }
    }, [disabled, isUploading, processFile]);

    // Click handler
    const handleFileInputChange = useCallback((e) => {
        const file = e.target.files?.[0];
        if (file && !disabled && !isUploading) {
            processFile(file);
        }
    }, [disabled, isUploading, processFile]);

    // Format file size for display
    const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    };

    const maxSizeFormatted = formatFileSize(maxFileSize);
    const acceptedTypesString = acceptedTypes.join(', ').toUpperCase().replace(/\./g, '');

    return (
        <div className={`flex-grow flex flex-col items-center justify-center text-center transition-all duration-500 ${className}`}>
            {/* Title and Subtitle */}
            <div className="mb-8">
                <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-white via-slate-200 to-slate-300 bg-clip-text text-transparent">
                    {title}
                </h1>
                <p className="text-gray-400 text-lg max-w-2xl leading-relaxed">
                    {subtitle}
                </p>
            </div>

            {/* Error Message */}
            {error && (
                <div className="w-full max-w-lg mb-6 p-4 bg-red-900/50 border border-red-700/50 rounded-lg">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                            </svg>
                            <span className="text-red-300 text-sm">{error}</span>
                        </div>
                        <button 
                            onClick={() => setError(null)}
                            className="text-red-300 hover:text-red-100 transition-colors"
                            aria-label="Dismiss error"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                </div>
            )}

            {/* Upload Area */}
            <div className="w-full max-w-lg">
                <label 
                    htmlFor="file-upload" 
                    className={`relative cursor-pointer bg-slate-800/30 backdrop-blur-sm border-2 border-dashed transition-all duration-300 rounded-xl p-12 flex flex-col items-center justify-center text-center group ${
                        disabled || isUploading
                            ? 'border-slate-700 opacity-50 cursor-not-allowed'
                            : isDragOver
                                ? 'border-blue-400 bg-blue-900/20 scale-105'
                                : 'border-slate-700 hover:border-blue-500 hover:bg-slate-800/40 hover:scale-[1.02]'
                    }`}
                    onDragEnter={handleDragEnter}
                    onDragLeave={handleDragLeave}
                    onDragOver={handleDragOver}
                    onDrop={handleDrop}
                >
                    {/* Upload Icon */}
                    <div className={`transition-all duration-300 ${isUploading ? 'animate-pulse' : isDragOver ? 'scale-110' : ''}`}>
                        {isUploading ? (
                            <div className="w-16 h-16 mb-4 relative">
                                <div className="w-16 h-16 border-4 border-slate-600 rounded-full"></div>
                                <div className="absolute top-0 left-0 w-16 h-16 border-4 border-blue-500 rounded-full border-t-transparent animate-spin"></div>
                            </div>
                        ) : (
                            <svg 
                                className={`w-16 h-16 mb-4 transition-colors duration-300 ${
                                    isDragOver ? 'text-blue-400' : 'text-slate-600 group-hover:text-slate-500'
                                }`} 
                                fill="none" 
                                stroke="currentColor" 
                                viewBox="0 0 24 24"
                            >
                                <path 
                                    strokeLinecap="round" 
                                    strokeLinejoin="round" 
                                    strokeWidth={1.5} 
                                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" 
                                />
                            </svg>
                        )}
                    </div>

                    {/* Upload Text */}
                    <div className="space-y-2">
                        <span className={`font-semibold transition-colors duration-300 ${
                            isUploading 
                                ? 'text-blue-400'
                                : isDragOver 
                                    ? 'text-blue-300' 
                                    : 'text-slate-300 group-hover:text-white'
                        }`}>
                            {isUploading 
                                ? 'Processing file...' 
                                : isDragOver 
                                    ? 'Drop your file here' 
                                    : 'Drag & drop your file here'
                            }
                        </span>
                        
                        {!isUploading && (
                            <span className={`text-sm transition-colors duration-300 ${
                                isDragOver ? 'text-blue-400' : 'text-slate-500 group-hover:text-slate-400'
                            }`}>
        
                            </span>
                        )}
                    </div>

                    {/* Drag Overlay */}
                    {isDragOver && (
                        <div className="absolute inset-0 bg-blue-500/10 rounded-xl border-2 border-blue-400 border-dashed flex items-center justify-center">
                            <div className="text-blue-300 font-medium">
                                Drop to upload
                            </div>
                        </div>
                    )}
                </label>

                <input 
                    id="file-upload" 
                    ref={fileInputRef}
                    type="file" 
                    className="hidden" 
                    onChange={handleFileInputChange}
                    accept={acceptedTypes.join(',')}
                    disabled={disabled || isUploading}
                    aria-label="Upload document file"
                />
            </div>

            {/* File Requirements */}
            <div className="mt-6 space-y-2 text-center">
                {showFileTypes && (
                    <p className="text-slate-400 text-sm">
                        <span className="font-medium">Supported formats:</span> {acceptedTypesString}
                    </p>
                )}
                {showMaxSize && (
                    <p className="text-slate-400 text-sm">
                        <span className="font-medium">Maximum size:</span> {maxSizeFormatted}
                    </p>
                )}
                <div className="flex items-center justify-center gap-4 mt-4 text-xs text-slate-500">
                    <div className="flex items-center gap-1">
                        <svg className="w-3 h-3 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        <span>Secure upload</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <svg className="w-3 h-3 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                        <span>AI-powered analysis</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <svg className="w-3 h-3 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M18 8a6 6 0 01-7.743 5.743L10 14l-1 1-1 1H6v2H2v-4l4.257-4.257A6 6 0 1118 8zm-6-4a1 1 0 100 2 2 2 0 012 2 1 1 0 102 0 4 4 0 00-4-4z" clipRule="evenodd" />
                        </svg>
                        <span>Privacy protected</span>
                    </div>
                </div>
            </div>

            {/* Additional Help Text */}
            <div className="mt-8 max-w-2xl">
                <p className="text-slate-500 text-sm leading-relaxed">
                    Upload contracts, legal documents, terms of service, privacy policies, and more. 
                    Our AI will analyze the content and help you understand key terms, identify risks, 
                    and answer your questions.
                </p>
            </div>
        </div>
    );
};

// PropTypes for type checking
UploadComponent.propTypes = {
    onFileUpload: PropTypes.func.isRequired,
    acceptedTypes: PropTypes.arrayOf(PropTypes.string),
    maxFileSize: PropTypes.number,
    disabled: PropTypes.bool,
    title: PropTypes.string,
    subtitle: PropTypes.string,
    showFileTypes: PropTypes.bool,
    showMaxSize: PropTypes.bool,
    className: PropTypes.string
};

export default UploadComponent;