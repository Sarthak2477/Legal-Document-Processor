// Debug helper for API calls
export const debugAPI = {
  logRequest: (url, options) => {
    console.log('🚀 API Request:', url, options);
  },
  
  logResponse: (response, data) => {
    console.log('📥 API Response:', response.status, data);
  },
  
  logError: (error) => {
    console.error('❌ API Error:', error);
  }
};