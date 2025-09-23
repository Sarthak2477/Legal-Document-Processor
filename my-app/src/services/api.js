import { debugAPI } from './debug';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://your-deployed-api-url.com';

class ApiService {
  async uploadContract(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('process_immediately', 'true');

            const url = `${API_BASE_URL}/upload/upload`;
      debugAPI.logRequest(url, { method: 'POST', file: file.name });

      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        mode: 'cors',
      });

      let data;
      try {
        data = await response.json();
      } catch (jsonError) {
        console.error('Failed to parse JSON response:', jsonError);
        const text = await response.clone().text();
        console.error('Response text:', text);
        throw new Error(`Invalid JSON response: ${response.status} ${response.statusText}`);
      }

      debugAPI.logResponse(response, data);

      if (!response.ok) {
        const errorMsg = data?.detail || data?.message || response.statusText || 'Unknown error';
        debugAPI.logError(`Upload failed: ${errorMsg}`);
        throw new Error(`Upload failed: ${errorMsg}`);
      }

      return data;
    } catch (error) {
      console.error('Upload error details:', error);
      throw error;
    }
  }

  async getContractStatus(contractId) {
    try {
      const response = await fetch(`${API_BASE_URL}/contracts/status/${contractId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to get status: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Get contract status error:', error);
      throw error;
    }
  }

  async getContract(contractId) {
    try {
      const response = await fetch(`${API_BASE_URL}/contracts/${contractId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to get contract: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Get contract error:', error);
      throw error;
    }
  }

  async askQuestion(contractId, question) {
    try {
      const response = await fetch(`${API_BASE_URL}/rag/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question,
          contract_id: contractId,
        }),
        mode: 'cors',
      });

      if (!response.ok) {
        throw new Error(`Question failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Ask question error:', error);
      throw error;
    }
  }

  async getRiskAnalysis(contractId) {
    try {
      const response = await fetch(`${API_BASE_URL}/rag/risks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contract_id: contractId,
        }),
        mode: 'cors',
      });

      if (!response.ok) {
        throw new Error(`Risk analysis failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Risk analysis error:', error);
      throw error;
    }
  }

  async getSummary(contractId) {
    try {
      const response = await fetch(`${API_BASE_URL}/rag/summary`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contract_id: contractId,
        }),
        mode: 'cors',
      });

      if (!response.ok) {
        throw new Error(`Summary failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Summary error:', error);
      throw error;
    }
  }
}

export default new ApiService();